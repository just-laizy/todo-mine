from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.checklistItem_repository import ChecklistItemRepository


from app.core.exceptions import AssigneeNotFound
from app.db.models import Task,User, Comment, ChecklistItem
from app.domain.enums import TaskStatus, TaskPriority
from datetime import date
from app.core.exceptions import InvalidStatusTransition,TaskNotFound, NotAllowed,CommentRequired
from app.schemas.task import TaskUpdate
from app.domain.enums import UserRole,ReviewDecision

AlLOWED_TRANSITIONS = {
    TaskStatus.TODO :{TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS : {TaskStatus.PENDING_REVIEW},
    TaskStatus.PENDING_REVIEW : {TaskStatus.IN_PROGRESS},
    TaskStatus.PENDING_REVIEW : {TaskStatus.DONE},

}
DECISION_OUTCOMES = {
    ReviewDecision.APPROVED: TaskStatus.DONE,
    ReviewDecision.CHANGES_REQUESTED: TaskStatus.IN_PROGRESS,
    ReviewDecision.DECLINED: TaskStatus.TODO,
}
class TaskService: 
    def __init__(
        self,
        task_repository: TaskRepository,
        user_repository : UserRepository,
        comment_repository : CommentRepository,
        checklist_repository : ChecklistItemRepository,
        activity_repository : ActivityRepository

    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.comment_repository = comment_repository
        self.checklist_repository = checklist_repository
        self.activity_repository = activity_repository

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
            assignee_id = current_user.id #type: ignore
        assignee = self.user_repository.get_by_id(assignee_id)#type:ignore
        if assignee is None:  
            raise AssigneeNotFound()
        if assignee_id != current_user.id and current_user.role == UserRole.USER: # type: ignore
            raise NotAllowed()
        if current_user.role == UserRole.MANAGER and assignee.team_id != current_user.team_id: # type: ignore
            raise NotAllowed()
        
        task = self.task_repository.create(
            title,
            description,
            priority,
            category,
            due_date,
            assignee_id=assignee_id,# type: ignore
            assigner_id=current_user.id,# type: ignore
            team_id = current_user.team_id) # type: ignore
        self.activity_repository.create(current_user.id, "task.created", f"task {task.id}: {task.title}")# type: ignore
        return task
    
    def list_tasks(self,status, category, assignee_id, assigner_id , search, current_user : User ):
        if current_user.role == UserRole.SUPERADMIN:#type: ignore
            team_id = None
        else :
            team_id = current_user.team_id
        tasks = self.task_repository.get_all(status, category, assignee_id,assigner_id,search, team_id=team_id)
        return tasks
    def get_board(self , current_user = User) -> dict[TaskStatus , list[Task]]:
        if current_user.role == UserRole.SUPERADMIN:#type: ignore
            team_id = None
        else :
            team_id = current_user.team_id
        tasks = self.task_repository.get_all(team_id=team_id)
        board = {status : [] for status in TaskStatus}
        for task in tasks:
            task_status = TaskStatus(task.status)
            board[task_status].append(task)
        return board
    
    def get_task(self,task_id : int, current_user = User) -> Task:
        task = self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFound()
        if current_user.role != UserRole.SUPERADMIN and task.team_id != current_user.team_id:#type: ignore
            raise TaskNotFound()
        return task
    

    def change_status(self, task_id : int, new_status : TaskStatus,current_user = User) -> Task:
        task = self.get_task(task_id,current_user)
        if new_status not in AlLOWED_TRANSITIONS[task.status]: # type: ignore
            raise InvalidStatusTransition()
        return self.task_repository.update_status(task,new_status)
    
    def update_task(self,task_id : int, data : TaskUpdate,current_user = User):
        task = self.get_task(task_id,current_user)
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
    
    def delete_task(self,task_id : int,current_user = User):
        task=self.get_task(task_id,current_user)
        self.task_repository.delete(task)

    def add_comment(
        self,
        task_id : int,
        current_user : User,
        text : str
    ) -> Comment:
        self.get_task(task_id,current_user)# type: ignore
        return self.comment_repository.create(
            text = text,
            task_id=task_id,
            author_id=current_user.id
        )
    def list_comments(self,task_id : int,current_user : User) -> list[Comment]:
        self.get_task(task_id,current_user)# type: ignore
        return list(self.comment_repository.get_by_task(task_id))
    
    def review_task(
        self,
        task_id : int,
        decision ,
        comment : str,
        current_user : User    
    ) -> Task:
        task = self.get_task(task_id,current_user)# type: ignore
        if task.status != TaskStatus.PENDING_REVIEW:# type: ignore
            raise InvalidStatusTransition()
        is_team_manager = current_user.role == UserRole.MANAGER and current_user.team_id == task.team_id
        is_superadmin = current_user.role == UserRole.SUPERADMIN
        if is_team_manager or is_superadmin: # type: ignore
            if decision == ReviewDecision.CHANGES_REQUESTED and comment is None:
                raise CommentRequired()
            if comment is not None:
                self.comment_repository.create(
                text=comment,
                task_id=task_id,
                author_id=current_user.id)           
        else :
            raise NotAllowed()
        self.activity_repository.create(current_user.id, "task.reviewed", f"task {task_id}: {decision.value}")# type: ignore
        return self.task_repository.update_status(task, DECISION_OUTCOMES[decision])

    def add_item(
        self,
        text : str,
        task_id : int,
        current_user : User,
    ) -> ChecklistItem:
        self.get_task(task_id,current_user)# type: ignore
        position = len(self.checklist_repository.get_by_task(task_id=task_id))
        return self.checklist_repository.create(text = text,position=position,task_id=task_id)
    
    def list_items(
        self,
        task_id : int,
        current_user : User
    ) -> list[ChecklistItem]:
        self.get_task(task_id,current_user)# type: ignore
        return list(self.checklist_repository.get_by_task(task_id=task_id))
        
    def toggle_item(
            self,
            item_id : int,
            current_user : User
    )->ChecklistItem:
        item = self.checklist_repository.get_by_id(item_id)# type: ignore
        if item is None:
            raise TaskNotFound
        self.get_task(item.task_id,current_user=current_user)# type: ignore
        return self.checklist_repository.set_done(item,not item.done_flag) # type: ignore
        
    def delete_item(
            self,
            item_id : int,
            current_user : User
    ):
        item = self.checklist_repository.get_by_id(item_id)# type: ignore
        if item is None:
            raise TaskNotFound
        self.get_task(item.task_id,current_user=current_user)# type: ignore
        self.checklist_repository.delete_item(item)


