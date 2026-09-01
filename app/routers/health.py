"""Απλός έλεγχος λειτουργίας του API."""

from fastapi import APIRouter

from app.schemas import HealthOut


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok")
