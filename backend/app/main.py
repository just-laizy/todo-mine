from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db import models
from app.db.base import Base
from app.db.session import engine
from app.core.exceptions import EmailAlreadyRegistered,AssigneeNotFound,InvalidCredentials,TaskNotFound, InvalidStatusTransition, TooManyAttempts, UserNotFound,NotAllowed,TeamNotFound,CommentRequired

from app.api.routes.auth import router as auth_router
from app.api.routes.tasks import router as task_router
from app.api.routes.teams import router as team_router
from app.api.routes.checklist import router as checklist_router
from app.api.routes.stats import router as stats_router
from app.api.routes.admin import router as admin_router
from app.api.routes.users import router as user_router

from fastapi.staticfiles import StaticFiles
from pathlib import Path

import mimetypes
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")

app = FastAPI(title="Ojak")


from fastapi.middleware.cors import CORSMiddleware

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

Base.metadata.create_all(bind = engine)

app.include_router(auth_router)
app.include_router(checklist_router)
app.include_router(task_router)
app.include_router(team_router)
app.include_router(stats_router)
app.include_router(admin_router )   
app.include_router(user_router)


@app.exception_handler(EmailAlreadyRegistered)
def handle_email(request,exc):
    return JSONResponse(
        status_code=400, 
        content={'detail' : 'Email already registered'}
    )
@app.exception_handler(InvalidCredentials)
def handle_credentials(request,exc):
    return JSONResponse(
        status_code=401, 
        content={'detail' : 'Email or password incorrect'}
    )
@app.exception_handler(AssigneeNotFound)
def handle_assignee(request,exc):
    return JSONResponse(
        status_code=400, 
        content={'detail' : 'Assignee not found'}
    )
@app.exception_handler(TaskNotFound)
def handle_task(request,exc):
    return JSONResponse(
        status_code=404, 
        content={'detail' : 'Task not found'}
    )
@app.exception_handler(InvalidStatusTransition)
def handle_status(request,exc):
    return JSONResponse(
        status_code=400, 
        content={'detail' : 'Invalid Move'}
    )
@app.exception_handler(NotAllowed)
def handle_notallowed(request,exc):
    return JSONResponse(
        status_code=403,
        content={'detail' : str(exc) or 'You are not allowed to do that'}
    )
@app.exception_handler(TeamNotFound)
def handle_team(request,exc):
    return JSONResponse(
        status_code=403, 
        content={'detail' : 'Team not found'}
    )
@app.exception_handler(CommentRequired)
def handle_comment(request,exc):
    return JSONResponse(
        status_code=400, 
        content={'detail' : 'required a comment'}
    )
@app.exception_handler(UserNotFound)
def handle_user(request,exc):
    return JSONResponse(
        status_code=401, 
        content={'detail' : 'user not found'}
    )
@app.exception_handler(TooManyAttempts)
def handle_too_many_attempts(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many login attempts. Try again in a minute."})
@app.get("/health")
def health_check():
    return {"status": "ok"}


# frontend_dir = Path(__file__).parent.parent.parent / "frontend"
# app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")