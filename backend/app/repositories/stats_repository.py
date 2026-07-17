from sqlalchemy.orm import Session
from sqlalchemy import select , func
from app.db.models import Task 
from app.domain.enums import TaskStatus
from datetime import date

class StatsRepository:
    def __init__(self, session : Session) :
        self.session = session 
        
    def count_by_status(
        self,team_id : int | None, 
    ):
        statement = select(Task.status, func.count()).group_by(Task.status)
        if team_id is not None:
            statement = statement.where(Task.team_id == team_id )
        rows = self.session.execute(statement).all()
        return rows
        
    def completed_counts(
    self,
    team_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    ):
        statement = (
            select(Task.assignee_id, func.count())
            .where(Task.status == TaskStatus.DONE)
            .group_by(Task.assignee_id)
            .order_by(func.count().desc())
        )
        if team_id is not None:
            statement = statement.where(Task.team_id == team_id)
        if from_date is not None:
            statement = statement.where(Task.done_at >= from_date)
        if to_date is not None:
            statement = statement.where(Task.done_at <= to_date)
        return self.session.execute(statement).all()
    def member_status_counts(self, team_id: int):
        statement = (
            select(Task.assignee_id, Task.status, func.count())
            .where(Task.team_id == team_id)
            .group_by(Task.assignee_id, Task.status)
        )
        return self.session.execute(statement).all()

    def member_overdue_counts(self, team_id: int, today: date):
        statement = (
            select(Task.assignee_id, func.count())
            .where(Task.team_id == team_id)
            .where(Task.due_date < today)
            .where(Task.status != TaskStatus.DONE)
            .group_by(Task.assignee_id)
        )
        return self.session.execute(statement).all()