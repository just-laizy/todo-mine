from sqlalchemy import Column,String,Integer,DateTime, Date,ForeignKey
from app.db.base import Base
from datetime import datetime
from sqlalchemy.orm import relationship
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    manager_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow) 
    members = relationship('User', foreign_keys='User.team_id')


 
    