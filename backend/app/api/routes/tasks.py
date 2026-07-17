from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.checklistItem_repository import ChecklistItemRepository


from app.schemas.comment import CommentResponse , CommentCreate
from app.db.models import User
from app.services.task_service import TaskService
from app.schemas.task import TaskResponse, TaskStatusUpdate,TaskUpdate, TaskCreate,ReviewCreate
from app.schemas.checklistItem import ChecklistItemResponse, ChecklistItemCreate
from app.api.deps import get_current_user,get_task_service
from app.domain.enums import TaskPriority,TaskStatus



router = APIRouter(prefix='/tasks' , tags=["tasks"])

@router.post('/', response_model=TaskResponse, status_code = 201)
def create_task(
    data : TaskCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)
):
    
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
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):    

    return service.list_tasks(
        status=status,
        category=category,
        assignee_id=assignee_id,
        assigner_id=assigner_id,
        search=search,
        current_user=current_user
    )

@router.get('/board', response_model=dict[TaskStatus, list[TaskResponse]])
def get_board(
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

): 
    return service.get_board(current_user)

@router.get('/{task_id}', response_model=TaskResponse)
def get_task(
    task_id : int, 
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):
    return service.get_task(task_id, current_user)

@router.patch("/{task_id}/status", response_model=TaskResponse)
def change_status(
    task_id : int,
    data : TaskStatusUpdate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):
    return service.change_status(task_id,data.status, current_user)

@router.patch('/{task_id}', response_model=TaskResponse)
def update_task(
    task_id : int,
    data : TaskUpdate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):
    return service.update_task(task_id,data,current_user)

@router.delete('/{task_id}', status_code=204)
def delete_task(
    task_id : int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):    
    service.delete_task(task_id, current_user)

@router.post('/{task_id}/comments', response_model=CommentResponse, status_code=201)
def add_comment(
    task_id :int,
    data :CommentCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)

):
    return service.add_comment(task_id,current_user,data.text)

@router.get('/{task_id}/comments', response_model=list[CommentResponse], status_code=201)
def list_comments(
    task_id :int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)
):
    return list(service.list_comments(task_id,current_user))

@router.post('/{task_id}/review', response_model=TaskResponse)
def review_create(
    task_id : int,
    data : ReviewCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)
):
    return service.review_task(task_id,data.decision,data.comment,current_user)

@router.post('/{task_id}/checklist', response_model=ChecklistItemResponse)
def add_checklists(
    task_id : int,
    data : ChecklistItemCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)
):
    return service.add_item(text=data.text, task_id=task_id,current_user=current_user)

@router.get('/{task_id}/checklist', response_model=list[ChecklistItemResponse])
def get_checklist(
    task_id : int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user),
    service : TaskService = Depends(get_task_service)
):
    return service.list_items(task_id=task_id,current_user=current_user)
