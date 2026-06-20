from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
healthRouter = APIRouter()


@healthRouter.get("")
async def get_health():
    logger.info("Checking health")
    return {"status": "App is healthy. app version: v2"}  #included app version to demo rolling update