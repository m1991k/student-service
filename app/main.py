from fastapi import FastAPI
from app.api.v1.student_routes import studentRouter
from app.api.v1.health_routes import healthRouter
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.APP_NAME)
logger.info(f"Starting {settings.APP_NAME}")
app.include_router(studentRouter, prefix="/api/v1/students", tags=["Students"])
app.include_router(healthRouter, prefix="/api/v1/health", tags=["Health"])
