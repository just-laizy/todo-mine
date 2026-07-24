"""Seed the database with a realistic office: 1 superadmin, 3 teams,
3 managers, 15 users, 45 tasks spread across statuses and due dates."""

from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db import models  # noqa: F401 - registers all models
from app.db.models.user import User
from app.db.models.team import Team
from app.db.models.task import Task
from app.core.security import hash_password
from app.domain.enums import UserRole, TaskStatus, TaskPriority, TaskCategory

ADMIN_EMAIL = "admin@ojak.com"
ADMIN_PASSWORD = "admin1234"
MANAGER_PASSWORD = "manager1234"
USER_PASSWORD = "12345678"

TEAMS = [
    {"name": "Platform Team", "manager": "Aman Nuryyev"},
    {"name": "Product Team",  "manager": "Maya Charyyeva"},
    {"name": "Mobile Team",   "manager": "Serdar Amanov"},
]

USER_NAMES = [
    ["Batyr K.", "Jemal A.", "Merdan S.", "Oguljan T.", "Rustem D."],
    ["Gulnar M.", "Kerim B.", "Leyla H.", "Nury G.", "Selbi R."],
    ["Arslan P.", "Bahar Y.", "Dovlet N.", "Enejan V.", "Guych O."],
]

# title, category, priority — cycled across users
TASK_TEMPLATES = [
    ("Redesign settings screen",        TaskCategory.UI_UX,    TaskPriority.MEDIUM),
    ("Fix login form validation",       TaskCategory.FRONTEND, TaskPriority.ADVANCED),
    ("Optimise task list query",        TaskCategory.BACKEND,  TaskPriority.MEDIUM),
    ("Push notifications on Android",   TaskCategory.MOBILE,   TaskPriority.ADVANCED),
    ("Set up staging pipeline",         TaskCategory.DEVOPS,   TaskPriority.URGENT),
    ("Dark mode colour tokens",         TaskCategory.UI_UX,    TaskPriority.LOW),
    ("Board drag-and-drop polish",      TaskCategory.FRONTEND, TaskPriority.MEDIUM),
    ("Add Redis cache to stats",        TaskCategory.BACKEND,  TaskPriority.ADVANCED),
    ("Offline mode for mobile app",     TaskCategory.MOBILE,   TaskPriority.URGENT),
    ("Nightly database backups",        TaskCategory.DEVOPS,   TaskPriority.URGENT),
    ("Empty-state illustrations",       TaskCategory.UI_UX,    TaskPriority.LOW),
    ("Client-side form errors",         TaskCategory.FRONTEND, TaskPriority.LOW),
    ("Audit log pagination",            TaskCategory.BACKEND,  TaskPriority.MEDIUM),
    ("Crash reporting SDK",             TaskCategory.MOBILE,   TaskPriority.MEDIUM),
    ("Docker image size reduction",     TaskCategory.DEVOPS,   TaskPriority.LOW),
]

# status, due-date offset in days (None = no due date)
TASK_SHAPES = [
    (TaskStatus.TODO,           3),
    (TaskStatus.IN_PROGRESS,    -2),    # overdue on purpose
    (TaskStatus.DONE,           -6),
    (TaskStatus.TODO,           0),     # due today
    (TaskStatus.PENDING_REVIEW, 5),
    (TaskStatus.IN_PROGRESS,    12),
    (TaskStatus.TODO,           None),  # no due date
    (TaskStatus.DONE,           -10),
    (TaskStatus.PENDING_REVIEW, -1),    # overdue and waiting on review
]


def now():
    return datetime.now(timezone.utc)


def seed():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        if session.query(User).filter(User.email == ADMIN_EMAIL).first():
            print("Database already seeded — nothing to do.")
            print(f"Sign in as {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
            return

        # ---------- superadmin ----------
        admin = User(
            name="Site Admin",
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.SUPERADMIN,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        print(f"superadmin  {ADMIN_EMAIL} / {ADMIN_PASSWORD}")

        template_index = 0
        shape_index = 0

        for team_number, team_info in enumerate(TEAMS, start=1):
            
            manager_email = f"manager{team_number}@ojak.com"
            manager = User(
                name=team_info["manager"],
                email=manager_email,
                hashed_password=hash_password(MANAGER_PASSWORD),
                role=UserRole.MANAGER,
            )
            session.add(manager)
            session.commit()
            session.refresh(manager)

            team = Team(name=team_info["name"], manager_id=manager.id)
            session.add(team)
            session.commit()
            session.refresh(team)

            manager.team_id = team.id
            session.commit()
            print(f"manager     {manager_email} / {MANAGER_PASSWORD}  → {team.name}")

            # ---------- members ----------
            for member_number in range(1, 6):
                member_email = f"team{team_number}user{member_number}@ojak.com"
                member = User(
                    name=USER_NAMES[team_number - 1][member_number - 1],
                    email=member_email,
                    hashed_password=hash_password(USER_PASSWORD),
                    role=UserRole.USER,
                    team_id=team.id,
                )
                session.add(member)
                session.commit()
                session.refresh(member)

                # ---------- 3 tasks per member ----------
                for _ in range(3):
                    title, category, priority = TASK_TEMPLATES[template_index % len(TASK_TEMPLATES)]
                    status, due_offset = TASK_SHAPES[shape_index % len(TASK_SHAPES)]
                    template_index += 1
                    shape_index += 1

                    due_date = None
                    if due_offset is not None:
                        due_date = (now() + timedelta(days=due_offset)).date()

                    task = Task(
                        title=title,
                        description=f"{title}. Follow up with the assignee if blocked.",
                        status=status,
                        priority=priority,
                        category=category,
                        due_date=due_date,
                        assignee_id=member.id,
                        assigner_id=manager.id,
                        team_id=team.id,
                        created_at=now() - timedelta(days=14),
                        done_at=now() - timedelta(days=2) if status == TaskStatus.DONE else None,
                    )
                    session.add(task)

                session.commit()
                print(f"  user      {member_email} / {USER_PASSWORD}")

        total_users = session.query(User).count()
        total_tasks = session.query(Task).count()
        print(f"\nDone: {total_users} users, 3 teams, {total_tasks} tasks.")

    finally:
        session.close()


if __name__ == "__main__":
    seed()