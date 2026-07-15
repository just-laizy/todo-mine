from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.checklistItem_repository import ChecklistItemRepository

from app.api.deps import get_current_user
from app.db.models import User
from app.schemas.checklistItem import ChecklistItemResponse, ChecklistItemCreate
from app.services.task_service import TaskService

router = APIRouter(prefix="/checklist-items", tags=["checklist"])

@router.patch('/{task_id}/toggle', response_model=ChecklistItemResponse)
def toggle_checklist(
    item_id:int,
    session :Session= Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session), CommentRepository(session),ChecklistItemRepository(session))
    return service.toggle_item(item_id,current_user)

@router.delete('/{task_id}', status_code=204)
def delete_checklist(
    item_id:int,
    session :Session= Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TaskService(TaskRepository(session), UserRepository(session), CommentRepository(session),ChecklistItemRepository(session))
    service.delete_item(item_id, current_user)
    