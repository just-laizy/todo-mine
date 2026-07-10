from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Task
from datetime import date
from app.domain.enums import TaskStatus

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
    
    def get_all(self, status = None, category = None, assignee_id = None, assigner_id = None, search = None):
        statement = select(Task)
        if status is not None:
            statement = statement.where(Task.status == status)
        if category is not None:
            statement = statement.where(Task.category == category)
        if assignee_id is not None:
            statement = statement.where(Task.assignee_id == assignee_id)
        if assigner_id is not None:
            statement = statement.where(Task.assigner_id == assigner_id)
        if search is not None:
            statement = statement.where(Task.title.contains(search))
        return self.session.execute(statement).scalars().all()
    
    def get_by_id(self,task_id : int)->Task | None:
        return self.session.get(Task,task_id)

    def update_status(self, task : Task, status : TaskStatus) -> Task:
        task.status = status # type: ignore
        self.session.commit()
        self.session.refresh(task)
        return task 
    def update(self,task :Task) ->Task:
        self.session.commit()
        self.session.refresh(task)
        return task
    def delete(self,task :Task) ->None:
        delete = self.session.delete(task)
        self.session.commit()
        


