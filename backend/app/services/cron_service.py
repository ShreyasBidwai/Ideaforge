import asyncio
from datetime import datetime
from uuid import UUID

class CronService:
    """Simple in-process scheduler for resuming builds after rate limits"""
    
    _scheduled_jobs: dict[str, asyncio.Task] = {}
    
    @classmethod
    async def schedule_resume(cls, project_id: UUID, resume_at: datetime, callback):
        """
        Schedule a one-shot job to resume the build.
        1. Calculate seconds until resume_at
        2. Create asyncio task that sleeps then calls callback
        3. Store task reference for cancellation
        """
        delay = (resume_at - datetime.utcnow()).total_seconds()
        if delay < 0:
            delay = 60  # minimum 1 minute wait
        
        async def _job():
            await asyncio.sleep(delay)
            await callback(project_id)
            cls._scheduled_jobs.pop(str(project_id), None)
        
        # Cancel existing job for this project if any
        existing = cls._scheduled_jobs.get(str(project_id))
        if existing:
            existing.cancel()
        
        cls._scheduled_jobs[str(project_id)] = asyncio.create_task(_job())
    
    @classmethod
    async def cancel_job(cls, project_id: UUID):
        """Cancel a scheduled resume"""
        job = cls._scheduled_jobs.pop(str(project_id), None)
        if job:
            job.cancel()
