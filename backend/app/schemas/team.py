from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints
from typing import Annotated
from app.schemas.user import UserResponse
from datetime import datetime
class TeamCreate(BaseModel):
    name : str

class TeamResponse(BaseModel):
    id : int
    name : str
    manager_id : int
    created_at : datetime
    model_config = ConfigDict(from_attributes=True)

class TeamDetailResponse(BaseModel):
    id : int
    name : str
    manager_id : int
    created_at : datetime
    model_config = ConfigDict(from_attributes=True)
    members : list[UserResponse]
class TeamMemberAdd(BaseModel):
    user_id : int 
