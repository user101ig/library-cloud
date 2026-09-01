"""Σύνδεση και αρχικοποίηση της SQLite."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/library.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session


def init_db() -> None:
    # Δημιουργεί μόνο τους πίνακες που λείπουν.
    from app import models

    Base.metadata.create_all(bind=engine)
