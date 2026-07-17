# services/user_service.py
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.core.exceptions import UserNotFound, NotAllowed
from app.schemas.user import UserUpdate
from app.db.models.user import User


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
        if user_id == current_user.id and data.role is not None:
            raise NotAllowed()

        if data.role is not None:
            user.role = data.role
        if data.status is not None:
            user.status = data.status
        if data.team_id is not None:
            user.team_id = data.team_id
        self.activity_repository.create(current_user.id, "user.updated", f"user {user_id} changed")
        return self.user_repository.update(user)