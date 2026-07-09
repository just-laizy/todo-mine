from fastapi import FastAPI

from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine

from app.api.routes.auth import router as auth_router
from app.api.routes.tasks import router as task_router


app = FastAPI(title="Task Manager API")

Base.metadata.create_all(bind = engine)

app.include_router(auth_router)
app.include_router(task_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}