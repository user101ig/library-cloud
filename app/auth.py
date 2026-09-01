"""Σύνδεση με Keycloak και διαχείριση session."""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient

# Δημόσιο URL για τον browser, εσωτερικό για τα containers.
KEYCLOAK_PUBLIC_URL = os.getenv(
    "KEYCLOAK_PUBLIC_URL",
    os.getenv("KEYCLOAK_URL", "http://localhost:8080"),
)
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", KEYCLOAK_PUBLIC_URL)
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "library")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "library-api")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "library-api-dev-secret")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000/")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

ISSUER = f"{KEYCLOAK_PUBLIC_URL}/realms/{KEYCLOAK_REALM}"
INTERNAL_ISSUER = f"{KEYCLOAK_INTERNAL_URL}/realms/{KEYCLOAK_REALM}"
AUTHORIZE_URL = f"{ISSUER}/protocol/openid-connect/auth"
TOKEN_URL = f"{INTERNAL_ISSUER}/protocol/openid-connect/token"
LOGOUT_URL = f"{INTERNAL_ISSUER}/protocol/openid-connect/logout"
JWKS_URL = f"{INTERNAL_ISSUER}/protocol/openid-connect/certs"
SESSION_COOKIE = "library_session"
LOGIN_COOKIE = "library_login"
jwks_client = PyJWKClient(JWKS_URL)


@dataclass(frozen=True)
class AuthUser:
    subject: str
    username: str
    email: str | None
    roles: set[str]


@dataclass
class LoginAttempt:
    state: str
    code_verifier: str
    expires_at: float


@dataclass
class UserSession:
    user: AuthUser
    access_token: str
    refresh_token: str | None
    csrf_token: str
    expires_at: float


# Προσωρινά sessions στη μνήμη για το τοπικό demo.
login_attempts: dict[str, LoginAttempt] = {}
user_sessions: dict[str, UserSession] = {}


def validate_access_token(token: str) -> AuthUser:
    # Έλεγχος υπογραφής και εκδότη του token.
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            options={"verify_aud": False, "require": ["exp", "iat", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

    if claims.get("azp") != KEYCLOAK_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Token was not issued for this API client")

    return AuthUser(
        subject=claims["sub"],
        username=claims.get("preferred_username", claims["sub"]),
        email=claims.get("email"),
        roles=set(claims.get("realm_access", {}).get("roles", [])),
    )


def create_login_attempt() -> tuple[str, LoginAttempt, str]:
    # PKCE challenge για ασφαλές authorization code flow.
    login_id = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    attempt = LoginAttempt(
        state=secrets.token_urlsafe(32),
        code_verifier=verifier,
        expires_at=time.time() + 300,
    )
    login_attempts[login_id] = attempt
    return login_id, attempt, challenge


def authorization_url(redirect_uri: str, attempt: LoginAttempt, challenge: str) -> str:
    query = urlencode(
        {
            "client_id": KEYCLOAK_CLIENT_ID,
            "response_type": "code",
            "scope": "openid profile email",
            "redirect_uri": redirect_uri,
            "state": attempt.state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


async def exchange_code(code: str, redirect_uri: str, verifier: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": KEYCLOAK_CLIENT_ID,
                "client_secret": KEYCLOAK_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        )
    if response.is_error:
        raise HTTPException(status_code=401, detail="Keycloak rejected the authorization code")
    return response.json()


def create_user_session(token: dict) -> tuple[str, UserSession]:
    session_id = secrets.token_urlsafe(48)
    session = UserSession(
        user=validate_access_token(token["access_token"]),
        access_token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        csrf_token=secrets.token_urlsafe(32),
        expires_at=time.time() + token.get("refresh_expires_in", token.get("expires_in", 300)),
    )
    user_sessions[session_id] = session
    return session_id, session


def get_current_session(request: Request) -> UserSession:
    session_id = request.cookies.get(SESSION_COOKIE)
    session = user_sessions.get(session_id or "")
    if session is None or session.expires_at <= time.time():
        if session_id:
            user_sessions.pop(session_id, None)
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session


def get_optional_session(request: Request) -> UserSession | None:
    session_id = request.cookies.get(SESSION_COOKIE)
    session = user_sessions.get(session_id or "")
    if session is not None and session.expires_at > time.time():
        return session
    if session_id:
        user_sessions.pop(session_id, None)
    return None


def require_roles(*allowed_roles: str):
    def dependency(
        request: Request,
        session: Annotated[UserSession, Depends(get_current_session)],
    ) -> AuthUser:
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("X-CSRF-Token") != session.csrf_token:
                raise HTTPException(status_code=403, detail="Invalid CSRF token")
        if session.user.roles.isdisjoint(allowed_roles):
            raise HTTPException(status_code=403, detail="Insufficient role permissions")
        return session.user

    return dependency
