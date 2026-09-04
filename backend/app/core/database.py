from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.models import Base
from app.core.logging import get_logger

logger = get_logger("database")

# Create engine (SQLite compatible or Postgres)
connect_args = {"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}

engine = create_engine(
    settings.SYNC_DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
