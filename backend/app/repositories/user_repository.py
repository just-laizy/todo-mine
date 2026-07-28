from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import User
from app.db.models.task import Task
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

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
    
    def count(self) -> int:
        return self.session.query(User).count()

    def create_otp_user(self, name: str, email: str, role, otp_code: str, otp_expiry) -> User:
        user = User(
            name=name,
            email=email,
            role=role,
            otp=otp_code,
            otp_expiry=otp_expiry,
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self,user_id : int) -> User | None :
        user = self.session.get(User, user_id)
        return user 
        
    def get_by_team(self,team_id : int) -> list[User]:
        statement = select(User).where(User.team_id == team_id)
        return list(self.session.execute(statement).scalars().all())
    
    def set_team(self,user : User,team_id : int | None)-> User:
        user.team_id = team_id # type: ignore
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def get_all(self,role = None,team_id  = None,status = None):
        statement = select(User)
        if role is not None:
            statement = statement.where(User.role == role)
        if team_id is not None:
            statement = statement.where(User.team_id == team_id)
        if status is not None:
            statement = statement.where(User.status == status)
        return self.session.execute(statement).scalars().all()
    def update(self,user : User) -> User:
        self.session.commit()
        self.session.refresh(user)
        return user
    # otp 
    def save_otp(self, email: str, otp_code: str):
    # 1. Fetch existing user
        user = self.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 2. Update OTP and expiration (e.g. valid for 10 minutes)
        user.otp = otp_code
        user.otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # 3. Save to database
        self.session.commit()
        self.session.refresh(user)
        return user
    def clear_otp(self, user:User):
        user.otp = None
        user.otp_expiry = None
        self.session.commit()