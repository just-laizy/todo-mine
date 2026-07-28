from sqlalchemy import text

from app.db.session import engine

STEPS = [
    "ALTER TABLE users MODIFY status VARCHAR(20) NULL",
    "UPDATE users SET status = 'ACTIVE' WHERE status IS NULL OR status NOT IN ('ACTIVE', 'INACTIVE')",
    "ALTER TABLE users MODIFY status ENUM('ACTIVE','INACTIVE') NOT NULL DEFAULT 'ACTIVE'",
    
    "UPDATE users SET role = 'USER' WHERE role IS NULL",
    "ALTER TABLE users MODIFY role ENUM('SUPERADMIN','MANAGER','USER') NOT NULL DEFAULT 'USER'",
]


def migrate():
    if engine.dialect.name != "mysql":
        raise SystemExit(f"This migration is written for MySQL, not {engine.dialect.name}.")

    with engine.begin() as connection:
        for statement in STEPS:
            print(statement)
            connection.execute(text(statement))

        rows = connection.execute(text("SELECT status, COUNT(*) FROM users GROUP BY status")).all()

    print("\nDone. users.status now holds:")
    for status, count in rows:
        print(f"  {status}: {count}")


if __name__ == "__main__":
    migrate()
