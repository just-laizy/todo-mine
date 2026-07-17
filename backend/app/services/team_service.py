from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.repositories.activity_repository import ActivityRepository
from app.core.exceptions import NotAllowed, TeamNotFound, AssigneeNotFound
from app.domain.enums import UserRole
from app.db.models.user import User
from app.db.models.team import Team


class TeamService: 
    def __init__(
            self,
            team_repository: TeamRepository,
            user_repository : UserRepository,
            activity_repository : ActivityRepository
        ):
        self.team_repository = team_repository
        self.user_repository = user_repository
        self.activity_repository = activity_repository
    
    def create_team(self,name : str,current_user : User) ->Team:
        if current_user.role not in (UserRole.SUPERADMIN,UserRole.MANAGER):
            raise NotAllowed()
        team = self.team_repository.create(name = name,manager_id=current_user.id)
        self.user_repository.set_team(current_user,team.id)  # type: ignore
        return team
    
    def get_team(self,team_id : int) -> Team:
        team = self.team_repository.get_by_id(team_id)
        if team is None:
            raise TeamNotFound()
        return team
    
    def add_member(self, team_id : int, user_id : int, current_user : User) -> User:
        team = self.get_team(team_id)
        team_manager = current_user.id == team.manager_id
        superadmin = current_user.role == UserRole.SUPERADMIN  
        if not (team_manager or superadmin): # type: ignore
            raise NotAllowed()
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise AssigneeNotFound()
        self.activity_repository.create(current_user.id, "team.member_added", f"user {user_id} -> team {team_id}")# type: ignore
        return  self.user_repository.set_team(user,team.id)# type: ignore

    def remove_member(self,team_id : int, user_id: int, current_user : User) -> User:
        team = self.get_team(team_id)
        team_manager = current_user.id == team.manager_id
        superadmin = current_user.role == UserRole.SUPERADMIN  
        if not (team_manager or superadmin): # type: ignore
            raise NotAllowed()
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise AssigneeNotFound()
        self.activity_repository.create(current_user.id, "team.member_removed", f"user {user_id} from team {team_id}")# type: ignore
        return self.user_repository.set_team(user, None)

        
