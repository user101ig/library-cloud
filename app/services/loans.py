"""Κανόνες δανεισμού και επιστροφής."""

from __future__ import annotations

from datetime import datetime

from app.errors import ConflictError, NotFoundError
from app.models import Loan
from app.messaging import publish_event
from app.repositories import books as book_repository
from app.repositories import loans as loan_repository
from app.repositories import members as member_repository
from app.schemas import LoanCreate
from sqlalchemy.orm import Session


class LoanNotFoundError(NotFoundError):
    detail = "Loan not found"


class BookNotFoundError(NotFoundError):
    detail = "Book not found"


class MemberNotFoundError(NotFoundError):
    detail = "Member not found"


class NoAvailableCopiesError(ConflictError):
    detail = "No available copies"


class LoanAlreadyReturnedError(ConflictError):
    detail = "Loan already returned"


def list_loans(session: Session) -> list[Loan]:
    return loan_repository.list_loans(session)


def borrow_book(session: Session, payload: LoanCreate) -> Loan:
    book_id = str(payload.book_id)
    member_id = str(payload.member_id)

    book = book_repository.get_book(session, book_id)
    if book is None:
        raise BookNotFoundError()

    member = member_repository.get_member(session, member_id)
    if member is None:
        raise MemberNotFoundError()

    if book.available_copies <= 0:
        raise NoAvailableCopiesError()

    book.available_copies -= 1
    loan = Loan(book_id=book_id, member_id=member_id, status="borrowed")
    session.add(loan)
    session.commit()
    session.refresh(loan)

    # Στέλνουμε ονόματα για το PDF, όχι εσωτερικά UUIDs.
    publish_event(
        "loan.borrowed",
        {
            "book_title": book.title,
            "book_author": book.author,
            "member_name": member.full_name,
        },
    )

    return loan


def return_book(session: Session, loan_id: str) -> Loan:
    loan = loan_repository.get_loan(session, loan_id)
    if loan is None:
        raise LoanNotFoundError()

    if loan.status == "returned":
        raise LoanAlreadyReturnedError()

    book = book_repository.get_book(session, loan.book_id)
    if book is None:
        raise BookNotFoundError()

    loan.status = "returned"
    loan.returned_at = datetime.utcnow()
    book.available_copies += 1
    session.commit()
    session.refresh(loan)

    publish_event(
        "loan.returned",
        {
            "book_title": book.title,
            "book_author": book.author,
            "member_name": loan.member.full_name,
        },
    )

    return loan
