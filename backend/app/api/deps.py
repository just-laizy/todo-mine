import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings 
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.db.models import User

oauth = OAuth2PasswordBearer(tokenUrl='/auth/login')

def get_current_user(
    token : str = Depends(oauth), 
    session : Session = Depends(get_db)
    ) -> User: 
    try: 
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms= [settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail='invalid or expired')
    user_id = int(payload['sub'])
    user = UserRepository(session).get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail='invalid or expired')
    return user
