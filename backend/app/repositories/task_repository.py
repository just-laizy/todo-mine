from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Task
from datetime import date

class TaskRepository:
    def __init__(self, session:Session):
        self.session = session

    def create(
        self, 
        title : str,
        description : str,
        priority : str,
        category : str,
        due_date : date,
        assignee_id : int,
        assigner_id : int
    ):
        task = Task(
            title = title,
            description = description,
            priority = priority,
            category = category,
            due_date = due_date,
            assignee_id = assignee_id,
            assigner_id = assigner_id)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

