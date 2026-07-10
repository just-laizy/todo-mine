from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.core.exceptions import EmailAlreadyRegistered,InvalidCredentials
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token



class AuthService :
    def __init__(self, repository: UserRepository):
        self.repository = repository


    def register(self, name : str, email : str, password : str) -> User: 
        existing = self.repository.get_by_email(email)
        if (existing is not None):
            raise EmailAlreadyRegistered()
        hashed = hash_password(password)
        return self.repository.create(name,email,hashed)
    
    def login(self,email : str,password : str) -> str:
        user = self.repository.get_by_email(email)
        if user is None:
            raise InvalidCredentials()
        if not verify_password(password, user.hashed_password): # type: ignore
            raise InvalidCredentials()
        return create_access_token(user.id) # type: ignore
    



    
