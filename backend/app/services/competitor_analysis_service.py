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

    async def _identify_competitor_names(self, solution, pass1_results) -> list[str]:
        """Ask Gemini to extract up to 5 real competitor company names from pass-1 search results.
        Returns [] if none clearly identified. Names only, no fabrication."""
        if not pass1_results:
            return []

        system_prompt = (
            "You are a helpful market research extraction assistant.\n"
            "Analyze the search results and extract up to 5 real competitor company names that are mentioned.\n"
            "Follow these rules:\n"
            "1. Only extract real competitor companies relevant to the user's solution.\n"
            "2. Do not invent or fabricate names.\n"
            "3. If no clear competitor names are mentioned, return an empty list.\n"
            "4. Return ONLY a valid JSON object matching the requested schema.\n"
        )

        results_str = ""
        for i, r in enumerate(pass1_results):
            results_str += f"[{i+1}] Title: {r.title}\nURL: {r.url}\nContent: {r.content}\n\n"

        user_prompt = f"""
Given the following solution details:
Title: {solution.title}
Description: {solution.description}

And the search results:
{results_str}

Extract up to 5 real competitor company names.
Response schema:
{{
  "competitors": ["Name 1", "Name 2", "Name 3"]
}}
"""
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "competitors": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            },
            "required": ["competitors"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.0
            )
            data = json.loads(raw_response)
            names = [name.strip() for name in data.get("competitors", []) if name.strip()]
            return names[:5]
        except Exception as e:
            logger.error(f"Failed to identify competitor names: {e}")
            return []

    async def run_analysis(self, solution_id: UUID, user_id: UUID) -> CompetitorAnalysis:
        """
        Runs in the BACKGROUND. Independent of evaluation.
        1. Set status=researching.
        2. Pass 1 - Broad queries from solution title + target_user + industry/location
           to identify who the competitors are.
        3. Call self.search.search() for each query with basic depth, dedupe results by domain.
        4. Ask Gemini to extract up to 5 real competitor company names.
        5. Pass 2 - For each identified competitor (max 4), run targeted queries with advanced depth:
           - "<name> pricing"
           - "<name> funding OR revenue OR crunchbase"
           - "<name> reviews limitations OR cons OR drawbacks"
        6. Log total searches performed.
        7. Deduplicate combined results by domain.
        8. Feed to Gemini with synthesis prompt.
        9. Save sources, set status=completed.
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

            # Build search queries (Pass 1)
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

            # Execute Pass 1 searches
            pass1_results = []
            total_searches = 0
            for query in queries:
                try:
                    res_list = await self.search.search(query, search_depth="basic")
                    pass1_results.extend(res_list)
                    total_searches += 1
                except Exception as e:
                    logger.error(f"Search query '{query}' failed: {e}")

            # Deduplicate by domain (Pass 1)
            seen_domains = set()
            unique_pass1_results = []
            for r in pass1_results:
                domain = self._get_domain(r.url)
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                    unique_pass1_results.append(r)

            # Identify competitor names
            competitor_names = await self._identify_competitor_names(solution, unique_pass1_results)

            # Execute Pass 2 searches (per competitor deep research)
            pass2_results = []
            if competitor_names:
                for name in competitor_names[:4]:
                    pass2_queries = [
                        f"{name} pricing",
                        f"{name} funding OR revenue OR crunchbase",
                        f"{name} reviews limitations OR cons OR drawbacks"
                    ]
                    for q in pass2_queries:
                        try:
                            res_list = await self.search.search(q, search_depth="advanced")
                            pass2_results.extend(res_list)
                            total_searches += 1
                        except Exception as e:
                            logger.error(f"Deep search query '{q}' failed: {e}")

            # Log total searches
            logger.info(f"Competitor analysis for solution {solution_id}: performed {total_searches} total searches.")

            # Combine all results and deduplicate by domain
            all_results = pass1_results + pass2_results
            seen_domains = set()
            all_unique_results = []
            for r in all_results:
                domain = self._get_domain(r.url)
                if domain and domain not in seen_domains:
                    seen_domains.add(domain)
                    all_unique_results.append(r)

            # Synthesis with Gemini
            system_prompt, user_prompt = self._build_synthesis_prompt(solution, all_unique_results)

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
            analysis.sources = [{"title": r.title, "url": r.url} for r in all_unique_results]
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
        - Attempt to fill: pricing, funding, strengths, AND weaknesses for each competitor.
        - Frame everything as 'based on publicly available information'.
        - Return ONLY valid JSON matching the schema.
        """
        system_prompt = (
            "You are a helpful and honest market research assistant.\n"
            "You MUST adhere to the following rules:\n"
            "1. Use ONLY the provided search results as evidence; do not invent companies. Only reference companies that appear in the search results.\n"
            "2. For EACH competitor, attempt to fill: pricing, funding, strengths, AND weaknesses.\n"
            "   - 'pricing': extract concrete pricing from the company's own pricing page or comparison articles if present in the search results (e.g. '$99/mo', 'custom enterprise pricing', 'free tier available'). If genuinely not present in results, return null.\n"
            "   - 'funding': extract funding/revenue facts if present (e.g. 'raised $30M Series B (2023)', 'bootstrapped'). If not present, return null. Do not fabricate funding/pricing numbers.\n"
            "   - 'weaknesses': derive from review, comparison, or limitation content in search results (e.g. 'steep learning curve', 'expensive for small properties', 'limited integrations'). A competitive analysis with no weaknesses is not useful — make a genuine effort to surface real limitations from the search results, but never fabricate them. Provide an empty list ONLY if no weakness signal exists.\n"
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
