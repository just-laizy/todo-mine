from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import User


class UserRepository:
    def __init__(self,session : Session ):
        self.session = session

    def get_by_email(self, email : str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.execute(statement).scalar_one_or_none()
    
    def create(self, name:str, email:str, hashed_password : str) -> User:
        user = User(name = name, email = email, hashed_password = hashed_password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
        
        
        