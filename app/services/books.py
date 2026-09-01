"""Λειτουργίες διαχείρισης βιβλίων."""

from __future__ import annotations

from app.errors import NotFoundError
from app.models import Book
from app.repositories import books as book_repository
from app.schemas import BookCreate
from sqlalchemy.orm import Session


class BookNotFoundError(NotFoundError):
    detail = "Book not found"


def create_book(session: Session, payload: BookCreate) -> Book:
    return book_repository.create_book(session, payload)


def list_books(session: Session) -> list[Book]:
    return book_repository.list_books(session)


def get_book(session: Session, book_id: str) -> Book:
    book = book_repository.get_book(session, book_id)
    if book is None:
        raise BookNotFoundError()
    return book
