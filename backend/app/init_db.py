import sys
import os
from sqlalchemy import text

# Add parent directory to path so app can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.security import get_password_hash
# Import models to register them on Base
from app.models.commerce import Commerce
from app.models.user import User, UserRole
from app.models.feedback import Feedback


def run_sqlite_migrations():
    """
    Apply minimal additive migrations for long-lived SQLite deployments.
    """
    with engine.begin() as connection:
        if connection.dialect.name != "sqlite":
            return

        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(feedbacks)")).fetchall()
        }

        if "customer_email" not in columns:
            print("Agregando columna faltante 'customer_email' a feedbacks...")
            connection.execute(
                text("ALTER TABLE feedbacks ADD COLUMN customer_email VARCHAR")
            )


def init_db():
    print("Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    run_sqlite_migrations()

    db = SessionLocal()
    try:
        # Check if super admin already exists
        admin_username = settings.SUPER_ADMIN_USERNAME
        admin_user = db.query(User).filter(User.username == admin_username).first()

        if not admin_user:
            print(f"Creando usuario Super Admin por defecto: '{admin_username}'...")
            hashed_password = get_password_hash(settings.SUPER_ADMIN_PASSWORD)
            new_admin = User(
                username=admin_username,
                password_hash=hashed_password,
                role=UserRole.SUPER_ADMIN,
                commerce_id=None
            )
            db.add(new_admin)
            db.commit()
            print("Usuario Super Admin creado exitosamente.")
        else:
            print(f"El usuario Super Admin '{admin_username}' ya existe.")

        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
