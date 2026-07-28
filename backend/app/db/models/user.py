from sqlalchemy import Column,String,Integer,DateTime,ForeignKey
from app.db.base import Base
from datetime import datetime
from app.domain.enums import UserRole,UserStatus
from sqlalchemy import Enum as SAEnum


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150) , unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SAEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow) 
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
# otp
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)

