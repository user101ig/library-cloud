"""Λειτουργίες διαχείρισης μελών."""

from __future__ import annotations

from app.errors import NotFoundError
from app.models import Member
from app.repositories import members as member_repository
from app.schemas import MemberCreate
from sqlalchemy.orm import Session


class MemberNotFoundError(NotFoundError):
    detail = "Member not found"


def create_member(session: Session, payload: MemberCreate) -> Member:
    return member_repository.create_member(session, payload)


def list_members(session: Session) -> list[Member]:
    return member_repository.list_members(session)


def get_member(session: Session, member_id: str) -> Member:
    member = member_repository.get_member(session, member_id)
    if member is None:
        raise MemberNotFoundError()
    return member
