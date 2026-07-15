from pydantic import BaseModel, ConfigDict

class ChecklistItemCreate(BaseModel):
    text : str
    
class ChecklistItemResponse(BaseModel):
    id : int
    text : str
    done_flag : bool
    position : int
    task_id : int
    model_config = ConfigDict(from_attributes=True)
    


