from fastapi import FastAPI
from app.api.v1.student_routes import router
from app.core.config import settings

app = FastAPI(title=settings.APP_NAME)
app.include_router(router, prefix="/api/v1/students", tags=["Students"])
