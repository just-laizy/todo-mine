from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Task
from app.db.models import ChecklistItem,Comment

class ChecklistItemRepository :
    def __init__(self , session : Session):
        self.session = session

    def create(self,
        text,
        position,
        task_id
    ):
        checklist = ChecklistItem(
            text = text,
            position = position,
            task_id = task_id,
        )
        self.session.add(checklist)
        self.session.commit()
        self.session.refresh(checklist)
        return checklist
        
    def get_by_task(self, task_id) -> list[ChecklistItem]:
        statement = select(ChecklistItem).where(ChecklistItem.task_id == task_id)
        return list(self.session.execute(statement).scalars().all())
    def get_by_id(self,item_id)->ChecklistItem | None:
        return self.session.get(ChecklistItem,item_id)
    def set_done(self,item : ChecklistItem, value : bool) -> ChecklistItem:
        item.done_flag = value # type: ignore
        self.session.commit()
        self.session.refresh(item)
        return item
    def delete_item(self,item : ChecklistItem) -> None:
        self.session.delete(item)
        self.session.commit()
