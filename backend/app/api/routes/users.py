from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.repositories.activity_repository import ActivityRepository

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/assignable", response_model=list[UserResponse])
def assignable_users(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserService(UserRepository(session),ActivityRepository(session)).assignable_users(current_user)