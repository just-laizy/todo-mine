from sqlalchemy import Column,String,Integer,DateTime, Date,ForeignKey,Text,Boolean
from app.db.base import Base
from datetime import datetime, timezone

class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100))
    details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    