"""Ερωτήματα βάσης για τα βιβλία."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError
from app.models import Book
from app.schemas import BookCreate


class DuplicateBookError(ConflictError):
    detail = "Book ISBN already exists"


def create_book(session: Session, payload: BookCreate) -> Book:
    book = Book(
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        total_copies=payload.total_copies,
        available_copies=payload.total_copies,
    )
    session.add(book)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateBookError() from exc

    session.refresh(book)
    return book


def list_books(session: Session) -> list[Book]:
    return list(session.scalars(select(Book).order_by(Book.created_at.desc(), Book.id.desc())))


def get_book(session: Session, book_id: str) -> Book | None:
    return session.get(Book, book_id)
