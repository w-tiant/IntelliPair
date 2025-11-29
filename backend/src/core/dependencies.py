
from sqlalchemy.orm import Session
from typing import Generator
from .lifespan import app_data
from ..database.database import SessionLocal

def get_app_data() -> dict:
    """
    Dependency to get the global application data dictionary.
    """
    return app_data

def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()