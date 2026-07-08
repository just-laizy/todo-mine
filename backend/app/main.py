from fastapi import FastAPI

from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine

from app.api.routes.auth import router

app = FastAPI(title="Task Manager API")

Base.metadata.create_all(bind = engine)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}