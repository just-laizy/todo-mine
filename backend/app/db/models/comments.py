from sqlalchemy import Column,String,Integer,DateTime, Date,ForeignKey,Text
from app.db.base import Base
from datetime import datetime

class Comment(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer , ForeignKey('tasks.id'))
    author_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow) 
