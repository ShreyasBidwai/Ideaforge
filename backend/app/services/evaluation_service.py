import json
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.ai.provider import AIProvider
from app.models import ProblemStatement, Solution, Evaluation
from app.core.maturity import get_maturity_config, MaturityLevel
from app.schemas.evaluation import RubricSchema
from app.ai.prompts.evaluation.rubric import build_rubric_prompt

class EvaluationService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession):
        self.ai = ai_provider
        self.db = db

    async def _get_problem_and_validate(self, problem_id: UUID, user_id: UUID) -> ProblemStatement:
        result = await self.db.execute(
            select(ProblemStatement)
            .options(joinedload(ProblemStatement.session))
            .where(ProblemStatement.id == problem_id)
        )
        problem = result.scalar_one_or_none()

        if problem is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Problem statement not found"
            )

        if problem.session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not own this session"
            )

        return problem

    async def _get_solutions(self, problem_id: UUID) -> list[Solution]:
        result = await self.db.execute(
            select(Solution).where(Solution.problem_id == problem_id)
        )
        solutions_list = list(result.scalars().all())
        if not solutions_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No solutions found for this problem statement. Please generate solutions first."
            )
        return solutions_list

    async def generate_rubric(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 2 of Evaluation Protocol.
        1. Fetch problem statement (validate ownership)
        2. Get maturity config from session
        3. Build rubric prompt (NO solution data included)
        4. Call Gemini AI
        5. Parse and validate rubric JSON
        6. Validate: 3-6 criteria, each has name/description/weight/scale with 1/3/5, 1-3 disqualifiers
        7. If production maturity: verify security/compliance criteria exist
        8. Store rubric in Evaluation records (create one per solution with the same rubric)
        9. Return rubric
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Check if already locked
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())
        if any(e.status == "rubric_locked" for e in evaluations_list):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Rubric is locked and cannot be regenerated"
            )

        session = problem.session
        maturity_config = get_maturity_config(MaturityLevel(session.maturity_level))

        # Build prompt
        problem_dict = {
            "title": problem.title,
            "description": problem.description,
            "target_user": problem.target_user,
            "core_pain": problem.core_pain,
            "market_context": problem.market_context
        }
        system_prompt, user_prompt = build_rubric_prompt(problem_dict, maturity_config)

        # Response schema for Gemini structured output
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "criteria": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING"},
                            "weight": {"type": "NUMBER"},
                            "scale": {
                                "type": "OBJECT",
                                "properties": {
                                    "1": {"type": "STRING"},
                                    "3": {"type": "STRING"},
                                    "5": {"type": "STRING"}
                                },
                                "required": ["1", "3", "5"]
                            }
                        },
                        "required": ["name", "description", "weight", "scale"]
                    }
                },
                "disqualifiers": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "description": {"type": "STRING"}
                        },
                        "required": ["name", "description"]
                    }
                }
            },
            "required": ["criteria", "disqualifiers"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.2
            )
            data = json.loads(raw_response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to generate rubric via AI: {str(e)}"
            )

        # Pydantic validation: 3-6 criteria, 1-3 disqualifiers
        try:
            rubric_schema = RubricSchema(**data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI generated an invalid rubric schema: {str(e)}"
            )

        # Enforce criteria length constraints
        if len(rubric_schema.criteria) < 3 or len(rubric_schema.criteria) > 6:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI generated {len(rubric_schema.criteria)} criteria, expected 3-6."
            )
        if len(rubric_schema.disqualifiers) < 1 or len(rubric_schema.disqualifiers) > 5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"AI generated {len(rubric_schema.disqualifiers)} disqualifiers, expected 1-5."
            )

        # 7. If production maturity: verify security/compliance criteria exist
        if session.maturity_level == "production":
            has_security = any(
                "security" in c.name.lower() or "privacy" in c.name.lower() or "data protection" in c.name.lower() or
                "security" in c.description.lower() or "privacy" in c.description.lower() or "data protection" in c.description.lower()
                for c in rubric_schema.criteria
            )
            has_compliance = any(
                "compliance" in c.name.lower() or "regulatory" in c.name.lower() or "legal" in c.name.lower() or
                "compliance" in c.description.lower() or "regulatory" in c.description.lower() or "legal" in c.description.lower()
                for c in rubric_schema.criteria
            )
            if not has_security:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Security & Data Privacy criterion is required for production maturity level."
                )
            if not has_compliance:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Regulatory Compliance criterion is required for production maturity level."
                )

        rubric_dict = rubric_schema.model_dump()

        # 8. Store rubric in Evaluation records (create one per solution with the same rubric)
        for solution in solutions_list:
            # Query existing evaluation
            result = await self.db.execute(
                select(Evaluation).where(Evaluation.solution_id == solution.id)
            )
            existing_eval = result.scalar_one_or_none()
            if existing_eval:
                existing_eval.rubric = rubric_dict
            else:
                new_eval = Evaluation(
                    solution_id=solution.id,
                    rubric=rubric_dict,
                    status="pending"
                )
                self.db.add(new_eval)

        await self.db.commit()

        return {
            "rubric": rubric_dict,
            "is_locked": False,
            "problem_id": problem_id
        }

    async def get_rubric(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Fetch the current rubric stored for a problem's solutions.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Fetch evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        if not evaluations_list or not any(e.rubric for e in evaluations_list):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rubric not found for this problem statement."
            )

        first_eval = evaluations_list[0]
        is_locked = any(e.status == "rubric_locked" for e in evaluations_list)
        return {
            "rubric": first_eval.rubric,
            "is_locked": is_locked,
            "problem_id": problem_id
        }

    async def update_rubric(self, problem_id: UUID, user_id: UUID, rubric: dict) -> dict:
        """
        Allow user to edit the rubric before locking.
        Validates rubric structure, updates all Evaluation records for this problem's solutions.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Check if locked
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())
        if any(e.status == "rubric_locked" for e in evaluations_list):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Rubric is locked and cannot be modified"
            )

        # Validate structure
        try:
            rubric_schema = RubricSchema(**rubric)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid rubric structure: {str(e)}"
            )

        rubric_dict = rubric_schema.model_dump()

        for solution in solutions_list:
            result = await self.db.execute(
                select(Evaluation).where(Evaluation.solution_id == solution.id)
            )
            existing_eval = result.scalar_one_or_none()
            if existing_eval:
                existing_eval.rubric = rubric_dict
            else:
                new_eval = Evaluation(
                    solution_id=solution.id,
                    rubric=rubric_dict,
                    status="pending"
                )
                self.db.add(new_eval)

        await self.db.commit()

        return {
            "rubric": rubric_dict,
            "is_locked": False,
            "problem_id": problem_id
        }

    async def lock_rubric(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Lock the rubric — no more edits allowed.
        After locking, scoring can begin.
        Updates evaluation status to 'rubric_locked'.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Fetch evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())
        if not evaluations_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No evaluations or rubrics found for this problem statement."
            )

        for eval_rec in evaluations_list:
            eval_rec.status = "rubric_locked"

        await self.db.commit()

        return {
            "rubric": evaluations_list[0].rubric,
            "is_locked": True,
            "problem_id": problem_id
        }

    async def run_disqualifier_gate(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 4: Disqualifier Gate
        1. Verify rubric is locked
        2. Get all solutions for the problem
        3. Get disqualifiers from rubric
        4. Call AI to evaluate each solution against each disqualifier
        5. Mark failed solutions as status='disqualified'
        6. If fewer than 2 survive, return error indicating regeneration needed
        7. Return results: which passed, which failed and why
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        if not evaluations_list or not any(e.status == "rubric_locked" for e in evaluations_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rubric is not locked. Please lock the rubric first."
            )

        rubric = evaluations_list[0].rubric
        disqualifiers = rubric.get("disqualifiers", [])

        # Format solutions for AI
        solutions_data = [
            {
                "title": s.title,
                "description": s.description,
                "mechanism": s.mechanism,
                "tech_stack": s.tech_stack,
                "target_user": s.target_user,
                "revenue_model": s.revenue_model
            } for s in solutions_list
        ]

        from app.ai.prompts.evaluation.disqualify import build_disqualifier_prompt
        system_prompt, user_prompt = build_disqualifier_prompt(solutions_data, disqualifiers)

        # Response schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "results": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "solution_title": {"type": "STRING"},
                            "passed": {"type": "BOOLEAN"},
                            "failed_disqualifiers": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "reasons": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            }
                        },
                        "required": ["solution_title", "passed", "failed_disqualifiers", "reasons"]
                    }
                }
            },
            "required": ["results"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.1
            )
            data = json.loads(raw_response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI generation failed for disqualifier gate: {str(e)}"
            )

        results = data.get("results", [])
        result_map = {r["solution_title"]: r for r in results}

        survivors_count = 0
        for solution in solutions_list:
            res = result_map.get(solution.title)
            eval_rec = next((e for e in evaluations_list if e.solution_id == solution.id), None)
            if res:
                if not res["passed"]:
                    solution.status = "disqualified"
                    if eval_rec:
                        eval_rec.status = "disqualified"
                else:
                    solution.status = "candidate"
                    if eval_rec:
                        eval_rec.status = "disqualified_passed"
                    survivors_count += 1
            else:
                if eval_rec:
                    eval_rec.status = "disqualified_passed"
                survivors_count += 1

        if survivors_count < 2:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fewer than 2 solution candidates passed the disqualifier gate. Regeneration of solution candidates is needed."
            )

        await self.db.commit()
        return {"results": results}

    async def run_scoring(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 5: Score Survivors
        1. Verify disqualifier gate has been run
        2. Get surviving solutions (status != 'disqualified')
        3. Get locked rubric criteria and weights
        4. Call AI to score each survivor on each criterion
        5. Compute weighted_avg = sum(score * weight) / sum(weights)
        6. Compute min_score = minimum score across all criteria
        7. Store scores in Evaluation records
        8. Return scoring matrix
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        # Check if disqualifier gate has been run
        is_disqualifier_run = any(
            e.status in ("disqualified_passed", "disqualified", "scored", "completed")
            for e in evaluations_list
        )
        if not is_disqualifier_run:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Disqualifier gate has not been run yet. Please run the disqualifier gate first."
            )

        surviving_solutions = [s for s in solutions_list if s.status != "disqualified"]
        rubric = evaluations_list[0].rubric
        criteria = rubric.get("criteria", [])

        # Format survivors for AI
        survivors_data = [
            {
                "title": s.title,
                "description": s.description,
                "mechanism": s.mechanism,
                "tech_stack": s.tech_stack,
                "target_user": s.target_user,
                "revenue_model": s.revenue_model
            } for s in surviving_solutions
        ]

        from app.ai.prompts.evaluation.scoring import build_scoring_prompt
        system_prompt, user_prompt = build_scoring_prompt(survivors_data, rubric)

        # Response schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "scores": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "solution_title": {"type": "STRING"},
                            "criterion_scores": {
                                "type": "ARRAY",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "criterion": {"type": "STRING"},
                                        "score": {"type": "NUMBER"},
                                        "justification": {"type": "STRING"}
                                    },
                                    "required": ["criterion", "score", "justification"]
                                }
                            }
                        },
                        "required": ["solution_title", "criterion_scores"]
                    }
                }
            },
            "required": ["scores"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.1,
                max_tokens=16000,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI generation failed for scoring: {str(e)}"
            )
        try:
            data = json.loads(raw_response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI scoring response was truncated or malformed — JSON error: {str(e)}"
            )

        scores_list = data.get("scores", [])
        for s_score in scores_list:
            s_score["weighted_avg"] = self.compute_weighted_avg(s_score["criterion_scores"], criteria)
            s_score["min_score"] = self.compute_min_score(s_score["criterion_scores"])

        score_map = {s["solution_title"]: s for s in scores_list}
        for solution in surviving_solutions:
            res = score_map.get(solution.title)
            eval_rec = next((e for e in evaluations_list if e.solution_id == solution.id), None)
            if res and eval_rec:
                eval_rec.scores = res["criterion_scores"]
                eval_rec.weighted_avg = res["weighted_avg"]
                eval_rec.min_score = res["min_score"]
                eval_rec.status = "scored"

        await self.db.commit()
        return {"scores": scores_list}

    async def get_scores(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Fetch the saved scores for surviving solutions.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        evaluations_result = await self.db.execute(
            select(Evaluation)
            .options(joinedload(Evaluation.solution))
            .where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        scores_out = []
        for e in evaluations_list:
            if e.scores is not None:
                scores_out.append({
                    "solution_title": e.solution.title,
                    "criterion_scores": e.scores,
                    "weighted_avg": e.weighted_avg,
                    "min_score": e.min_score
                })

        return {"scores": scores_out}

    async def run_devils_advocate(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 6: Devil's Advocate Attack
        1. Verify scoring has been completed
        2. Get surviving solutions with their scores
        3. Call AI for strongest attack per solution
        4. Store attack_summary and attack_survives in Evaluation records
        5. Return attacks
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        if not any(e.status in ("scored", "completed") for e in evaluations_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scoring has not been completed. Please run scoring first."
            )

        surviving_solutions = [s for s in solutions_list if s.status != "disqualified"]
        
        scores_data = []
        for e in evaluations_list:
            if e.scores and e.status in ("scored", "completed"):
                # Find solution title
                sol_title = next(s.title for s in solutions_list if s.id == e.solution_id)
                scores_data.append({
                    "solution_title": sol_title,
                    "criterion_scores": e.scores,
                    "weighted_avg": e.weighted_avg,
                    "min_score": e.min_score
                })

        solutions_data = [
            {
                "title": s.title,
                "description": s.description,
                "mechanism": s.mechanism,
                "tech_stack": s.tech_stack,
                "target_user": s.target_user,
                "revenue_model": s.revenue_model
            } for s in surviving_solutions
        ]

        from app.ai.prompts.evaluation.devils_advocate import build_devils_advocate_prompt
        system_prompt, user_prompt = build_devils_advocate_prompt(solutions_data, scores_data)

        # Response schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "attacks": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "solution_title": {"type": "STRING"},
                            "attack": {"type": "STRING"},
                            "severity": {"type": "STRING"},
                            "survives": {"type": "BOOLEAN"},
                            "survival_reasoning": {"type": "STRING"}
                        },
                        "required": ["solution_title", "attack", "severity", "survives", "survival_reasoning"]
                    }
                }
            },
            "required": ["attacks"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.15
            )
            data = json.loads(raw_response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI generation failed for Devil's Advocate: {str(e)}"
            )

        attacks_list = data.get("attacks", [])
        attack_map = {a["solution_title"]: a for a in attacks_list}

        for solution in surviving_solutions:
            res = attack_map.get(solution.title)
            eval_rec = next((e for e in evaluations_list if e.solution_id == solution.id), None)
            if res and eval_rec:
                eval_rec.attack_summary = res["attack"]
                eval_rec.attack_survives = res["survives"]
                eval_rec.status = "attacked"

        await self.db.commit()
        return {"attacks": attacks_list}

    async def run_ach_analysis(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 7: ACH Inconsistency Count
        1. Verify devil's advocate has been run (or skip if POC/MVP maturity)
        2. Get solutions, problem, scores, attacks
        3. Call AI for inconsistency analysis
        4. Store inconsistencies and inconsistency_count in Evaluation records
        5. Return analysis
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation).where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        session = problem.session
        from app.core.maturity import get_maturity_config, MaturityLevel
        maturity_config = get_maturity_config(MaturityLevel(session.maturity_level))

        # Check if devil's advocate has been run
        is_attack_run = any(
            e.status in ("attacked", "completed") or e.attack_summary is not None
            for e in evaluations_list
        )
        if "devils_advocate" in maturity_config.evaluation_steps and not is_attack_run:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Devil's Advocate attack has not been run yet. Please run the attack first."
            )

        surviving_solutions = [s for s in solutions_list if s.status != "disqualified"]
        
        scores_data = []
        for e in evaluations_list:
            if e.scores:
                sol_title = next(s.title for s in solutions_list if s.id == e.solution_id)
                scores_data.append({
                    "solution_title": sol_title,
                    "criterion_scores": e.scores,
                    "weighted_avg": e.weighted_avg,
                    "min_score": e.min_score
                })

        solutions_data = [
            {
                "title": s.title,
                "description": s.description,
                "mechanism": s.mechanism,
                "tech_stack": s.tech_stack,
                "target_user": s.target_user,
                "revenue_model": s.revenue_model
            } for s in surviving_solutions
        ]

        problem_dict = {
            "title": problem.title,
            "description": problem.description,
            "target_user": problem.target_user,
            "core_pain": problem.core_pain,
            "market_context": problem.market_context
        }

        from app.ai.prompts.evaluation.ach import build_ach_prompt
        system_prompt, user_prompt = build_ach_prompt(solutions_data, problem_dict, scores_data)

        # Response schema
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "analysis": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "solution_title": {"type": "STRING"},
                            "inconsistencies": {
                                "type": "ARRAY",
                                "items": {"type": "STRING"}
                            },
                            "count": {"type": "NUMBER"}
                        },
                        "required": ["solution_title", "inconsistencies", "count"]
                    }
                }
            },
            "required": ["analysis"]
        }

        try:
            raw_response = await self.ai.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                temperature=0.1
            )
            data = json.loads(raw_response)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI generation failed for ACH analysis: {str(e)}"
            )

        analysis_list = data.get("analysis", [])
        analysis_map = {a["solution_title"]: a for a in analysis_list}

        for solution in surviving_solutions:
            res = analysis_map.get(solution.title)
            eval_rec = next((e for e in evaluations_list if e.solution_id == solution.id), None)
            if res and eval_rec:
                eval_rec.inconsistencies = res["inconsistencies"]
                eval_rec.inconsistency_count = res["count"]
                eval_rec.status = "completed"

        await self.db.commit()
        return {"analysis": analysis_list}

    async def get_attacks(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Fetch the saved attacks for surviving solutions.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        evaluations_result = await self.db.execute(
            select(Evaluation)
            .options(joinedload(Evaluation.solution))
            .where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        attacks_out = []
        for e in evaluations_list:
            if e.attack_summary is not None:
                attacks_out.append({
                    "solution_title": e.solution.title,
                    "attack": e.attack_summary,
                    "survives": e.attack_survives
                })

        return {"attacks": attacks_out}

    async def get_ach(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Fetch the ACH results for surviving solutions.
        """
        await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        evaluations_result = await self.db.execute(
            select(Evaluation)
            .options(joinedload(Evaluation.solution))
            .where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        analysis_out = []
        for e in evaluations_list:
            if e.inconsistencies is not None:
                analysis_out.append({
                    "solution_title": e.solution.title,
                    "inconsistencies": e.inconsistencies,
                    "count": e.inconsistency_count
                })

        return {"analysis": analysis_out}

    async def generate_comparison(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Step 8: Final Comparison (computed, no AI call needed)
        1. Gather all evaluation data for survivors: weighted_avg, min_score, attack_summary, attack_survives, inconsistency_count
        2. Build comparison table
        3. Determine leader per metric:
           - Highest weighted_avg
           - Highest min_score
           - Best attack survival (survives=True > False)
           - Lowest inconsistency_count
        4. Flag if one candidate wins ALL 4 metrics → "clear survivor"
        5. Flag if metrics disagree → highlight disagreement explicitly
        6. DO NOT recommend or decide. Present data only.
        7. Update session status to "completed"
        8. Return comparison
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation)
            .options(joinedload(Evaluation.solution))
            .where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        surviving_solutions = [s for s in solutions_list if s.status != "disqualified"]

        entries = []
        for s in surviving_solutions:
            e = next((ev for ev in evaluations_list if ev.solution_id == s.id), None)
            if e:
                entries.append({
                    "solution_id": s.id,
                    "solution_title": s.title,
                    "weighted_avg": e.weighted_avg or 0.0,
                    "min_score": e.min_score or 0.0,
                    "attack_summary": e.attack_summary or "",
                    "attack_survives": e.attack_survives if e.attack_survives is not None else False,
                    "inconsistency_count": e.inconsistency_count or 0
                })

        comparison = self._compute_comparison_results(entries)

        # Update session and evaluation status
        session = problem.session
        session.status = "completed"
        for ev in evaluations_list:
            ev.status = "completed"

        await self.db.commit()
        return comparison

    async def get_full_evaluation(self, problem_id: UUID, user_id: UUID) -> dict:
        """
        Get complete evaluation state: rubric, disqualifier results, scores, attacks, ACH, comparison.
        Single endpoint to load the full evaluation wizard state.
        """
        problem = await self._get_problem_and_validate(problem_id, user_id)
        solutions_list = await self._get_solutions(problem_id)

        # Get evaluations
        evaluations_result = await self.db.execute(
            select(Evaluation)
            .options(joinedload(Evaluation.solution))
            .where(Evaluation.solution_id.in_([s.id for s in solutions_list]))
        )
        evaluations_list = list(evaluations_result.scalars().all())

        if not evaluations_list:
            return {
                "status": "pending"
            }

        rubric = evaluations_list[0].rubric
        status_str = evaluations_list[0].status

        # 1. Disqualifier results
        disqualifier_results = None
        is_disq_run = any(
            e.status in ("disqualified_passed", "disqualified", "scored", "completed")
            for e in evaluations_list
        )
        if is_disq_run:
            results = []
            for e in evaluations_list:
                passed = (e.status != "disqualified" and e.solution.status != "disqualified")
                results.append({
                    "solution_title": e.solution.title,
                    "passed": passed,
                    "failed_disqualifiers": [] if passed else ["Disqualified by gate"],
                    "reasons": [] if passed else ["Candidate failed disqualifier gate check"]
                })
            disqualifier_results = {"results": results}

        # 2. Scores
        scores = None
        is_scored = any(e.status in ("scored", "completed") for e in evaluations_list)
        if is_scored:
            scores_list = []
            for e in evaluations_list:
                if e.scores:
                    scores_list.append({
                        "solution_title": e.solution.title,
                        "criterion_scores": e.scores,
                        "weighted_avg": e.weighted_avg,
                        "min_score": e.min_score
                    })
            scores = {"scores": scores_list}

        # 3. Attacks
        attacks = None
        is_attacked = any(e.status in ("completed",) or e.attack_summary is not None for e in evaluations_list)
        if is_attacked:
            attacks_list = []
            for e in evaluations_list:
                if e.attack_summary is not None:
                    attacks_list.append({
                        "solution_title": e.solution.title,
                        "attack": e.attack_summary,
                        "survives": e.attack_survives
                    })
            attacks = {"attacks": attacks_list}

        # 4. ACH Analysis
        ach_analysis = None
        is_ach = any(e.status == "completed" or e.inconsistencies is not None for e in evaluations_list)
        if is_ach:
            analysis_list = []
            for e in evaluations_list:
                if e.inconsistencies is not None:
                    analysis_list.append({
                        "solution_title": e.solution.title,
                        "inconsistencies": e.inconsistencies,
                        "count": e.inconsistency_count
                    })
            ach_analysis = {"analysis": analysis_list}

        # 5. Comparison
        comparison = None
        surviving_evals = [e for e in evaluations_list if e.status != "disqualified" and e.solution.status != "disqualified"]
        if surviving_evals and any(e.weighted_avg is not None for e in surviving_evals):
            entries = []
            for e in surviving_evals:
                entries.append({
                    "solution_id": e.solution_id,
                    "solution_title": e.solution.title,
                    "weighted_avg": e.weighted_avg or 0.0,
                    "min_score": e.min_score or 0.0,
                    "attack_summary": e.attack_summary or "",
                    "attack_survives": e.attack_survives if e.attack_survives is not None else False,
                    "inconsistency_count": e.inconsistency_count or 0
                })
            comparison = self._compute_comparison_results(entries)

        return {
            "rubric": rubric,
            "disqualifier_results": disqualifier_results,
            "scores": scores,
            "attacks": attacks,
            "ach_analysis": ach_analysis,
            "comparison": comparison,
            "status": status_str
        }

    @staticmethod
    def _compute_comparison_results(entries: list[dict]) -> dict:
        if not entries:
            return {
                "entries": [],
                "leaders": {},
                "is_clear_winner": False,
                "disagreements": []
            }

        max_weighted_avg = max(x["weighted_avg"] for x in entries)
        max_min_score = max(x["min_score"] for x in entries)
        max_attack_survives = max(x["attack_survives"] for x in entries)
        min_inconsistency = min(x["inconsistency_count"] for x in entries)

        weighted_avg_leader = max(entries, key=lambda x: x["weighted_avg"])["solution_title"]
        min_score_leader = max(entries, key=lambda x: x["min_score"])["solution_title"]
        attack_survives_leader = max(entries, key=lambda x: x["attack_survives"])["solution_title"]
        inconsistency_count_leader = min(entries, key=lambda x: x["inconsistency_count"])["solution_title"]

        leaders = {
            "weighted_avg": weighted_avg_leader,
            "min_score": min_score_leader,
            "attack_survives": attack_survives_leader,
            "inconsistency_count": inconsistency_count_leader
        }

        clear_winner_title = None
        for entry in entries:
            if (entry["weighted_avg"] == max_weighted_avg and
                entry["min_score"] == max_min_score and
                entry["attack_survives"] == max_attack_survives and
                entry["inconsistency_count"] == min_inconsistency):
                clear_winner_title = entry["solution_title"]
                break

        is_clear_winner = clear_winner_title is not None

        disagreements = []
        if not is_clear_winner:
            leaders_by_metric = {}
            for entry in entries:
                metrics_led = []
                if entry["weighted_avg"] == max_weighted_avg:
                    metrics_led.append("weighted_avg")
                if entry["min_score"] == max_min_score:
                    metrics_led.append("min_score")
                if entry["attack_survives"] == max_attack_survives:
                    metrics_led.append("attack_survives")
                if entry["inconsistency_count"] == min_inconsistency:
                    metrics_led.append("inconsistency_count")
                for m in metrics_led:
                    leaders_by_metric.setdefault(m, []).append(entry["solution_title"])

            for m1, m2 in [("weighted_avg", "min_score"), ("weighted_avg", "attack_survives"), ("weighted_avg", "inconsistency_count")]:
                l1 = leaders_by_metric.get(m1, [])
                l2 = leaders_by_metric.get(m2, [])
                if not (set(l1) & set(l2)):
                    disagreements.append(
                        f"{m1.replace('_', ' ').title()} points to {', '.join(l1)}, but {m2.replace('_', ' ').title()} points to {', '.join(l2)}."
                    )

        return {
            "entries": entries,
            "leaders": leaders,
            "is_clear_winner": is_clear_winner,
            "disagreements": disagreements
        }

    @staticmethod
    def compute_weighted_avg(scores: list[dict], criteria: list[dict]) -> float:
        """Compute weighted average from scores and criteria weights"""
        weight_map = {c["name"]: c["weight"] for c in criteria}
        total_weighted = sum(s["score"] * weight_map.get(s["criterion"], 1) for s in scores)
        total_weight = sum(weight_map.get(s["criterion"], 1) for s in scores)
        return round(total_weighted / total_weight, 2) if total_weight > 0 else 0

    @staticmethod
    def compute_min_score(scores: list[dict]) -> float:
        """Find the minimum score across all criteria"""
        return min(s["score"] for s in scores) if scores else 0


