from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository
from app.db.models import User
from app.services.team_service import TeamService
from app.schemas.team import TeamDetailResponse ,TeamMemberAdd,TeamResponse,TeamCreate   
from app.schemas.user import UserResponse   
from app.api.deps import get_current_user
 


router = APIRouter(prefix='/teams' , tags=["teams"])

@router.post('/', response_model=TeamResponse, status_code=201)
def create_team(
    data : TeamCreate,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
): 
    service = TeamService(TeamRepository(session), UserRepository(session))
    return service.create_team(
        name=data.name,
        current_user=current_user
    )

@router.get('/{team_id}', response_model=TeamDetailResponse)
def get_team(
    team_id : int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TeamService(TeamRepository(session), UserRepository(session))
    return service.get_team(team_id)

@router.post('/{team_id}/members', response_model=UserResponse)
def add_member(
    team_id : int,
    data : TeamMemberAdd,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TeamService(TeamRepository(session), UserRepository(session))
    return service.add_member(team_id=team_id,user_id=data.user_id, current_user=current_user)

@router.delete('/')
def delete_member(
    team_id : int,
    user_id :int,
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = TeamService(TeamRepository(session), UserRepository(session))
    return service.remove_member(team_id,user_id,current_user)
    