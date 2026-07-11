from sqlalchemy.orm import Session
from app.db.models import Team

class TeamRepository:
    def __init__(self, session:Session):
        self.session = session
    
    def create(
        self,
        name : str,
        manager_id
    )->Team:
        team = Team(name = name, manager_id = manager_id)
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)
        return team
        
    def get_by_id(self,team_id : int) -> Team | None :
        team = self.session.get(Team, team_id)
        return team 
        