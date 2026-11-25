"""Database engine configuration, explicitly supplied by the deployment boundary."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(url: str) -> Engine:
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError("PostgreSQL with Psycopg 3 is required")
    return create_engine(url, pool_pre_ping=True)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
