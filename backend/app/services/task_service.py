from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.core.exceptions import AssigneeNotFound
from app.db.models.task import Task
from app.db.models.user import User
from app.domain.enums import TaskStatus, TaskPriority
from datetime import date
from app.core.exceptions import InvalidStatusTransition,TaskNotFound
from app.schemas.task import TaskUpdate

AlLOWED_TRANSITIONS = {
    TaskStatus.TODO :{TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS : {TaskStatus.PENDING_REVIEW},
    TaskStatus.PENDING_REVIEW : {TaskStatus.IN_PROGRESS},
    TaskStatus.PENDING_REVIEW : {TaskStatus.DONE},

}

class TaskService: 
    def __init__(self, task_repository: TaskRepository, user_repository : UserRepository):
        self.task_repository = task_repository
        self.user_repository = user_repository

    def create_task(
        self,
        title : str,
        description : str,
        priority : TaskPriority,
        category : str,
        due_date : date | None ,
        assignee_id : int | None,
        current_user: User,
    ) -> Task:
        if assignee_id is None:
            assignee_id = current_user.id # type: ignore
        if self.user_repository.get_by_id(assignee_id) is None:  # type: ignore
            raise AssigneeNotFound()
        task = self.task_repository.create(title,description,priority,category,due_date,assignee_id=assignee_id,assigner_id=current_user.id) # type: ignore
        return task
    
    def list_tasks(self,status, category, assignee_id, assigner_id , search ):
        tasks = self.task_repository.get_all(status, category, assignee_id,assigner_id,search)
        return tasks
    def get_board(self) -> dict[TaskStatus , list[Task]]:
        tasks = self.task_repository.get_all()
        board = {status : [] for status in TaskStatus}
        for task in tasks:
            task_status = TaskStatus(task.status)
            board[task_status].append(task)
        return board
    
    def get_task(self,task_id : int) -> Task:
        task = self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFound()
        return task

    def change_status(self, task_id : int, new_status : TaskStatus) -> Task:
        task = self.get_task(task_id)
        if new_status not in AlLOWED_TRANSITIONS[task.status]: # type: ignore
            raise InvalidStatusTransition()
        return self.task_repository.update_status(task,new_status)
    
    def update_task(self,task_id : int, data : TaskUpdate):
        task = self.get_task(task_id)
        if data.title is not None:
            task.title = data.title  # type: ignore
        if data.description is not None:
            task.description = data.description  # type: ignore
        if data.priority is not None:
            task.priority = data.priority  # type: ignore
        if data.category is not None:
            task.category = data.category  # type: ignore
        if data.due_date is not None:
            task.due_date = data.due_date  # type: ignore
        if data.assignee_id is not None:
            if self.user_repository.get_by_id(data.assignee_id) is None:  # type: ignore
                raise AssigneeNotFound()
            task.assignee_id = data.assignee_id  # type: ignore
        return self.task_repository.update(task)
    
    def delete_task(self,task_id : int):
        task=self.get_task(task_id)
        self.task_repository.delete(task)

        



