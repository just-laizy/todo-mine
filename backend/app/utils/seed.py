from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.core.security import hash_password
from app.domain.enums import UserRole


def seed():
    session = SessionLocal()
    try:
        repository = UserRepository(session)
        existing = repository.get_by_email('admin@todo.com')
        if existing is not None:
            print("Superadmin already exists - nothing to do")
            return
        user = repository.create('Admin', 'admin@todo.com', hash_password('admin12345'))
        user.role = UserRole.SUPERADMIN # type: ignore
        session.commit()
        print(f"Superadmin created with id {user.id}")
    finally:
        session.close()


if __name__ == "__main__":
    seed()