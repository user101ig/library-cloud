"""Endpoints εισόδου, callback και αποσύνδεσης."""

from __future__ import annotations

import secrets
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from app import auth

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login(request: Request) -> RedirectResponse:
    login_id, attempt, challenge = auth.create_login_attempt()
    redirect_uri = str(request.url_for("auth_callback"))
    response = RedirectResponse(auth.authorization_url(redirect_uri, attempt, challenge))
    response.set_cookie(
        auth.LOGIN_COOKIE,
        login_id,
        max_age=300,
        httponly=True,
        secure=auth.COOKIE_SECURE,
        samesite="lax",
    )
    return response


@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, code: str, state: str) -> RedirectResponse:
    login_id = request.cookies.get(auth.LOGIN_COOKIE, "")
    attempt = auth.login_attempts.pop(login_id, None)
    if attempt is None or attempt.expires_at <= time.time() or not secrets.compare_digest(attempt.state, state):
        raise HTTPException(status_code=400, detail="Invalid or expired login attempt")

    redirect_uri = str(request.url_for("auth_callback"))
    token = await auth.exchange_code(code, redirect_uri, attempt.code_verifier)
    session_id, session = auth.create_user_session(token)

    response = RedirectResponse(auth.FRONTEND_URL)
    response.delete_cookie(auth.LOGIN_COOKIE)
    response.set_cookie(
        auth.SESSION_COOKIE,
        session_id,
        max_age=max(1, int(session.expires_at - time.time())),
        httponly=True,
        secure=auth.COOKIE_SECURE,
        samesite="lax",
    )
    return response


@router.get("/me")
def me(session: auth.UserSession = Depends(auth.get_current_session)) -> dict:
    return {
        "subject": session.user.subject,
        "username": session.user.username,
        "email": session.user.email,
        "roles": sorted(session.user.roles),
        "csrf_token": session.csrf_token,
    }


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response) -> None:
    session_id = request.cookies.get(auth.SESSION_COOKIE, "")
    session = auth.user_sessions.get(session_id)
    if session is not None and request.headers.get("X-CSRF-Token") != session.csrf_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    session = auth.user_sessions.pop(session_id, None)
    if session and session.refresh_token:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                auth.LOGOUT_URL,
                data={
                    "client_id": auth.KEYCLOAK_CLIENT_ID,
                    "client_secret": auth.KEYCLOAK_CLIENT_SECRET,
                    "refresh_token": session.refresh_token,
                },
            )
    response.delete_cookie(auth.SESSION_COOKIE)
    response.headers["HX-Redirect"] = "/"
