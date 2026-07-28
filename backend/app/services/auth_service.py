import email

from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.core.exceptions import EmailAlreadyRegistered,InvalidCredentials, TooManyAttempts
from app.db.models import User
from app.core.security import hash_password, verify_password, create_access_token
from app.core.cache import redis_client



# class AuthService :
#     def __init__(self, repository: UserRepository):
#         self.repository = repository
        

#     def register(self, name : str, email : str, password : str) -> User: 
#         existing = self.repository.get_by_email(email)
#         if (existing is not None):
#             raise EmailAlreadyRegistered()
#         hashed = hash_password(password)
#         return self.repository.create(name,email,hashed)
    
#     def login(self, email: str, password: str) -> str:
#         attempts_key = f"login:attempts:{email}"
#         attempts = redis_client.incr(attempts_key)
#         if attempts == 1:
#             redis_client.expire(attempts_key, 60)
#         if attempts > 5:
#             raise TooManyAttempts()

#         user = self.repository.get_by_email(email)
#         if user is None:
#             raise InvalidCredentials()
#         if not verify_password(password, user.hashed_password):
#             raise InvalidCredentials()

#         redis_client.delete(attempts_key)          
#         return create_access_token(user.id)
    

import random
from datetime import datetime, timedelta, timezone
from fastapi import BackgroundTasks, HTTPException, status
from app.repositories.user_repository import UserRepository
from app.utils.email import send_otp_email
from app.core.security import create_access_token  # Ensure this matches your token utility import
from app.core.exceptions import EmailAlreadyRegistered
from app.domain.enums import UserRole

OTP_TTL_MINUTES = 10

class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register(self, name: str, email: str, background_tasks: BackgroundTasks):
        # 1. Reject duplicates up front (handled -> 400 "Email already registered").
        if self.repository.get_by_email(email):
            raise EmailAlreadyRegistered()

        # 2. The very first account to register bootstraps the superadmin;
        #    everyone after is a regular user.
        role = UserRole.SUPERADMIN if self.repository.count() == 0 else UserRole.USER

        # 3. Create the (password-less) account with an OTP already attached.
        otp_code = f"{random.randint(100000, 999999)}"
        otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
        self.repository.create_otp_user(
            name=name, email=email, role=role, otp_code=otp_code, otp_expiry=otp_expiry
        )

        # 4. Queue the (slow) SMTP send so the request returns fast.
        background_tasks.add_task(send_otp_email, email, otp_code)

    def generate_and_send_otp(self, email: str, background_tasks: BackgroundTasks):
        # 1. Generate 6-digit random code
        otp_code = f"{random.randint(100000, 999999)}"

        # 2. Save OTP to DB via UserRepository.
        #    Runs synchronously so an unknown email returns a clean 404 to the
        #    client, instead of raising inside a background task after the
        #    response has already been sent.
        self.repository.save_otp(email=email, otp_code=otp_code)

        # 3. Queue the (slow) SMTP send in the background so the request stays fast.
        background_tasks.add_task(send_otp_email, email, otp_code)

    def verify_otp(self, email: str, code: str):
        user = self.repository.get_by_email(email)

        # 1. Check if user exists and OTP matches
        if not user or user.otp != code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )

        # 2. Check expiration (timezone aware)
        now = datetime.now(timezone.utc)
        user_expiry = user.otp_expiry

        if user_expiry and user_expiry.tzinfo is None:
            user_expiry = user_expiry.replace(tzinfo=timezone.utc)

        if not user_expiry or user_expiry < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )

        # 3. Clear OTP so it can't be reused
        self.repository.clear_otp(user)

        # 4. Generate JWT access token
        access_token = create_access_token(user.id)
        return {"access_token": access_token, "token_type": "bearer"}