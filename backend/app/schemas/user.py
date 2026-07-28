from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated
from app.domain.enums import UserRole,UserStatus


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
    role : UserRole
    status : UserStatus = UserStatus.ACTIVE
    team_id: int | None = None
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    role: UserRole | None = None
    status: UserStatus | None = None
    team_id: int | None = None

class UserMini(BaseModel):
    
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class RegisterUser(BaseModel):
    name : NameStr
    email : EmailStr

class RequestOTP(BaseModel):
    email: EmailStr

class VerifyOTP(BaseModel):
    email: EmailStr
    code: str