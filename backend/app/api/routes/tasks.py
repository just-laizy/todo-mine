from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate
from app.db.models import User
from app.services.task_service import TaskService
from app.schemas.task import TaskResponse
from app.api.deps import get_current_user



router = APIRouter(prefix='/tasks' , tags=["tasks"])

@router.post('/', response_model=TaskResponse, status_code = 201)
def task(
    data : TaskCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session))
    return service.create_task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            category=data.category,
            due_date=data.due_date,
            assignee_id=data.assignee_id,
            current_user=current_user,
    )
