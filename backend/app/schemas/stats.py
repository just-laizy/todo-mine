from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from app.domain.enums import TaskStatus


class LeaderboardEntry(BaseModel):
    assignee_id: int
    count: int

class MemberStats(BaseModel):
    user_id: int
    counts: dict[TaskStatus, int]
    overdue: int
    avg_completion_hours: float | None = None