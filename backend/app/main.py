from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine
from app.core.exceptions import EmailAlreadyRegistered,AssigneeNotFound,InvalidCredentials,TaskNotFound, InvalidStatusTransition

from app.api.routes.auth import router as auth_router
from app.api.routes.tasks import router as task_router


app = FastAPI(title="Task Manager API")

Base.metadata.create_all(bind = engine)

app.include_router(auth_router)
app.include_router(task_router)

@app.exception_handler(EmailAlreadyRegistered)
def handle_email(request,exc):
    return JSONResponse(status_code=400, content={'detail' : 'Email already registered'})
@app.exception_handler(InvalidCredentials)
def handle_credentials(request,exc):
    return JSONResponse(status_code=401, content={'detail' : 'Email or password incorrect'})
@app.exception_handler(AssigneeNotFound)
def handle_assignee(request,exc):
    return JSONResponse(status_code=400, content={'detail' : 'Assignee not found'})
@app.exception_handler(TaskNotFound)
def handle_task(request,exc):
    return JSONResponse(status_code=404, content={'detail' : 'Task not found'})
@app.exception_handler(InvalidStatusTransition)
def handle_status(request,exc):
    return JSONResponse(status_code=400, content={'detail' : 'Invalid Move'})



@app.get("/health")
def health_check():
    return {"status": "ok"}