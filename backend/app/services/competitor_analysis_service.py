import json
import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.models.competitor_analysis import CompetitorAnalysis
from app.models.solution import Solution
from app.models.problem_statement import ProblemStatement
from app.services.search import get_search_provider
from sqlalchemy import func

logger = logging.getLogger(__name__)

class CompetitorAnalysisService:
    def __init__(self, ai_provider, db):
        self.ai = ai_provider
        self.db = db
        self.search = get_search_provider()

    async def get_or_create(self, solution_id: UUID, user_id: UUID) -> CompetitorAnalysis:
        """Return existing analysis (cached) or create a pending one."""
        # Optional: Validate user owns the solution
        stmt_sol = (
            select(Solution)
            .options(joinedload(Solution.problem_statement).joinedload(ProblemStatement.session))
            .where(Solution.id == solution_id)
        )
        res_sol = await self.db.execute(stmt_sol)
        solution = res_sol.scalar_one_or_none()
        if not solution:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solution not found")
        if solution.problem_statement.session.user_id != user_id:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        stmt = select(CompetitorAnalysis).where(CompetitorAnalysis.solution_id == solution_id)
        result = await self.db.execute(stmt)
        analysis = result.scalar_one_or_none()
        if not analysis:
            analysis = CompetitorAnalysis(solution_id=solution_id, status="pending")
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)
        return analysis

    async def run_analysis(self, solution_id: UUID, user_id: UUID) -> CompetitorAnalysis:
        """
        Runs in the BACKGROUND. Independent of evaluation.
        1. Set status=researching.
        2. Build search queries from solution title + target_user + industry/location
           (e.g. "<solution domain> competitors", "<core function> startups <location>",
           "<target_user> <problem> software pricing"). 3-4 queries max to conserve credits.
        3. Call self.search.search() for each query, dedupe results by domain.
        4. Feed combined search results to Gemini with a synthesis prompt (see below).
        5. Parse JSON: competitors[], market_summary, differentiation.
        6. Save sources actually used (title+url), set researched_at=now(), status=completed.
        7. On ANY failure (no key, search error, parse error): status=failed, store error,
           DO NOT raise to caller in a way that breaks anything — this is fire-and-forget.
        """
        # Fetch the CompetitorAnalysis object to update status
        stmt = select(CompetitorAnalysis).where(CompetitorAnalysis.solution_id == solution_id)
        res = await self.db.execute(stmt)
        analysis = res.scalar_one_or_none()
        if not analysis:
            analysis = CompetitorAnalysis(solution_id=solution_id, status="researching")
            self.db.add(analysis)
        else:
            analysis.status = "researching"
            analysis.error = None
        await self.db.commit()

        try:
            # Check TAVILY_API_KEY
            from app.core.config import settings
            if not settings.TAVILY_API_KEY:
                raise RuntimeError("Search not configured")

            # Check AI provider
            if not self.ai:
                raise RuntimeError("AI Provider not configured")

            # Fetch solution with relationship to problem_statement and session
            stmt_sol = (
                select(Solution)
                .options(
                    joinedload(Solution.problem_statement).joinedload(ProblemStatement.session)
                )
                .where(Solution.id == solution_id)
            )
            res_sol = await self.db.execute(stmt_sol)
            solution = res_sol.scalar_one_or_none()
            if not solution:
                raise ValueError("Solution not found")

            # Build search queries
            title = solution.title or ""
            industry = solution.problem_statement.session.industry or ""
            location = solution.problem_statement.session.location or ""
            target_user = solution.target_user or solution.problem_statement.target_user or ""

            queries = []
            queries.append(f"{title} competitors")
            if industry:
                queries.append(f"{title} {industry} startups")
            if target_user:
                queries.append(f"{target_user} {title} software pricing")
            if location:
                queries.append(f"{title} startups {location}")

            queries = list(dict.fromkeys([q.strip() for q in queries if q.strip()]))[:3]

            # Execute searches
            all_results = []
            for query in queries:
                try:
                    res_list = await self.search.search(query)
                    all_results.extend(res_list)
                except Exception as e:
                    logger.error(f"Search query '{query}' failed: {e}")

            # Deduplicate by domain
            seen_domains = set()
            unique_results = []
            for r in all_results:
                domain = self._get_domain(r.url)
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                    unique_results.append(r)

            # Synthesis with Gemini
            system_prompt, user_prompt = self._build_synthesis_prompt(solution, unique_results)

            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "competitors": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "name": {"type": "STRING"},
                                "description": {"type": "STRING"},
                                "pricing": {"type": "STRING"},
                                "funding": {"type": "STRING"},
                                "strengths": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "weaknesses": {"type": "ARRAY", "items": {"type": "STRING"}},
                                "url": {"type": "STRING"}
                            },
                            "required": ["name", "description", "strengths", "weaknesses"]
                        }
                    },
                    "market_summary": {"type": "STRING"},
                    "differentiation": {"type": "STRING"}
                },
                "required": ["competitors", "market_summary", "differentiation"]
            }

            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.2
            )

            data = json.loads(raw_response)

            # Map results to db fields
            analysis.competitors = data.get("competitors", [])
            analysis.market_summary = data.get("market_summary", "")
            analysis.differentiation = data.get("differentiation", "")
            analysis.sources = [{"title": r.title, "url": r.url} for r in unique_results]
            analysis.researched_at = func.now()
            analysis.status = "completed"
            analysis.error = None

            await self.db.commit()
            await self.db.refresh(analysis)

        except Exception as e:
            logger.error(f"Competitor analysis failed for solution {solution_id}: {e}", exc_info=True)
            try:
                analysis.status = "failed"
                analysis.error = str(e)
                await self.db.commit()
            except Exception as db_err:
                logger.error(f"Failed to update failed status in db: {db_err}")

        return analysis

    def _get_domain(self, url: str) -> str:
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            netloc = parsed.netloc
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc.lower()
        except Exception:
            return url.lower()

    def _build_synthesis_prompt(self, solution, search_results) -> tuple[str, str]:
        """
        System prompt MUST instruct:
        - Use ONLY the provided search results as evidence; do not invent companies.
        - If pricing/funding is not in the results, return null for that field — never guess a number.
        - Frame everything as 'based on publicly available information'.
        - Return ONLY valid JSON, schema:
          {
            "competitors": [
              {"name": str, "description": str, "pricing": str|null,
               "funding": str|null, "strengths": [str], "weaknesses": [str], "url": str|null}
            ],
            "market_summary": str,
            "differentiation": str
          }
        - If no real competitors found in results, return empty competitors[] and say so in market_summary.
        """
        system_prompt = (
            "You are a helpful and honest market research assistant.\n"
            "You MUST adhere to the following rules:\n"
            "1. Use ONLY the provided search results as evidence; do not invent companies. Only reference companies that appear in the search results.\n"
            "2. If pricing/funding is not in the results, return null for that field — never guess a number. Do not fabricate funding/pricing numbers.\n"
            "3. Frame everything as 'based on publicly available information'.\n"
            "4. If no real competitors are found in the results, return an empty competitors list and say so in the market summary.\n"
            "5. Return ONLY a valid JSON object matching the requested schema.\n"
        )

        # Contextualize search results for User prompt
        results_str = ""
        for i, r in enumerate(search_results):
            results_str += f"[{i+1}] Title: {r.title}\nURL: {r.url}\nContent: {r.content}\nScore: {r.score}\n\n"

        user_prompt = f"""
Given the following solution details:
Title: {solution.title}
Description: {solution.description}
Mechanism: {getattr(solution, 'mechanism', '')}
Target User: {getattr(solution, 'target_user', '')}

And these Google/Tavily search results:
{results_str}

Please perform a competitive analysis for this solution.
Your output must be a valid JSON object matching the schema below:
{{
  "competitors": [
    {{
      "name": "Competitor name",
      "description": "Short description of competitor",
      "pricing": "Pricing string or null if not found",
      "funding": "Funding info or null if not found",
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1", "weakness2"],
      "url": "competitor url or null if not found"
    }}
  ],
  "market_summary": "Summary of competitive landscape based on search results",
  "differentiation": "How this solution differs / its gap in the market"
}}
"""
        return system_prompt, user_prompt
