"""SQLite connection and session lifecycle."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = f"sqlite:///{Path(__file__).parent.parent / 'star_wars.db'}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database() -> None:
    # Import models here so all mapped tables are registered before creation.
    from galaxy import models  # noqa: F401

    Base.metadata.create_all(engine)
