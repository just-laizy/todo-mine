from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import require_superadmin
from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.activity_repository import ActivityRepository
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.team import TeamResponse
from app.domain.enums import UserRole, UserStatus
from app.services.user_service import UserService

from app.schemas.admin import AuditEntry
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
def list_users(
    role: UserRole | None = None,
    team_id: int | None = None,
    status: UserStatus | None = None,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return UserRepository(session).get_all(role=role, team_id=team_id, status=status)

@router.get("/teams", response_model=list[TeamResponse])
def list_teams(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return TeamRepository(session).get_all()

@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin),
):
    return UserService(UserRepository(session),ActivityRepository(session)).update_user(user_id, data, current_user)

@router.get('/audit', response_model=list[AuditEntry])
def audit_log(
    limit :int = 50,
    session : Session = Depends(get_db),
    current_user : User = Depends(require_superadmin)
):
    return ActivityRepository(session).get_all(limit)