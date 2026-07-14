from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Comment,Task

class CommentRepository : 
    def __init__(self , session : Session):
        self.session = session

    def create(self,text,author_id,task_id):
        comment = Comment(
            text = text,
            task_id = task_id,
            author_id = author_id
            )
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment
    def get_by_task(self, task_id) -> list[Comment]:
        comment = select(Comment).where(Comment.task_id == task_id)
        return list(self.session.execute(comment).scalars().all())

