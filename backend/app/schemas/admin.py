from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AuditEntry(BaseModel):
    id : int
    user_id : int
    action : str
    details : str
    created_at : datetime

    model_config = ConfigDict(from_attributes = True)
    
