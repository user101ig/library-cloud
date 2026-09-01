"""REST endpoints για τα μέλη."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.database import get_session
from app.models import Member
from app.schemas import MemberCreate, MemberOut
from app.services import members as member_service


router = APIRouter(prefix="/members", tags=["members"])


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(
    payload: MemberCreate,
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> Member:
    return member_service.create_member(session, payload)


@router.get("", response_model=list[MemberOut])
def list_members(
    session: Session = Depends(get_session),
    _current_user=Depends(require_roles("admin", "librarian")),
) -> list[Member]:
    return member_service.list_members(session)
