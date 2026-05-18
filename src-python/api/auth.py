from __future__ import annotations

import base64
import hashlib
import os
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
GOOGLE_CLIENT_ID = os.environ.get("CLOUDSAVER_GOOGLE_CLIENT_ID", "")
REDIRECT_URI = "cloudsaver://oauth/callback"
_pending: dict[str, str] = {}


@router.get("/health")
async def health():
    return {"status": "ok", "router": "auth"}


def _pkce_pair():
    verifier = secrets.token_urlsafe(96)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
        .rstrip(b"=")
        .decode()
    )
    return verifier, challenge


@router.get("/gdrive/url")
async def gdrive_auth_url():
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    _pending[state] = verifier

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(
            [
                "https://www.googleapis.com/auth/drive.metadata.readonly",
                "https://www.googleapis.com/auth/drive.file",
            ]
        ),
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "state": state,
    }
    return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params), "state": state}


class TokenExchangeRequest(BaseModel):
    code: str
    state: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/gdrive/exchange")
async def gdrive_exchange(req: TokenExchangeRequest):
    import httpx

    verifier = _pending.pop(req.state, None)
    if not verifier:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": req.code,
                "client_id": GOOGLE_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
            },
        )
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data.get("error_description", data["error"]))

    return {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token"),
        "expires_in": data.get("expires_in"),
    }


@router.post("/gdrive/refresh")
async def gdrive_refresh(req: RefreshRequest):
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "refresh_token": req.refresh_token,
                "client_id": GOOGLE_CLIENT_ID,
                "grant_type": "refresh_token",
            },
        )
    data = response.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data.get("error_description", data["error"]))
    return {"access_token": data["access_token"], "expires_in": data.get("expires_in")}
