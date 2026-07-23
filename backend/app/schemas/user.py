from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated
from app.domain.enums import UserRole,TaskStatus

NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
UsernameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=100)]
PasswordStr = Annotated[str, StringConstraints(min_length=8)]

class UserCreate(BaseModel):
    name : NameStr
    email : EmailStr
    password : PasswordStr

class UserResponse(BaseModel): 
    id : int
    name : NameStr
    email : EmailStr
    role : str
    team_id: int | None = None
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    id : int | None = None
    name : NameStr | None = None
    email : EmailStr | None = None
    role : UserRole
    status : TaskStatus
    team_id : int