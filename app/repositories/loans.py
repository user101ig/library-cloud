"""Ερωτήματα βάσης για τους δανεισμούς."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Loan


def list_loans(session: Session) -> list[Loan]:
    return list(session.scalars(select(Loan).order_by(Loan.borrowed_at.desc(), Loan.id.desc())))


def get_loan(session: Session, loan_id: str) -> Loan | None:
    return session.get(Loan, loan_id)
