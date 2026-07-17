import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings 
from app.db.session import get_db
from app.db.models import User
from app.services.task_service import TaskService
from app.services.team_service import TeamService
from app.domain.enums import UserRole
from app.core.exceptions import NotAllowed

from app.repositories.activity_repository import ActivityRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.checklistItem_repository import ChecklistItemRepository

oauth = OAuth2PasswordBearer(tokenUrl='/auth/login')

def get_current_user(
    token : str = Depends(oauth), 
    session : Session = Depends(get_db)
    ) -> User: 
    try: 
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms= [settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='invalid or expired')
    user_id = int(payload['sub'])
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail='invalid or expired')
    return user

def get_task_service(
    session : Session = Depends(get_db)
    ) -> TaskService:
        service = TaskService(
            TaskRepository(session),
            UserRepository(session),     
            CommentRepository(session),
            ChecklistItemRepository(session),
            ActivityRepository(session)    
        )
        return service

def get_team_service(
    session : Session = Depends(get_db)
    ) -> TeamService:
        service = TeamService(   
            TeamRepository(session),
            UserRepository(session),
            ActivityRepository(session)    
        )
        return service


def require_superadmin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPERADMIN: # type: ignore
        raise NotAllowed()
    return current_user
