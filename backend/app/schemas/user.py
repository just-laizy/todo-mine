from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated

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
    model_config = ConfigDict(from_attributes=True)
