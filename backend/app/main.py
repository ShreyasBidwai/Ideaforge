import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.cache import CacheService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup events
    logger.info("Initializing IdeaForge Backend...")
    
    # Run database migration to ensure pause_on_failure column exists
    try:
        from app.core.database import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE projects ADD COLUMN IF NOT EXISTS pause_on_failure BOOLEAN DEFAULT FALSE;"))
        logger.info("Successfully checked/added projects.pause_on_failure database column.")
    except Exception as e:
        logger.error(f"Failed to check/add database column during startup: {e}")

    cache_service = CacheService(settings.REDIS_URL)
    await cache_service.connect()
    app.state.cache = cache_service

    # Start build queue processing loop
    import asyncio
    from app.services.build_queue import BuildQueue
    queue_task = asyncio.create_task(BuildQueue.get_instance().start_processing())

    yield
    # Run shutdown events
    logger.info("Shutting down IdeaForge Backend...")
    queue_task.cancel()
    await cache_service.close()


app = FastAPI(
    title="IdeaForge",
    description="AI-powered startup idea discovery and validation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register aggregated routes
app.include_router(api_v1_router, prefix="/api/v1")
