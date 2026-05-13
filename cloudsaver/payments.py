from __future__ import annotations

"""
Stripe integration for CloudSaver Pro license purchase.

Required environment variables:
  CLOUDSAVER_STRIPE_SECRET_KEY      - sk_live_... or sk_test_...
  CLOUDSAVER_STRIPE_WEBHOOK_SECRET  - whsec_...
  CLOUDSAVER_STRIPE_PRO_PRICE_ID    - price_... (Pro monthly)
  CLOUDSAVER_STRIPE_PRO_ANNUAL_ID   - price_... (Pro annual)
  CLOUDSAVER_STRIPE_BIZ_PRICE_ID    - price_... (Business per seat)
  CLOUDSAVER_LICENSE_SECRET         - must match license.py
  CLOUDSAVER_BASE_URL               - e.g. https://cloudsaver.app
"""

import os
from datetime import datetime, timezone

from cloudsaver.license import TIER_BIZ, TIER_PRO, generate_license_key

try:
    import stripe

    STRIPE_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised through availability checks
    stripe = None
    STRIPE_AVAILABLE = False

STRIPE_SECRET = os.environ.get("CLOUDSAVER_STRIPE_SECRET_KEY", "")
WEBHOOK_SECRET = os.environ.get("CLOUDSAVER_STRIPE_WEBHOOK_SECRET", "")


def create_checkout_session(
    price_id: str,
    customer_email: str | None,
    success_url: str,
    cancel_url: str,
) -> str:
    """Creates a Stripe Checkout session and returns the checkout URL."""

    if not STRIPE_AVAILABLE:
        raise RuntimeError("stripe package not installed")
    if not STRIPE_SECRET:
        raise RuntimeError("CLOUDSAVER_STRIPE_SECRET_KEY not set")
    stripe.api_key = STRIPE_SECRET
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        customer_email=customer_email,
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={"source": "cloudsaver_app"},
    )
    return session.url


def handle_webhook(payload: bytes, signature: str) -> dict | None:
    """
    Verifies webhook signature and handles checkout.session.completed.
    Returns a generated license delivery dict for actionable events.
    """

    if not STRIPE_AVAILABLE:
        raise RuntimeError("stripe package not installed")
    if not WEBHOOK_SECRET:
        raise RuntimeError("CLOUDSAVER_STRIPE_WEBHOOK_SECRET not set")

    event = stripe.Webhook.construct_event(payload, signature, WEBHOOK_SECRET)
    if event.get("type") != "checkout.session.completed":
        return None

    session = event["data"]["object"]
    price_id = _session_price_id(session)
    tier = _tier_for_price(price_id)
    expiry_yyyymm = compute_expiry_yyyymm(12)
    return {
        "session_id": session.get("id"),
        "license_key": generate_license_key(tier, expiry_yyyymm),
        "tier": tier,
        "expiry_yyyymm": expiry_yyyymm,
        "customer_email": session.get("customer_email") or session.get("customer_details", {}).get("email"),
    }


def compute_expiry_yyyymm(months_from_now: int = 12) -> str:
    """Returns YYYYMM string for license expiry."""

    now = datetime.now(timezone.utc)
    month_index = (now.month - 1) + months_from_now
    year = now.year + (month_index // 12)
    month = (month_index % 12) + 1
    return f"{year:04d}{month:02d}"


def _tier_for_price(price_id: str | None) -> str:
    if price_id and price_id == os.environ.get("CLOUDSAVER_STRIPE_BIZ_PRICE_ID", ""):
        return TIER_BIZ
    return TIER_PRO


def _session_price_id(session: dict) -> str | None:
    line_items = session.get("line_items", {}).get("data", [])
    if line_items:
        price = line_items[0].get("price") or {}
        return price.get("id")
    metadata = session.get("metadata") or {}
    return metadata.get("price_id")
