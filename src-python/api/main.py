from contextlib import asynccontextmanager
import os
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from cloudsaver import advisor, payments, team, updater
from cloudsaver.analytics import analytics_summary, record_event
from cloudsaver.config import load_privacy_settings, save_privacy_settings
from cloudsaver.diagnostics import diagnostics_export
from cloudsaver.history import (
    get_license_delivery,
    list_scan_history,
    mark_license_delivery_activated,
    save_license_delivery,
)
from cloudsaver.license import activate_license, deactivate_license, is_biz, is_pro, load_license
from api import auth, cleanup, duplicates, gdrive, icloud, optimize, scan, sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="CloudSaver Sidecar", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420", "http://127.0.0.1:1420"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/scan")
app.include_router(gdrive.router, prefix="/gdrive")
app.include_router(icloud.router, prefix="/icloud")
app.include_router(duplicates.router, prefix="/duplicates")
app.include_router(cleanup.router, prefix="/cleanup")
app.include_router(optimize.router, prefix="/optimize")
app.include_router(auth.router, prefix="/auth")
app.include_router(sources.router, prefix="/sources")


@app.get("/health")
async def health():
    return {"status": "ok"}


def license_state_response(state) -> dict:
    return {
        "tier": state.tier,
        "valid": state.valid,
        "expired": state.expired,
        "expires_at": state.expires_at,
        "key": state.key,
        "key_masked": state.key,
        "email": state.email,
        "is_pro": is_pro(state),
        "is_biz": is_biz(state),
    }


def stripe_price_id_for_plan(plan: str) -> str:
    return {
        "pro_monthly": os.environ.get("CLOUDSAVER_STRIPE_PRO_PRICE_ID", ""),
        "pro_annual": os.environ.get("CLOUDSAVER_STRIPE_PRO_ANNUAL_ID", ""),
        "business": os.environ.get("CLOUDSAVER_STRIPE_BIZ_PRICE_ID", ""),
    }.get(plan, "")


@app.get("/history")
async def history():
    return {"scans": list_scan_history()}


@app.get("/license")
async def license_status():
    return license_state_response(load_license())


@app.post("/license/activate")
async def license_activate(payload: dict):
    key = (payload.get("key") or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="A CloudSaver license key is required.")
    state = activate_license(key, payload.get("email"))
    record_event("license_activated", {"tier": state.tier})
    return {"success": True, **license_state_response(state)}


@app.post("/license/deactivate")
async def license_deactivate():
    deactivate_license()
    return {"success": True}


@app.get("/capabilities")
async def capabilities():
    payments_configured = any(
        stripe_price_id_for_plan(plan) for plan in ("pro_monthly", "pro_annual", "business")
    )
    return {
        "payments_configured": payments_configured and payments.STRIPE_AVAILABLE,
        "advisor_package_available": advisor.ADVISOR_AVAILABLE,
        "advisor_api_key_configured": bool(os.environ.get("ANTHROPIC_API_KEY", "")),
        "team_preview_available": True,
    }


@app.post("/payments/checkout")
async def payment_checkout(payload: dict):
    price_id = (payload.get("price_id") or "").strip() or stripe_price_id_for_plan(
        (payload.get("plan") or "").strip()
    )
    if not price_id:
        raise HTTPException(status_code=400, detail="A Stripe price id is required.")
    base_url = os.environ.get("CLOUDSAVER_BASE_URL", "http://127.0.0.1:8765")
    checkout_url = payments.create_checkout_session(
        price_id=price_id,
        customer_email=payload.get("email") or None,
        success_url=f"{base_url}/payments/success",
        cancel_url=base_url,
    )
    return {"checkout_url": checkout_url}


@app.post("/payments/webhook")
async def payment_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    delivery = payments.handle_webhook(payload, signature)
    if delivery:
        save_license_delivery(delivery)
    return {"success": True}


@app.get("/payments/success")
async def payment_success(session_id: str = ""):
    if not session_id:
        raise HTTPException(status_code=400, detail="A Stripe Checkout session id is required.")
    delivery = get_license_delivery(session_id)
    if not delivery:
        raise HTTPException(status_code=400, detail="License delivery was not found.")
    state = activate_license(delivery["license_key"], delivery.get("customer_email"))
    mark_license_delivery_activated(session_id)
    return {
        "license_key": delivery["license_key"],
        "tier": delivery["tier"],
        "expires_at": state.expires_at,
        **license_state_response(state),
    }


@app.get("/advisor/status")
async def advisor_status():
    if not advisor.ADVISOR_AVAILABLE:
        return {"available": False, "reason": "package_missing"}
    if not os.environ.get("ANTHROPIC_API_KEY", ""):
        return {"available": False, "reason": "api_key_missing"}
    return {"available": True, "reason": "ok"}


@app.get("/update/status")
async def update_status():
    return updater.update_info_dict(updater.get_update_state())


@app.get("/analytics/summary")
async def analytics():
    return analytics_summary()


@app.get("/privacy/settings")
async def privacy_settings():
    return load_privacy_settings()


@app.post("/privacy/settings")
async def privacy_settings_update(payload: dict):
    settings = save_privacy_settings(payload)
    record_event(
        "privacy_settings_updated",
        {"local_diagnostics_enabled": settings["local_diagnostics_enabled"]},
    )
    return settings


@app.get("/diagnostics/export")
async def diagnostics_export_endpoint():
    return diagnostics_export()


def require_biz_state():
    if not is_biz(load_license()):
        raise HTTPException(
            status_code=402,
            detail={"error": "biz_required", "message": "This feature requires CloudSaver Business."},
        )


@app.get("/team/status")
async def team_status():
    require_biz_state()
    return team.team_status()


@app.get("/team/audits")
async def team_audits():
    require_biz_state()
    return {"audits": team.list_shared_audits()}


@app.get("/team/schedule")
async def team_schedule_list():
    require_biz_state()
    return {"schedules": team.list_schedules()}


@app.post("/team/create")
async def team_create(payload: dict):
    require_biz_state()
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="A team workspace name is required.")
    return team.create_workspace(name)


@app.post("/team/join")
async def team_join(payload: dict):
    require_biz_state()
    invite_code = (payload.get("invite_code") or "").strip()
    if not invite_code:
        raise HTTPException(status_code=400, detail="A team invite code is required.")
    return team.join_workspace(invite_code, payload.get("display_name"))


@app.post("/team/share-audit")
async def team_share_audit(payload: dict):
    require_biz_state()
    scan_id = payload.get("scan_id")
    if not scan_id:
        raise HTTPException(status_code=400, detail="A scan history id is required.")
    return {"shared_audit_id": team.share_audit(int(scan_id))}


@app.post("/team/schedule")
async def team_schedule_create(payload: dict):
    require_biz_state()
    path = (payload.get("path") or "").strip()
    cron_expression = (payload.get("cron_expression") or "").strip()
    if not path or not cron_expression:
        raise HTTPException(status_code=400, detail="A path and cron expression are required.")
    return {"schedule_id": team.create_schedule(path, cron_expression)}


@app.delete("/team/schedule/{schedule_id}")
async def team_schedule_delete(schedule_id: str):
    require_biz_state()
    team.delete_schedule(schedule_id)
    return {"success": True}


@app.post("/team/leave")
async def team_leave():
    require_biz_state()
    team.leave_workspace()
    return {"success": True}
