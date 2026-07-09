from pydantic import BaseModel, ConfigDict
from app.domain.enums import TaskPriority,TaskStatus
from datetime import date,datetime

class TaskCreate(BaseModel):
    title : str
    description : str
    priority : TaskPriority
    category : str
    due_date : date | None = None
    assignee_id : int | None = None

class TaskResponse(BaseModel):
    id : int
    title : str
    description : str
    status : TaskStatus
    priority : TaskPriority
    category : str
    due_date : date | None = None
    assignee_id : int | None = None
    assigner_id : int 
    created_at : datetime
    model_config = ConfigDict(from_attributes=True)



