from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate,UserResponse
from app.services.auth_service import AuthService
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register' , response_model=UserResponse, status_code=201)
def register(data: UserCreate, session : Session = Depends(get_db)):
    service = AuthService(UserRepository(session))
    return service.register(data.name, data.email,data.password)

@router.post('/login')
def login(
    form : OAuth2PasswordRequestForm = Depends(), 
    session : Session = Depends(get_db)
):
    service = AuthService(UserRepository(session))
    token = service.login(form.username, form.password)
    return {"access_token" : token, "token_type" : "bearer"}


