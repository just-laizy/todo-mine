from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.repositories.stats_repository import StatsRepository
from app.repositories.user_repository import UserRepository
from app.repositories.team_repository import TeamRepository
from app.services.stats_service import StatsService
from app.domain.enums import TaskStatus
from fastapi import Query
from datetime import date
from app.schemas.stats import LeaderboardEntry, MemberStats


router = APIRouter(prefix='/stats' , tags=['stats'])

@router.get('/board', response_model=dict[TaskStatus,int])
def board_statS(
    session :Session= Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = StatsService(StatsRepository(session),TeamRepository(session),UserRepository(session))
    return service.board_stats(current_user)

@router.get('/leaderboard', response_model=list[LeaderboardEntry])
def leaderboard(
    from_date : date | None = Query(None, alias='from'),
    to_date : date | None = Query(None, alias='to'),
    session : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
):
    service = StatsService(StatsRepository(session),TeamRepository(session),UserRepository(session))
    return service.leaderboard(current_user,from_date,to_date)

@router.get("/team/{team_id}", response_model=list[MemberStats])
def team_stats(
    team_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = StatsService(StatsRepository(session), TeamRepository(session), UserRepository(session))
    return service.team_stats(team_id, current_user)