"""REST endpoints για τους δανεισμούς."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_session
from app.models import Loan
from app.schemas import LoanCreate, LoanOut
from app.services import loans as loan_service


router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("", response_model=LoanOut, status_code=status.HTTP_201_CREATED)
def borrow_book(
    payload: LoanCreate,
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> Loan:
    return loan_service.borrow_book(session, payload)


@router.post("/{loan_id}/return", response_model=LoanOut)
def return_book(
    loan_id: str,
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> Loan:
    return loan_service.return_book(session, loan_id)


@router.get("", response_model=list[LoanOut])
def list_loans(
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> list[Loan]:
    return loan_service.list_loans(session)
