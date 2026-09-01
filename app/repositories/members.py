"""Ερωτήματα βάσης για τα μέλη."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ConflictError
from app.models import Member
from app.schemas import MemberCreate


class DuplicateMemberError(ConflictError):
    detail = "Member email already exists"


def create_member(session: Session, payload: MemberCreate) -> Member:
    member = Member(full_name=payload.full_name, email=str(payload.email))
    session.add(member)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateMemberError() from exc

    session.refresh(member)
    return member


def list_members(session: Session) -> list[Member]:
    return list(session.scalars(select(Member).order_by(Member.created_at.desc(), Member.id.desc())))


def get_member(session: Session, member_id: str) -> Member | None:
    return session.get(Member, member_id)
