from sqlalchemy import Column,String,Integer,DateTime
from app.db.base import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150) , unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    role = Column(String(20) ,default='user')
    status = Column(String(20), default='active')   
    created_at = Column(DateTime, default=datetime.utcnow) 
