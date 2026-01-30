from __future__ import annotations

from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class AuthRequestIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class ConsentRecordIn(BaseModel):
    doc_type: Literal["terms", "privacy"]
    doc_version: str = Field(min_length=1, max_length=64)
    accepted_at: str = Field(min_length=10, max_length=64)  # ISO string
    source: Literal["ui", "api"] = "ui"
    evidence_hash: Optional[str] = Field(default=None, max_length=256)


class AuthVerifyIn(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    challenge_id: str = Field(min_length=8, max_length=80)
    otp: str = Field(min_length=4, max_length=12)
    consents: List[ConsentRecordIn]


class AuthRequestOut(BaseModel):
    ok: bool = True
    challenge_id: str
    message: str
    # nur dev
    dev_otp: Optional[str] = None


class AuthVerifyOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str


class MeOut(BaseModel):
    user_id: str
    role: str


class LogoutOut(BaseModel):
    ok: bool = True
