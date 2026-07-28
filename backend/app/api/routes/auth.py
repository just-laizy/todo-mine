from app.schemas.user import UserCreate,UserResponse
from app.api.deps import get_current_user
from app.db.models import User

from fastapi import APIRouter, BackgroundTasks, Depends
from app.schemas.user import RegisterUser, RequestOTP, VerifyOTP
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(
    payload: RegisterUser,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.register(payload.name, payload.email, background_tasks)
    return {"message": "OTP sent to your email"}

@router.post("/request-otp")
def request_otp(
    payload: RequestOTP,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    auth_service.generate_and_send_otp(payload.email, background_tasks)
    return {"message": "OTP sent to your email"}

@router.post("/verify-otp")
def verify_otp(
    payload: VerifyOTP,
    auth_service: AuthService = Depends(get_auth_service)
):
    return auth_service.verify_otp(email=payload.email, code=payload.code)

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user