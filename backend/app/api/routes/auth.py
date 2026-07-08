from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate,UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])

@router.post('/register' , response_model=UserResponse, status_code=201)
def register(data: UserCreate, session : Session = Depends(get_db)):
    service = AuthService(UserRepository(session))
    return service.register(data.name, data.email,data.password)

