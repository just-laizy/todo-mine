from pydantic import BaseModel, ConfigDict
from datetime import date,datetime

class CommentCreate (BaseModel): 
    text : str

class CommentResponse(BaseModel):
    id : int
    text : str
    author_id : int
    task_id : int
    created_at : datetime

    