import json

from app.repositories.stats_repository import StatsRepository
from app.repositories.team_repository import TeamRepository
from app.repositories.user_repository import UserRepository

from app.core.exceptions import TeamNotFound, NotAllowed

from app.domain.enums import TaskStatus, UserRole
from app.db.models import User
from app.schemas.stats import MemberStats
from datetime import date
from app.schemas.stats import LeaderboardEntry


    
import json
from app.core.cache import redis_client

BOARD_CACHE_TTL = 60  
class StatsService:
    def __init__(
        self,
        stats_repository: StatsRepository,
        team_repository: TeamRepository,
        user_repository: UserRepository
    ):
        self.stats_repository = stats_repository
        self.user_repository = user_repository
        self.team_repository = team_repository




    def board_stats(self, current_user: User) -> dict[TaskStatus, int]:
        if current_user.role == UserRole.SUPERADMIN:
            team_id = None
        else:
            team_id = current_user.team_id

        cache_key = f"stats:board:{team_id if team_id is not None else 'all'}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            return json.loads(cached)

        counts = {status: 0 for status in TaskStatus}
        for status, count in self.stats_repository.count_by_status(team_id):
            counts[status] = count

        redis_client.set(cache_key, json.dumps(counts), ex=BOARD_CACHE_TTL)
        return counts

    def leaderboard(
        self,
        current_user : User,
        from_date : date | None = None,
        to_date : date | None = None
    ) -> list[LeaderboardEntry]:
        if current_user.role == UserRole.SUPERADMIN:
            team_id = None
        else :
            team_id = current_user.team_id
        rows = self.stats_repository.completed_counts(
            team_id=team_id,
            from_date=from_date,
            to_date=to_date
        ) 
        return [LeaderboardEntry(assignee_id=a,count=c)for a,c in rows]


    def team_stats(self, team_id: int, current_user: User) -> list[MemberStats]:
        team = self.team_repository.get_by_id(team_id)
        if team is None:
            raise TeamNotFound()
        if current_user.role != UserRole.SUPERADMIN and current_user.team_id != team_id:
            raise NotAllowed()
        members = self.user_repository.get_by_team(team_id)
        stats = {
            member.id: MemberStats(user_id=member.id, counts={s: 0 for s in TaskStatus}, overdue=0)
            for member in members
        }
        for assignee_id, status, count in self.stats_repository.member_status_counts(team_id):
            if assignee_id in stats:
                stats[assignee_id].counts[status] = count
        for assignee_id, count in self.stats_repository.member_overdue_counts(team_id, date.today()):
            if assignee_id in stats:
                stats[assignee_id].overdue = count
        return list(stats.values())