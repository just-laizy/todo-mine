import email

from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.core.exceptions import EmailAlreadyRegistered,InvalidCredentials, TooManyAttempts
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.cache import redis_client



class AuthService :
    def __init__(self, repository: UserRepository):
        self.repository = repository
        

    def register(self, name : str, email : str, password : str) -> User: 
        existing = self.repository.get_by_email(email)
        if (existing is not None):
            raise EmailAlreadyRegistered()
        hashed = hash_password(password)
        return self.repository.create(name,email,hashed)
    
    def login(self, email: str, password: str) -> str:
        attempts_key = f"login:attempts:{email}"
        attempts = redis_client.incr(attempts_key)
        if attempts == 1:
            redis_client.expire(attempts_key, 60)
        if attempts > 5:
            raise TooManyAttempts()

        user = self.repository.get_by_email(email)
        if user is None:
            raise InvalidCredentials()
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentials()

        redis_client.delete(attempts_key)          
        return create_access_token(user.id)
    



    
