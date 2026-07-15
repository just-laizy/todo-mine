from sqlalchemy import Column,String,Integer,DateTime, Date,ForeignKey,Text,Boolean
from app.db.base import Base

class ChecklistItem(Base):
    __tablename__ = 'checklists'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    position = Column(Integer)
    done_flag = Column(Boolean , default=False)
    task_id = Column(Integer , ForeignKey('tasks.id'))
    
