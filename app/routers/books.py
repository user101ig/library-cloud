"""REST endpoints για τα βιβλία."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_session
from app.models import Book
from app.schemas import BookCreate, BookOut
from app.services import books as book_service


router = APIRouter(prefix="/books", tags=["books"])


@router.post("", response_model=BookOut, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> Book:
    return book_service.create_book(session, payload)


@router.get("", response_model=list[BookOut])
def list_books(
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian", "reader")),
) -> list[Book]:
    return book_service.list_books(session)


@router.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: str,
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian", "reader")),
) -> Book:
    return book_service.get_book(session, book_id)
