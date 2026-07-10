from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task import TaskCreate
from app.db.models import User
from app.services.task_service import TaskService
from app.schemas.task import TaskResponse, TaskStatusUpdate,TaskUpdate
from app.api.deps import get_current_user
from app.domain.enums import TaskPriority,TaskStatus
 


router = APIRouter(prefix='/tasks' , tags=["tasks"])

@router.post('/', response_model=TaskResponse, status_code = 201)
def task(
    data : TaskCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session))
    return service.create_task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        category=data.category,
        due_date=data.due_date,
        assignee_id=data.assignee_id,
        current_user=current_user,
    )
@router.get('/', response_model=list[TaskResponse])
def get_tasks(
    search : str | None,
    status : TaskStatus | None,
    category : str | None = None,
    assignee_id : int |None = None,
    assigner_id : int |None = None,
    session : Session = Depends(get_db),
):
    service = TaskService(TaskRepository(session),UserRepository(session))
    return service.list_tasks(
        status=status,
        category=category,
        assignee_id=assignee_id,
        assigner_id=assigner_id,
        search=search
    )

@router.get('/board', response_model=dict[TaskStatus, list[TaskResponse]])
def get_board(
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
): 
    service = TaskService(TaskRepository(session),UserRepository(session))
    return service.get_board()

@router.get('/{task_id}', response_model=TaskResponse)
def get_task(
    task_id : int, 
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session),UserRepository(session))
    return service.get_task(task_id)

@router.patch("/{task_id}/status", response_model=TaskResponse)
def change_status(
    task_id : int,
    data : TaskStatusUpdate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session))
    return service.change_status(task_id,data.status)

@router.patch('/{task_id}', response_model=TaskResponse)
def update_task(
    task_id : int,
    data : TaskUpdate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session))
    return service.update_task(task_id,data)

@router.delete('/{task_id}', status_code=204)
def delete_task(
    task_id : int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session))
    service.delete_task(task_id)