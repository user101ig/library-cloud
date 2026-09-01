"""HTMX routes για το απλό web περιβάλλον."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import auth
from app.auth import AuthUser, require_roles
from app.database import get_session
from app.errors import AppError
from app.repositories import books as book_repository
from app.repositories import loans as loan_repository
from app.repositories import members as member_repository
from app.schemas import BookCreate, LoanCreate, MemberCreate
from app.services import books as book_service
from app.services import loans as loan_service
from app.services import members as member_service

router = APIRouter(tags=["frontend"])
templates = Jinja2Templates(directory="app/templates")


def error_message(exc: Exception) -> str:
    if isinstance(exc, AppError):
        return exc.detail
    if isinstance(exc, ValidationError):
        return exc.errors()[0]["msg"]
    return "The submitted data is invalid"


def books_response(request: Request, session: Session, user: AuthUser, message: str | None = None):
    return templates.TemplateResponse(request=request, name="partials/books.html", context={
        "books": book_repository.list_books(session), "user": user, "message": message,
    })


def members_response(request: Request, session: Session, message: str | None = None):
    return templates.TemplateResponse(request=request, name="partials/members.html", context={
        "members": member_repository.list_members(session), "message": message,
    })


def loans_response(request: Request, session: Session, message: str | None = None):
    return templates.TemplateResponse(request=request, name="partials/loans.html", context={
        "loans": loan_repository.list_loans(session),
        "books": book_repository.list_books(session),
        "members": member_repository.list_members(session),
        "message": message,
    })


@router.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={
        "user_session": auth.get_optional_session(request),
    })


@router.get("/ui/books", include_in_schema=False)
def books_partial(request: Request, session: Session = Depends(get_session), user: AuthUser = Depends(require_roles("admin", "librarian", "reader"))):
    return books_response(request, session, user)


@router.post("/ui/books", include_in_schema=False)
def create_book(request: Request, title: str = Form(), author: str = Form(), isbn: str = Form(default=""), total_copies: int = Form(default=1), session: Session = Depends(get_session), user: AuthUser = Depends(require_roles("admin", "librarian"))):
    try:
        book_service.create_book(session, BookCreate(title=title, author=author, isbn=isbn or None, total_copies=total_copies))
        message = "Book added successfully"
    except (AppError, ValidationError) as exc:
        message = error_message(exc)
    return books_response(request, session, user, message)


@router.get("/ui/members", include_in_schema=False)
def members_partial(request: Request, session: Session = Depends(get_session), _user: AuthUser = Depends(require_roles("admin", "librarian"))):
    return members_response(request, session)


@router.post("/ui/members", include_in_schema=False)
def create_member(request: Request, full_name: str = Form(), email: str = Form(), session: Session = Depends(get_session), _user: AuthUser = Depends(require_roles("admin", "librarian"))):
    try:
        member_service.create_member(session, MemberCreate(full_name=full_name, email=email))
        message = "Member added successfully"
    except (AppError, ValidationError) as exc:
        message = error_message(exc)
    return members_response(request, session, message)


@router.get("/ui/loans", include_in_schema=False)
def loans_partial(request: Request, session: Session = Depends(get_session), _user: AuthUser = Depends(require_roles("admin", "librarian"))):
    return loans_response(request, session)


@router.post("/ui/loans", include_in_schema=False)
def create_loan(request: Request, book_id: str = Form(), member_id: str = Form(), session: Session = Depends(get_session), _user: AuthUser = Depends(require_roles("admin", "librarian"))):
    try:
        loan_service.borrow_book(session, LoanCreate(book_id=UUID(book_id), member_id=UUID(member_id)))
        message = "Book borrowed successfully"
    except (AppError, ValidationError, ValueError) as exc:
        message = error_message(exc)
    return loans_response(request, session, message)


@router.post("/ui/loans/{loan_id}/return", include_in_schema=False)
def return_loan(loan_id: str, request: Request, session: Session = Depends(get_session), _user: AuthUser = Depends(require_roles("admin", "librarian"))):
    try:
        loan_service.return_book(session, loan_id)
        message = "Book returned successfully"
    except AppError as exc:
        message = error_message(exc)
    return loans_response(request, session, message)
