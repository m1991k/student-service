from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(settings.MONGO_URI)
logger.info("MongoDB client created")

db = client[settings.MONGO_DB]
logger.info(f"Connected to database: {settings.MONGO_DB}")
