import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.cache import CacheService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup events
    logger.info("Initializing IdeaForge Backend...")
    cache_service = CacheService(settings.REDIS_URL)
    await cache_service.connect()
    app.state.cache = cache_service
    yield
    # Run shutdown events
    logger.info("Shutting down IdeaForge Backend...")
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
