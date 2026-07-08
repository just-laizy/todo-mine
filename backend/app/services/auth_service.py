from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from fastapi import HTTPException, status
from app.db.models import User
from app.core.security import hash_password

class AuthService :
    def __init__(self, repository: UserRepository):
        self.repository = repository


    def register(self, name : str, email : str, password : str) -> User: 
        existing = self.repository.get_by_email(email)
        if (existing is not None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='email already registered')
        hashed = hash_password(password)
        return self.repository.create(name,email,hashed)

    
