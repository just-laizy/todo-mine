from sqlalchemy import Column,String,Integer,DateTime, Date,ForeignKey
from sqlalchemy import Enum as SAEnum 
from sqlalchemy.orm import relationship
from app.domain.enums import TaskStatus, TaskPriority , TaskCategory
from app.db.base import Base
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

task_collaborators = Table(
    "task_collaborators",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=True)
    description = Column(String(1000)) 
    status = Column(SAEnum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(SAEnum(TaskPriority), default=TaskPriority.LOW) 
    category = Column(SAEnum(TaskCategory), default=TaskCategory.BACKEND, nullable=False)
    due_date = Column(DateTime, nullable=True) 
    assignee_id = Column(Integer, ForeignKey('users.id'))
    assigner_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow) 
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    done_at = Column(DateTime, nullable=True)
    comments = relationship("Comment", cascade="all, delete-orphan")
    checklist_items = relationship("ChecklistItem", cascade="all, delete-orphan")
    collaborators = relationship("User", secondary=task_collaborators)