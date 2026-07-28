from pydantic import BaseModel, ConfigDict
from app.domain.enums import TaskPriority,TaskStatus, ReviewDecision, TaskCategory
from datetime import date,datetime

from app.schemas.user import UserMini

class TaskCreate(BaseModel):
    title : str
    description : str
    priority : TaskPriority
    category : TaskCategory
    due_date : date | None = None
    assignee_id : int | None = None
    collaborator_ids: list[int] = []

class CollaboratorsUpdate(BaseModel):
    user_ids: list[int]

class TaskResponse(BaseModel):
    id : int
    title : str
    description : str
    status : TaskStatus
    priority : TaskPriority
    category : TaskCategory
    collaborators: list[UserMini] = []
    due_date : date | None = None
    assignee_id : int | None = None
    assigner_id : int 
    created_at : datetime
    done_at : datetime | None= None
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
    

class TaskStatusUpdate(BaseModel):
    status : TaskStatus

class TaskUpdate(BaseModel):
    title : str | None = None
    description : str | None = None
    priority : TaskPriority | None = None
    category : TaskCategory | None = None
    due_date : date | None = None
    assignee_id : int | None = None

class ReviewCreate(BaseModel):
    decision : ReviewDecision
    comment : str | None = None

