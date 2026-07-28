# services/user_service.py
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.core.exceptions import UserNotFound, NotAllowed
from app.schemas.user import UserUpdate
from app.db.models.user import User
from app.domain.enums import UserRole

class UserService:
    def __init__(
            self,
            user_repository: UserRepository,
            activity_repository : ActivityRepository 
        ):
        self.user_repository = user_repository
        self.activity_repository = activity_repository

    def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        if user_id == current_user.id and data.role is not None and data.role != user.role:
            raise NotAllowed("You cannot change your own role")

        fields = data.model_fields_set
        changes: list[str] = []

        if data.role is not None and data.role != user.role:
            changes.append(f"role {user.role.value} -> {data.role.value}")  # type: ignore
            user.role = data.role  # type: ignore
        if data.status is not None and data.status != user.status:
            changes.append(f"status {user.status.value} -> {data.status.value}")  # type: ignore
            user.status = data.status  # type: ignore
        if "team_id" in fields and data.team_id != user.team_id:
            changes.append(f"team {user.team_id} -> {data.team_id}")
            user.team_id = data.team_id  # type: ignore

        if not changes:
            return user

        updated = self.user_repository.update(user)
        self.activity_repository.create(
            current_user.id, "user.updated", f"user {user_id} ({user.name}): " + ", ".join(changes)
        )
        return updated

    def assignable_users(self, current_user: User) -> list[User]:
        if current_user.role == UserRole.SUPERADMIN:
            return self.user_repository.get_all()
        if current_user.team_id is None:
            return [current_user]
        members = self.user_repository.get_by_team(current_user.team_id)
        if current_user.role == UserRole.MANAGER:
            return members
        return [m for m in members if m.role == UserRole.USER]