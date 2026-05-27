import asyncio
import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

class BuildQueue:
    """
    Manages sequential build execution.
    Only one build runs at a time. Others wait in queue.
    """
    
    _instance = None
    _queue: asyncio.Queue = None
    _current_build: UUID | None = None
    _is_processing: bool = False
    
    @classmethod
    def get_instance(cls) -> 'BuildQueue':
        if cls._instance is None:
            cls._instance = cls()
            cls._queue = asyncio.Queue()
        return cls._instance
    
    async def enqueue_build(self, project_id: UUID, user_id: UUID) -> dict:
        """
        Add a project to the build queue.
        Returns: {
            "position": int (1-based position in queue),
            "estimated_wait": str (e.g., "~2 hours based on queue depth"),
            "status": "queued"
        }
        If no builds running, starts immediately.
        """
        # Check if project already in queue
        items = list(self._queue._queue)
        for idx, (pid, uid) in enumerate(items):
            if str(pid) == str(project_id):
                return {
                    "position": idx + 1,
                    "estimated_wait": f"~{idx * 2} hours based on queue depth",
                    "status": "queued"
                }
        
        # Put in queue
        await self._queue.put((project_id, user_id))
        
        # Calculate position (1-based)
        position = self._queue.qsize()
        
        # Set project status to queued in DB if database is accessible
        try:
            from app.core.database import async_session
            from app.models.project import Project
            async with async_session() as db_session:
                stmt = select(Project).where(Project.id == project_id)
                res = await db_session.execute(stmt)
                project = res.scalars().first()
                if project and project.status != "building":
                    project.status = "queued"
                    await db_session.commit()
        except Exception:
            pass

        return {
            "position": position,
            "estimated_wait": f"~{(position - 1) * 2} hours based on queue depth",
            "status": "queued"
        }
    
    async def start_processing(self):
        """
        Main queue processing loop (runs as background task).
        1. Dequeue next project
        2. Set as current build
        3. Run BuildOrchestrator.start_build()
        4. On completion/failure, dequeue next
        5. On rate limit, pause current but DON'T skip to next
           (next build would also be rate limited)
        """
        if self._is_processing:
            return
        self._is_processing = True
        logger.info("Build queue processing loop started.")
        try:
            while True:
                project_id, user_id = await self._queue.get()
                self._current_build = project_id
                logger.info(f"Processing build for project: {project_id}")
                
                while True:
                    from app.core.database import async_session
                    from app.models.project import Project
                    from app.models.sprint_task import SprintTask
                    from app.models.sprint import Sprint
                    from app.services.build_orchestrator import BuildOrchestrator
                    
                    async with async_session() as db_session:
                        stmt = select(Project).where(Project.id == project_id)
                        res = await db_session.execute(stmt)
                        project = res.scalars().first()
                        
                        if not project or project.status in ("failed", "complete"):
                            break
                        
                        if project.status == "queued":
                            project.status = "building"
                            await db_session.commit()
                            
                        orch = BuildOrchestrator(db_session)
                        try:
                            await orch.start_build(project_id, user_id)
                        except Exception as e:
                            logger.error(f"Error building project {project_id}: {e}")
                        
                        await db_session.refresh(project)
                        if project.status == "rate_limited":
                            reset_time = None
                            stmt_tasks = select(SprintTask).join(Sprint).where(Sprint.project_id == project_id)
                            res_tasks = await db_session.execute(stmt_tasks)
                            tasks = res_tasks.scalars().all()
                            for t in tasks:
                                if t.status == "rate_limited" and t.rate_limit_reset_at:
                                    reset_time = t.rate_limit_reset_at
                                    break
                            
                            now = datetime.utcnow()
                            if reset_time and reset_time > now:
                                sleep_seconds = (reset_time - now).total_seconds()
                            else:
                                sleep_seconds = 60
                                
                            logger.info(f"Queue paused due to rate limit. Sleeping for {sleep_seconds} seconds.")
                            await asyncio.sleep(sleep_seconds)
                            
                            project.status = "building"
                            await db_session.commit()
                            continue
                        else:
                            break
                
                self._current_build = None
                self._queue.task_done()
        except asyncio.CancelledError:
            logger.info("Build queue processing loop cancelled.")
        except Exception as e:
            logger.error(f"Error in build queue processing loop: {e}")
        finally:
            self._is_processing = False
    
    async def get_queue_status(self) -> dict:
        """
        Returns: {
            "current_build": {project_id, name, progress} | None,
            "queued": [{project_id, name, position, estimated_wait}],
            "total_in_queue": int
        }
        """
        current_build_info = None
        if self._current_build:
            name = str(self._current_build)
            progress = 0
            try:
                from app.core.database import async_session
                from app.models.project import Project
                from app.models.sprint import Sprint
                from app.models.sprint_task import SprintTask
                async with async_session() as db_session:
                    stmt = select(Project).where(Project.id == self._current_build)
                    res = await db_session.execute(stmt)
                    proj = res.scalars().first()
                    if proj:
                        name = proj.name
                        stmt_tasks = select(SprintTask).join(Sprint).where(Sprint.project_id == self._current_build)
                        res_tasks = await db_session.execute(stmt_tasks)
                        tasks = res_tasks.scalars().all()
                        if tasks:
                            passed = len([t for t in tasks if t.status == "passed"])
                            progress = int((passed / len(tasks)) * 100)
            except Exception:
                pass
            current_build_info = {
                "project_id": str(self._current_build),
                "name": name,
                "progress": progress
            }

        queued_list = []
        items = list(self._queue._queue)
        for idx, (pid, uid) in enumerate(items):
            name = str(pid)
            try:
                from app.core.database import async_session
                from app.models.project import Project
                async with async_session() as db_session:
                    stmt = select(Project).where(Project.id == pid)
                    res = await db_session.execute(stmt)
                    proj = res.scalars().first()
                    if proj:
                        name = proj.name
            except Exception:
                pass
            queued_list.append({
                "project_id": str(pid),
                "name": name,
                "position": idx + 1,
                "estimated_wait": f"~{idx * 2} hours based on queue depth"
            })

        return {
            "current_build": current_build_info,
            "queued": queued_list,
            "total_in_queue": len(queued_list)
        }
    
    async def cancel_queued(self, project_id: UUID, user_id: UUID) -> bool:
        """Remove a project from the queue (not the currently running one)"""
        temp_list = []
        found = False
        while not self._queue.empty():
            item = self._queue.get_nowait()
            if str(item[0]) == str(project_id):
                found = True
            else:
                temp_list.append(item)
        for item in temp_list:
            self._queue.put_nowait(item)
            
        if found:
            try:
                from app.core.database import async_session
                from app.models.project import Project
                async with async_session() as db_session:
                    stmt = select(Project).where(Project.id == project_id)
                    res = await db_session.execute(stmt)
                    project = res.scalars().first()
                    if project:
                        project.status = "doc_review"
                        await db_session.commit()
            except Exception:
                pass
        return found
    
    async def get_position(self, project_id: UUID) -> int | None:
        """Get queue position for a project (None if not in queue)"""
        items = list(self._queue._queue)
        for idx, (pid, uid) in enumerate(items):
            if str(pid) == str(project_id):
                return idx + 1
        return None
