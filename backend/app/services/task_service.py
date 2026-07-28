from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.activity_repository import ActivityRepository
from app.repositories.checklistItem_repository import ChecklistItemRepository

from app.core.exceptions import AssigneeNotFound
from app.db.models import Task, User, Comment, ChecklistItem
from app.domain.enums import TaskStatus, TaskPriority
from datetime import date
from app.core.exceptions import InvalidStatusTransition, TaskNotFound, NotAllowed, CommentRequired
from app.schemas.task import TaskUpdate
from app.domain.enums import UserRole, ReviewDecision, TaskCategory

ALLOWED_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.PENDING_REVIEW},
    TaskStatus.PENDING_REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE},
    TaskStatus.DONE: set(),
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
        user_repository: UserRepository,
        comment_repository: CommentRepository,
        checklist_repository: ChecklistItemRepository,
        activity_repository: ActivityRepository,
    ):
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.comment_repository = comment_repository
        self.checklist_repository = checklist_repository
        self.activity_repository = activity_repository

    def can_assign_to(self, current_user: User, assignee: User) -> bool:
        if current_user.role == UserRole.SUPERADMIN:
            return True
        if assignee.id == current_user.id:
            return True
        if current_user.team_id is None or assignee.team_id != current_user.team_id:
            return False
        if current_user.role == UserRole.MANAGER:
            return True
        return assignee.role == UserRole.USER

    def _resolve_collaborators(self, user_ids, task_team_id, current_user : User) -> list[User]:
        users = []
        for uid in user_ids:
            user = self.user_repository.get_by_id(uid)
            if user is None:
                raise AssigneeNotFound()
            if current_user.role != UserRole.SUPERADMIN and user.team_id != task_team_id:
                raise NotAllowed()
            users.append(user)
        return users
    def _can_access(self, task, current_user: User) -> bool:
        if current_user.role == UserRole.SUPERADMIN:
            return True
        if current_user.role == UserRole.MANAGER and current_user.team_id == task.team_id:
            return True
        if task.assignee_id == current_user.id:
            return True
        return any(c.id == current_user.id for c in task.collaborators)

    def _can_modify(self, task, current_user: User) -> bool:
        if current_user.role == UserRole.SUPERADMIN:
            return True
        if current_user.role == UserRole.MANAGER and current_user.team_id == task.team_id:
            return True
        return task.assignee_id == current_user.id
    def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority,
        category: TaskCategory,
        due_date: date | None,
        assignee_id: int | None,
        current_user: User,
        collaborator_ids: list[int] | None = None,
    ) -> Task:
        if assignee_id is None:
            assignee_id = current_user.id

        assignee = self.user_repository.get_by_id(assignee_id)
        if assignee is None:
            raise AssigneeNotFound()
        if not self.can_assign_to(current_user, assignee):
            raise NotAllowed()

        task = self.task_repository.create(
            title,
            description,
            priority,
            category,
            due_date,
            assignee_id=assignee_id,
            assigner_id=current_user.id,
            team_id=current_user.team_id,
        )

        if collaborator_ids:
            task.collaborators = self._resolve_collaborators(
                collaborator_ids, task.team_id, current_user
            )
            task = self.task_repository.update(task)

        self.activity_repository.create(
            current_user.id, "task.created", f"task {task.id}: {task.title}"
        )
        return task

    def set_collaborators(self, task_id: int, user_ids: list[int], current_user: User) -> Task:
        task = self.get_task(task_id, current_user)

        is_superadmin = current_user.role == UserRole.SUPERADMIN
        is_team_manager = (
            current_user.role == UserRole.MANAGER
            and current_user.team_id == task.team_id
        )
        is_assigner = task.assigner_id == current_user.id
        if not (is_superadmin or is_team_manager or is_assigner):
            raise NotAllowed()

        task.collaborators = self._resolve_collaborators(user_ids, task.team_id, current_user)
        return self.task_repository.update(task)

    def list_tasks(self, status, category, assignee_id, assigner_id, search, current_user: User):
        if current_user.role == UserRole.SUPERADMIN:
            team_id = None
        elif current_user.team_id is None:
            team_id = None
            assignee_id = current_user.id
        else:
            team_id = current_user.team_id

        tasks = self.task_repository.get_all(
            status, category, assignee_id, assigner_id, search, team_id=team_id
        )
        if current_user.role != UserRole.SUPERADMIN:
            tasks = self._add_collaborating(tasks, current_user)
        return tasks

    def get_board(self, current_user: User) -> dict[TaskStatus, list[Task]]:
        assignee_id = None
        if current_user.role == UserRole.SUPERADMIN:
            team_id = None
        elif current_user.team_id is None:
            team_id = None
            assignee_id = current_user.id
        else:
            team_id = current_user.team_id
        tasks = self.task_repository.get_all(team_id=team_id, assignee_id=assignee_id)
        if current_user.role != UserRole.SUPERADMIN:
            tasks = self._add_collaborating(tasks, current_user)
        board = {status: [] for status in TaskStatus}
        for task in tasks:
            board[task.status].append(task)
        return board

    def get_task(self, task_id: int, current_user: User) -> Task:
        task = self.task_repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFound()

        if not self._can_access(task, current_user):
            raise TaskNotFound()

        return task

    def change_status(self, task_id: int, new_status: TaskStatus, current_user: User) -> Task:
        task = self.get_task(task_id, current_user)

        if not self._can_modify(task, current_user):
            raise NotAllowed()

        if new_status not in ALLOWED_TRANSITIONS[task.status]:
            raise InvalidStatusTransition()

        if task.status == TaskStatus.PENDING_REVIEW:
            is_team_manager = (
                current_user.role == UserRole.MANAGER
                and current_user.team_id == task.team_id
            )
            is_superadmin = current_user.role == UserRole.SUPERADMIN
            if not (is_team_manager or is_superadmin):
                raise NotAllowed()
        updated = self.task_repository.update_status(task, new_status)
        self.activity_repository.create(
        current_user.id, "task.status_changed",
        f"task {task_id}: → {new_status.value}"
        )
        return updated

    def update_task(self, task_id: int, data: TaskUpdate, current_user: User):
        task = self.get_task(task_id, current_user)
        if not self._can_modify(task, current_user):
            raise NotAllowed()
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.priority is not None:
            task.priority = data.priority
        if data.category is not None:
            task.category = data.category
        if data.due_date is not None:
            task.due_date = data.due_date
        if data.assignee_id is not None:
            if self.user_repository.get_by_id(data.assignee_id) is None:
                raise AssigneeNotFound()
            task.assignee_id = data.assignee_id
        return self.task_repository.update(task)
    
    # def _can_modify(self, task_id : int, current_user : User) -> bool:
    #     task = self.get_task(task_id, current_user)
    #     if current_user.role == UserRole.SUPERADMIN:
    #         return True
    #     if current_user.role == UserRole.MANAGER and current_user.team_id == task.team_id:
    #         return True
    #     return task.assignee_id == current_user.id
    
    def delete_task(self, task_id: int, current_user: User) -> None:
        task = self.get_task(task_id, current_user)

        is_superadmin = current_user.role == UserRole.SUPERADMIN
        is_team_manager = (
            current_user.role == UserRole.MANAGER
            and current_user.team_id == task.team_id
        )
        is_owner = task.assignee_id == current_user.id
        if not (is_superadmin or is_team_manager or is_owner):
            raise NotAllowed()
        self.activity_repository.create(
            current_user.id, 
            "task.deleted", 
            f"task {task.id}: {task.title}"
        )
        self.task_repository.delete(task)

    def add_comment(self, task_id: int, current_user: User, text: str) -> Comment:
        self.get_task(task_id, current_user)
        return self.comment_repository.create(
            text=text, task_id=task_id, author_id=current_user.id
        )

    def list_comments(self, task_id: int, current_user: User) -> list[Comment]:
        self.get_task(task_id, current_user)
        return list(self.comment_repository.get_by_task(task_id))

    def review_task(self, task_id: int, decision, comment: str, current_user: User) -> Task:
        task = self.get_task(task_id, current_user)
        if task.status != TaskStatus.PENDING_REVIEW:
            raise InvalidStatusTransition()

        is_team_manager = (
            current_user.role == UserRole.MANAGER
            and current_user.team_id == task.team_id
        )
        is_superadmin = current_user.role == UserRole.SUPERADMIN
        if not (is_team_manager or is_superadmin):
            raise NotAllowed()
        
        if decision in (ReviewDecision.CHANGES_REQUESTED, ReviewDecision.DECLINED) and not comment:
            raise CommentRequired()
        if comment:
            self.comment_repository.create(
                text=comment, task_id=task_id, author_id=current_user.id
            )

        self.activity_repository.create(
            current_user.id, "task.reviewed", f"task {task_id}: {decision.value}"
        )
        return self.task_repository.update_status(task, DECISION_OUTCOMES[decision])

    def add_item(self, text: str, task_id: int, current_user: User) -> ChecklistItem:
        self.get_task(task_id, current_user)
        position = len(self.checklist_repository.get_by_task(task_id=task_id))
        return self.checklist_repository.create(text=text, position=position, task_id=task_id)

    def list_items(self, task_id: int, current_user: User) -> list[ChecklistItem]:
        self.get_task(task_id, current_user)
        return list(self.checklist_repository.get_by_task(task_id=task_id))

    def toggle_item(self, item_id: int, current_user: User) -> ChecklistItem:
        item = self.checklist_repository.get_by_id(item_id)
        if item is None:
            raise TaskNotFound()
        self.get_task(item.task_id, current_user=current_user)
        return self.checklist_repository.set_done(item, not item.done_flag)

    def delete_item(self, item_id: int, current_user: User):
        item = self.checklist_repository.get_by_id(item_id)
        if item is None:
            raise TaskNotFound()
        self.get_task(item.task_id, current_user=current_user)
        self.checklist_repository.delete_item(item)
    def _add_collaborating(self, tasks, current_user):
        tasks = list(tasks)
        seen = {t.id for t in tasks}
        for task in self.task_repository.get_collaborating(current_user.id):
            if task.id not in seen:
                tasks.append(task)
                seen.add(task.id)
        return tasks