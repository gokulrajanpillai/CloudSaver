from __future__ import annotations

"""
License key format: CS-{TIER}-{YYYYMM}-{PAYLOAD}-{CHECKSUM}

TIER:      PRO | BIZ | ENT
YYYYMM:    expiry year+month (202512 = expires Dec 2025)
PAYLOAD:   base32 token, unique per key
CHECKSUM:  base32 HMAC-SHA256 of "CS-{TIER}-{YYYYMM}-{PAYLOAD}"
           using CLOUDSAVER_LICENSE_SECRET env var as key
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from cloudsaver.config import app_data_path

LICENSE_SECRET = os.environ.get("CLOUDSAVER_LICENSE_SECRET", "cs-dev-secret-do-not-use-in-prod")
LICENSE_FILE = app_data_path("license.json")
TIER_FREE = "FREE"
TIER_PRO = "PRO"
TIER_BIZ = "BIZ"
TIER_ENT = "ENT"
PRO_TIERS = {TIER_PRO, TIER_BIZ, TIER_ENT}
BIZ_TIERS = {TIER_BIZ, TIER_ENT}

_license_state: "LicenseState | None" = None


@dataclass
class LicenseState:
    tier: str
    valid: bool
    expires_at: str
    expired: bool
    key: str
    activated_at: float | None
    email: str | None


def _base32_token(raw: bytes, length: int | None = None) -> str:
    token = base64.b32encode(raw).decode("ascii").rstrip("=")
    return token[:length] if length else token


def _current_yyyymm() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m")


def _is_expired(expiry_yyyymm: str) -> bool:
    return expiry_yyyymm < _current_yyyymm()


def _expires_at(expiry_yyyymm: str) -> str:
    return f"{expiry_yyyymm[:4]}-{expiry_yyyymm[4:]}"


def _masked_key(key: str) -> str:
    parts = key.strip().upper().split("-")
    if len(parts) != 5:
        return ""
    return f"{parts[0]}-{parts[1]}-****-****-{parts[4]}"


def _free_state() -> LicenseState:
    return LicenseState(
        tier=TIER_FREE,
        valid=False,
        expires_at="",
        expired=False,
        key="",
        activated_at=None,
        email=None,
    )


def _unsigned_key(tier: str, expiry_yyyymm: str, payload: str) -> str:
    return f"CS-{tier}-{expiry_yyyymm}-{payload}"


def _checksum(unsigned: str) -> str:
    digest = hmac.new(
        LICENSE_SECRET.encode("utf-8"),
        unsigned.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return _base32_token(digest, 5)


def validate_key(key: str) -> tuple[bool, str, str]:
    """Returns (is_valid, tier, expiry_yyyymm). Pure function, no I/O."""

    parts = key.strip().upper().split("-")
    if len(parts) != 5 or parts[0] != "CS":
        return False, TIER_FREE, ""

    _, tier, expiry_yyyymm, payload, supplied_checksum = parts
    if tier not in PRO_TIERS:
        return False, TIER_FREE, ""
    if len(expiry_yyyymm) != 6 or not expiry_yyyymm.isdigit():
        return False, tier, ""
    if len(payload) < 6 or not payload.isalnum():
        return False, tier, expiry_yyyymm
    if not supplied_checksum.isalnum():
        return False, tier, expiry_yyyymm

    expected = _checksum(_unsigned_key(tier, expiry_yyyymm, payload))
    return hmac.compare_digest(expected, supplied_checksum), tier, expiry_yyyymm


def activate_license(key: str, email: str | None = None) -> LicenseState:
    """Validates key, persists to LICENSE_FILE, returns state."""

    global _license_state

    normalized_key = key.strip().upper()
    is_valid, tier, expiry_yyyymm = validate_key(normalized_key)
    if not is_valid:
        raise ValueError("Invalid CloudSaver license key.")

    expired = _is_expired(expiry_yyyymm)
    state = LicenseState(
        tier=tier,
        valid=not expired,
        expires_at=_expires_at(expiry_yyyymm),
        expired=expired,
        key=_masked_key(normalized_key),
        activated_at=time.time(),
        email=email.strip() if email else None,
    )
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)
    LICENSE_FILE.write_text(
        json.dumps(
            {
                **asdict(state),
                "raw_key": normalized_key,
                "expiry_yyyymm": expiry_yyyymm,
            },
            indent=2,
        )
    )
    _license_state = state
    return state


def load_license() -> LicenseState:
    """Reads LICENSE_FILE. Returns FREE tier if not found or invalid."""

    global _license_state
    if _license_state is not None:
        return _license_state

    if not LICENSE_FILE.exists():
        _license_state = _free_state()
        return _license_state

    try:
        data = json.loads(LICENSE_FILE.read_text())
        raw_key = data.get("raw_key") or ""
        is_valid, tier, expiry_yyyymm = validate_key(raw_key)
        if not is_valid:
            _license_state = _free_state()
            return _license_state
        expired = _is_expired(expiry_yyyymm)
        _license_state = LicenseState(
            tier=tier,
            valid=not expired,
            expires_at=_expires_at(expiry_yyyymm),
            expired=expired,
            key=_masked_key(raw_key),
            activated_at=data.get("activated_at"),
            email=data.get("email"),
        )
        return _license_state
    except Exception:
        _license_state = _free_state()
        return _license_state


def deactivate_license() -> LicenseState:
    """Removes the persisted license and returns the free state."""

    global _license_state
    try:
        LICENSE_FILE.unlink()
    except FileNotFoundError:
        pass
    _license_state = _free_state()
    return _license_state


def is_pro(state: LicenseState | None = None) -> bool:
    """True if current license is PRO, BIZ, or ENT and not expired."""

    license_state = state or load_license()
    return license_state.valid and not license_state.expired and license_state.tier in PRO_TIERS


def is_biz(state: LicenseState | None = None) -> bool:
    """True if current license is BIZ or ENT and not expired."""

    license_state = state or load_license()
    return license_state.valid and not license_state.expired and license_state.tier in BIZ_TIERS


def generate_license_key(tier: str, expiry_yyyymm: str) -> str:
    """Admin tool - generates a valid signed license key. Never expose via API."""

    normalized_tier = tier.strip().upper()
    if normalized_tier not in PRO_TIERS:
        raise ValueError("License tier must be PRO, BIZ, or ENT.")
    if len(expiry_yyyymm) != 6 or not expiry_yyyymm.isdigit():
        raise ValueError("License expiry must use YYYYMM format.")

    payload = _base32_token(secrets.token_bytes(5))
    unsigned = _unsigned_key(normalized_tier, expiry_yyyymm, payload)
    return f"{unsigned}-{_checksum(unsigned)}"
