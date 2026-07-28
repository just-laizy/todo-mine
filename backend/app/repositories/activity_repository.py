from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.models import Activity

class ActivityRepository:
    def __init__(self, session:Session):
        self.session = session
    
    def create(
        self,
        user_id : int,
        action : str,
        details : str
    )->Activity:
        activity = Activity(user_id = user_id, action = action, details = details)
        self.session.add(activity)
        self.session.commit()
        self.session.refresh(activity)
        return activity
    
    def get_all(
            self,
            limit : int = 50
    ) -> list[Activity]:
        statement = (select(Activity).order_by(Activity.id.desc()).limit(limit))
        return list(self.session.execute(statement).scalars().all())
    