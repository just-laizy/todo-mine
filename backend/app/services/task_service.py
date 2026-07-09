from app.repositories.task_repository import TaskRepository
from app.db.models.task import Task
from app.db.models.user import User


class TaskService: 
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def create_task(
        self,
        title,
        description,
        priority,
        category,
        due_date,
        assignee_id,
        current_user: User
    ) -> Task:
        if assignee_id is None:
            assignee_id = current_user.id
        task = self.repository.create(title,description,priority,category,due_date,assignee_id=assignee_id,assigner_id=current_user.id) # type: ignore
        return task