from sqlalchemy import Column,String,Integer,DateTime,ForeignKey
from app.db.base import Base
from datetime import datetime
from app.domain.enums import UserRole,TaskStatus
from sqlalchemy import Enum as SAEnum


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150) , unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.USER)
    status = Column(SAEnum(TaskStatus), default=TaskStatus.TODO)   
    created_at = Column(DateTime, default=datetime.utcnow) 
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)