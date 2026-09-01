"""Μοντέλα της βάσης δεδομένων."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def new_uuid() -> str:
    return str(uuid4())


class Book(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)
    isbn: Mapped[str | None] = mapped_column(String(32), unique=True)
    total_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    available_copies: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    loans: Mapped[list["Loan"]] = relationship(back_populates="book")

    __table_args__ = (
        CheckConstraint("total_copies >= 0", name="books_total_copies_non_negative"),
        CheckConstraint("available_copies >= 0", name="books_available_copies_non_negative"),
    )


class Member(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    loans: Mapped[list["Loan"]] = relationship(back_populates="member")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    book_id: Mapped[str] = mapped_column(String(36), ForeignKey("books.id"), nullable=False)
    member_id: Mapped[str] = mapped_column(String(36), ForeignKey("members.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime)

    book: Mapped[Book] = relationship(back_populates="loans")
    member: Mapped[Member] = relationship(back_populates="loans")

    __table_args__ = (CheckConstraint("status IN ('borrowed', 'returned')", name="loans_valid_status"),)
