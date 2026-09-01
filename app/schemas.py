"""Σχήματα εισόδου και εξόδου του API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=200)
    isbn: str | None = Field(default=None, max_length=32)
    total_copies: int = Field(default=1, ge=1)


class BookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    author: str
    isbn: str | None
    total_copies: int
    available_copies: int
    created_at: datetime


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    created_at: datetime


class LoanCreate(BaseModel):
    book_id: UUID
    member_id: UUID


class LoanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    book_id: UUID
    member_id: UUID
    status: str
    borrowed_at: datetime
    returned_at: datetime | None


class HealthOut(BaseModel):
    status: str
