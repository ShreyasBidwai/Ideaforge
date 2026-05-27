import logging
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.project import Project
from app.models.document import Document
from app.models.solution import Solution
from app.models.problem_statement import ProblemStatement
from app.models.evaluation import Evaluation
from app.models.session import Session
from app.core.maturity import get_maturity_config, MaturityLevel
from app.ai.provider import AIProvider

from app.ai.prompts.docs.architecture import build_architecture_prompt
from app.ai.prompts.docs.prd import build_prd_prompt
from app.ai.prompts.docs.trd import build_trd_prompt
from app.ai.prompts.docs.sprint_plan import build_sprint_plan_prompt
from app.ai.prompts.docs.engineering import build_engineering_prompt

logger = logging.getLogger(__name__)

class DocGenerationService:
    def __init__(self, ai_provider: AIProvider, db: AsyncSession):
        self.ai = ai_provider
        self.db = db

    async def _build_context(self, project: Project) -> dict:
        solution = project.solution
        if not solution:
            raise HTTPException(status_code=400, detail="Project is missing an associated solution.")
        
        problem = solution.problem_statement
        if not problem:
            raise HTTPException(status_code=400, detail="Solution is missing an associated problem statement.")
        
        session = problem.session
        if not session:
            raise HTTPException(status_code=400, detail="Problem statement is missing an associated session.")

        evaluation = solution.evaluation
        
        # Get maturity config
        try:
            mat_level = MaturityLevel(project.maturity_level)
        except ValueError:
            mat_level = MaturityLevel.MVP
        
        maturity_config = get_maturity_config(mat_level)

        context = {
            "solution": {
                "title": solution.title,
                "description": solution.description,
                "mechanism": solution.mechanism,
                "tech_stack": solution.tech_stack or [],
                "target_user": solution.target_user,
                "revenue_model": solution.revenue_model
            },
            "problem": {
                "title": problem.title,
                "description": problem.description,
                "target_user": problem.target_user,
                "core_pain": problem.core_pain,
                "market_context": problem.market_context
            },
            "evaluation": {
                "weighted_avg": evaluation.weighted_avg if evaluation else None,
                "min_score": evaluation.min_score if evaluation else None,
                "attack_summary": evaluation.attack_summary if evaluation else None,
                "attack_survives": evaluation.attack_survives if evaluation else None,
                "inconsistency_count": evaluation.inconsistency_count if evaluation else 0
            },
            "session": {
                "industry": session.industry,
                "location": session.location,
                "maturity_level": session.maturity_level,
                "tech_stack_preferences": session.tech_stack_preferences or []
            },
            "maturity_config": maturity_config.model_dump() if hasattr(maturity_config, "model_dump") else maturity_config.dict()
        }
        return context

    async def generate_all_docs(self, project_id: UUID, user_id: UUID) -> list[Document]:
        """
        Generate all 5 document types for a project.
        1. Fetch project with solution, problem, evaluation, session data
        2. Build context dict
        3. Generate each doc sequentially (architecture first, then PRD, TRD, sprint_plan, engineering)
        4. Save each as Document record
        5. Return list of created documents
        """
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.solution).selectinload(Solution.problem_statement).selectinload(ProblemStatement.session),
                selectinload(Project.solution).selectinload(Solution.evaluation)
            )
        )
        result = await self.db.execute(stmt)
        project = result.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Update status to doc_generation if not already
        project.status = "doc_generation"
        await self.db.commit()

        context = await self._build_context(project)
        
        doc_types = ["architecture", "prd", "trd", "sprint_plan", "engineering_standards"]
        generated_docs = []

        for doc_type in doc_types:
            try:
                doc = await self._generate_single_doc_internal(project, doc_type, context)
                generated_docs.append(doc)
            except Exception as e:
                project.status = "doc_generation_failed"
                await self.db.commit()
                raise HTTPException(status_code=500, detail=f"Failed to generate {doc_type} document: {str(e)}")

        project.status = "doc_review"
        await self.db.commit()
        return generated_docs

    async def generate_all_docs_stream(self, project_id: UUID, user_id: UUID):
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.solution).selectinload(Solution.problem_statement).selectinload(ProblemStatement.session),
                selectinload(Project.solution).selectinload(Solution.evaluation)
            )
        )
        result = await self.db.execute(stmt)
        project = result.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Update status to doc_generation if not already
        project.status = "doc_generation"
        await self.db.commit()

        yield {"status": "starting", "message": "Preparing project context..."}

        context = await self._build_context(project)
        
        doc_types = ["architecture", "prd", "trd", "sprint_plan", "engineering_standards"]

        for doc_type in doc_types:
            display_name = doc_type.replace("_", " ").title()
            if doc_type == "prd":
                display_name = "PRD"
            elif doc_type == "trd":
                display_name = "TRD"
                
            yield {"status": "generating", "doc_type": doc_type, "message": f"Generating {display_name}..."}
            
            try:
                await self._generate_single_doc_internal(project, doc_type, context)
            except Exception as e:
                project.status = "doc_generation_failed"
                await self.db.commit()
                raise e
            
            yield {"status": "generated", "doc_type": doc_type, "message": f"{display_name} complete"}

        project.status = "doc_review"
        await self.db.commit()

        yield {"status": "complete", "message": "All 5 documents generated", "doc_count": 5}

    async def _generate_single_doc_internal(self, project: Project, doc_type: str, context: dict) -> Document:
        # Check if document already exists
        stmt = select(Document).where(Document.project_id == project.id, Document.doc_type == doc_type)
        res = await self.db.execute(stmt)
        existing_doc = res.scalars().first()

        # Build prompt
        if doc_type == "architecture":
            system_prompt, user_prompt = build_architecture_prompt(context)
            title = f"Architecture Document - {project.name}"
        elif doc_type == "prd":
            system_prompt, user_prompt = build_prd_prompt(context)
            title = f"PRD - {project.name}"
        elif doc_type == "trd":
            system_prompt, user_prompt = build_trd_prompt(context)
            title = f"TRD - {project.name}"
        elif doc_type == "sprint_plan":
            system_prompt, user_prompt = build_sprint_plan_prompt(context)
            title = f"Sprint Plan - {project.name}"
        elif doc_type == "engineering_standards":
            system_prompt, user_prompt = build_engineering_prompt(context)
            title = f"Engineering Standards - {project.name}"
        else:
            raise ValueError(f"Unknown document type: {doc_type}")

        # Call Gemini
        content = await self.ai.generate(prompt=user_prompt, system_prompt=system_prompt)

        if existing_doc:
            existing_doc.content = content
            existing_doc.version += 1
            existing_doc.title = title
            await self.db.commit()
            await self.db.refresh(existing_doc)
            return existing_doc
        else:
            new_doc = Document(
                project_id=project.id,
                doc_type=doc_type,
                title=title,
                content=content,
                version=1,
                status="draft"
            )
            self.db.add(new_doc)
            await self.db.commit()
            await self.db.refresh(new_doc)
            return new_doc

    async def generate_document(self, project_id: UUID, doc_type: str, user_id: UUID) -> Document:
        """Generate a single document type"""
        stmt = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.solution).selectinload(Solution.problem_statement).selectinload(ProblemStatement.session),
                selectinload(Project.solution).selectinload(Solution.evaluation)
            )
        )
        result = await self.db.execute(stmt)
        project = result.scalars().first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

        context = await self._build_context(project)
        return await self._generate_single_doc_internal(project, doc_type, context)

    async def regenerate_document(self, doc_id: UUID, user_id: UUID) -> Document:
        """Regenerate a document (increments version)"""
        stmt = (
            select(Document)
            .join(Project, Document.project_id == Project.id)
            .where(Document.id == doc_id, Project.user_id == user_id)
        )
        res = await self.db.execute(stmt)
        document = res.scalars().first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found.")

        # Load project with other relations
        stmt_proj = (
            select(Project)
            .where(Project.id == document.project_id)
            .options(
                selectinload(Project.solution).selectinload(Solution.problem_statement).selectinload(ProblemStatement.session),
                selectinload(Project.solution).selectinload(Solution.evaluation)
            )
        )
        result_proj = await self.db.execute(stmt_proj)
        project = result_proj.scalars().first()
        
        context = await self._build_context(project)
        return await self._generate_single_doc_internal(project, document.doc_type, context)
