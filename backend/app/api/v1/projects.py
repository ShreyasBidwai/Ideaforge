from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User, Solution, ProblemStatement, Session
from app.models.project import Project
from app.models.document import Document
from app.schemas.project import ProjectResponse, DocumentResponse
from app.services.doc_generation_service import DocGenerationService
from app.ai.provider import get_ai_provider, AIProvider

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/solutions/{solution_id}/create-project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    solution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Fetch solution with problem and session details
    stmt = (
        select(Solution)
        .where(Solution.id == solution_id)
        .options(selectinload(Solution.problem_statement).selectinload(ProblemStatement.session))
    )
    result = await db.execute(stmt)
    solution = result.scalars().first()
    if not solution:
        raise HTTPException(status_code=404, detail="Solution not found")

    # Check if solution is approved
    if solution.status != "approved":
        raise HTTPException(status_code=400, detail="Solution must be approved to create a project")

    # Check if project already exists
    stmt_existing = select(Project).where(Project.solution_id == solution_id)
    res_existing = await db.execute(stmt_existing)
    existing_project = res_existing.scalars().first()
    if existing_project:
        return existing_project

    problem = solution.problem_statement
    session = problem.session

    new_project = Project(
        user_id=current_user.id,
        solution_id=solution.id,
        name=solution.title,
        description=solution.description,
        industry=session.industry,
        location=session.location,
        maturity_level=session.maturity_level,
        tech_stack=solution.tech_stack or [],
        status="doc_generation"
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.user_id == current_user.id).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/projects/{id}")
async def get_project(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Project)
        .where(Project.id == id, Project.user_id == current_user.id)
        .options(selectinload(Project.documents), selectinload(Project.sprints))
    )
    res = await db.execute(stmt)
    project = res.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{id}/generate-docs", response_model=list[DocumentResponse])
async def generate_docs(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    ai_provider: AIProvider = Depends(get_ai_provider)
):
    service = DocGenerationService(ai_provider, db)
    return await service.generate_all_docs(id, current_user.id)

@router.get("/projects/{id}/documents", response_model=list[DocumentResponse])
async def list_project_documents(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_proj = select(Project).where(Project.id == id, Project.user_id == current_user.id)
    proj_res = await db.execute(stmt_proj)
    if not proj_res.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(Document).where(Document.project_id == id)
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/projects/{id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_project_document(
    id: UUID,
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Document)
        .join(Project, Document.project_id == Project.id)
        .where(Document.id == doc_id, Document.project_id == id, Project.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    doc = res.scalars().first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
