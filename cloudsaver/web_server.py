from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cloudsaver.core import (
    DEFAULT_IMAGE_QUALITY,
    HD_RESOLUTION,
    REDUCED_DIR,
    attach_duplicate_verification,
    attach_reduction_estimates,
    build_storage_audit,
    convert_image_format,
    find_perceptual_duplicates,
    human_readable_size,
    is_path_within,
    optimize_png_lossless,
    quarantine_selected_files,
    reduce_selected_images,
    restore_quarantine,
    scan_local_folder,
)
from cloudsaver import payments
from cloudsaver.history import (
    get_license_delivery,
    list_scan_history,
    mark_license_delivery_activated,
    save_license_delivery,
    save_scan_history,
)
from cloudsaver.license import (
    activate_license,
    deactivate_license,
    is_biz,
    is_pro,
    load_license,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "web"
SCAN_JOBS: dict[str, dict] = {}
SCAN_JOBS_LOCK = threading.Lock()


def common_scan_locations() -> list[dict]:
    """Return useful local and mounted folder suggestions."""

    home = Path.home()
    candidates = [
        home,
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Pictures",
        home / "Library" / "CloudStorage",
        Path("/Volumes"),
    ]
    if Path("/Volumes").exists():
        candidates.extend(path for path in Path("/Volumes").iterdir() if path.is_dir())

    seen = set()
    locations = []
    for candidate in candidates:
        path = str(candidate)
        if path in seen or not candidate.exists():
            continue
        seen.add(path)
        locations.append({"label": candidate.name or path, "path": path})
    return locations


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


def require_pro(handler_method):
    """Decorator for request handler methods that require Pro tier."""

    def wrapper(self, payload):
        if not is_pro(load_license()):
            self.write_json(
                {"error": "pro_required", "message": "This feature requires CloudSaver Pro."},
                HTTPStatus.PAYMENT_REQUIRED,
            )
            return
        return handler_method(self, payload)

    return wrapper


def require_biz(handler_method):
    """Decorator for request handler methods that require Business tier."""

    def wrapper(self, payload):
        if not is_biz(load_license()):
            self.write_json(
                {"error": "biz_required", "message": "This feature requires CloudSaver Business."},
                HTTPStatus.PAYMENT_REQUIRED,
            )
            return
        return handler_method(self, payload)

    return wrapper


class CloudSaverRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/locations":
                self.write_json({"locations": common_scan_locations()})
                return
            if parsed.path == "/api/health":
                self.write_json({"status": "ok"})
                return
            if parsed.path == "/api/scan/status":
                self.handle_scan_status(parsed)
                return
            if parsed.path == "/api/history":
                self.write_json({"scans": list_scan_history()})
                return
            if parsed.path == "/api/license":
                self.handle_license_status()
                return
            if parsed.path == "/api/payments/success":
                self.handle_payment_success(parsed)
                return
        except ValueError as error:
            self.write_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as error:
            self.write_json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/payments/webhook":
                self.handle_payment_webhook()
                return
            payload = self.read_json()
            if parsed.path == "/api/scan":
                self.handle_scan(payload)
                return
            if parsed.path == "/api/scan/start":
                self.handle_scan_start(payload)
                return
            if parsed.path == "/api/reduce":
                self.handle_reduce(payload)
                return
            if parsed.path == "/api/convert":
                self.handle_convert(payload)
                return
            if parsed.path == "/api/optimize-png":
                self.handle_optimize_png(payload)
                return
            if parsed.path == "/api/scan/perceptual":
                self.handle_perceptual_scan_start(payload)
                return
            if parsed.path == "/api/quarantine":
                self.handle_quarantine(payload)
                return
            if parsed.path == "/api/restore":
                self.handle_restore(payload)
                return
            if parsed.path == "/api/reveal":
                self.handle_reveal(payload)
                return
            if parsed.path == "/api/license/activate":
                self.handle_license_activate(payload)
                return
            if parsed.path == "/api/license/deactivate":
                self.handle_license_deactivate(payload)
                return
            if parsed.path == "/api/payments/checkout":
                self.handle_payment_checkout(payload)
                return
        except ValueError as error:
            self.write_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except (FileNotFoundError, NotADirectoryError) as error:
            self.write_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as error:
            self.write_json({"error": str(error)}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.write_json({"error": "Unknown endpoint."}, HTTPStatus.NOT_FOUND)

    def read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return {}
        raw_body = self.rfile.read(content_length)
        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Request body must be valid JSON.") from error

    def read_raw_body(self) -> bytes:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            return b""
        return self.rfile.read(content_length)

    def handle_scan(self, payload: dict) -> None:
        self.write_json(run_scan(payload))

    def handle_license_status(self) -> None:
        self.write_json(license_state_response(load_license()))

    def handle_license_activate(self, payload: dict) -> None:
        key = payload.get("key", "").strip()
        if not key:
            raise ValueError("A CloudSaver license key is required.")
        state = activate_license(key, payload.get("email"))
        self.write_json({"success": True, **license_state_response(state)})

    def handle_license_deactivate(self, payload: dict) -> None:
        deactivate_license()
        self.write_json({"success": True})

    def handle_payment_checkout(self, payload: dict) -> None:
        price_id = payload.get("price_id", "").strip()
        if not price_id:
            raise ValueError("A Stripe price id is required.")
        base_url = os.environ.get("CLOUDSAVER_BASE_URL", "http://127.0.0.1:8765")
        checkout_url = payments.create_checkout_session(
            price_id=price_id,
            customer_email=payload.get("email") or None,
            success_url=f"{base_url}/api/payments/success",
            cancel_url=base_url,
        )
        self.write_json({"checkout_url": checkout_url})

    def handle_payment_webhook(self) -> None:
        payload = self.read_raw_body()
        signature = self.headers.get("Stripe-Signature", "")
        delivery = payments.handle_webhook(payload, signature)
        if delivery:
            save_license_delivery(delivery)
        self.write_json({"success": True})

    def handle_payment_success(self, parsed) -> None:
        params = parse_qs(parsed.query or "")
        session_id = (params.get("session_id") or [""])[0]
        if not session_id:
            raise ValueError("A Stripe Checkout session id is required.")
        delivery = get_license_delivery(session_id)
        if not delivery:
            raise ValueError("License delivery was not found.")
        state = activate_license(delivery["license_key"], delivery.get("customer_email"))
        mark_license_delivery_activated(session_id)
        self.write_json(
            {
                "license_key": delivery["license_key"],
                "tier": delivery["tier"],
                "expires_at": state.expires_at,
                **license_state_response(state),
            }
        )

    def handle_scan_start(self, payload: dict) -> None:
        job_id = str(uuid.uuid4())
        with SCAN_JOBS_LOCK:
            SCAN_JOBS[job_id] = {
                "id": job_id,
                "status": "queued",
                "created_at": time.time(),
                "updated_at": time.time(),
                "files_scanned": 0,
                "current_path": "",
                "current_folder": "",
                "stage": "Waiting to start",
            }

        thread = threading.Thread(target=run_scan_job, args=(job_id, payload), daemon=True)
        thread.start()
        self.write_json({"job_id": job_id, "status": "queued"})

    def handle_scan_status(self, parsed) -> None:
        query = parsed.query or ""
        params = dict(part.split("=", 1) for part in query.split("&") if "=" in part)
        job_id = params.get("job_id")
        if not job_id:
            raise ValueError("A scan job id is required.")
        with SCAN_JOBS_LOCK:
            job = SCAN_JOBS.get(job_id)
            if not job:
                raise ValueError("Scan job was not found.")
            self.write_json(job)

    def handle_reduce(self, payload: dict) -> None:
        root_path = payload.get("root_path", "").strip()
        file_ids = payload.get("file_ids") or []
        if not root_path:
            raise ValueError("A scan root path is required.")
        if not isinstance(file_ids, list) or not file_ids:
            raise ValueError("Select at least one file to reduce.")

        quality = int(payload.get("quality", DEFAULT_IMAGE_QUALITY))
        max_width = int(payload.get("max_width", HD_RESOLUTION[0]))
        max_height = int(payload.get("max_height", HD_RESOLUTION[1]))
        output_dir = payload.get("output_dir") or REDUCED_DIR
        output_dir = os.path.abspath(os.path.expanduser(output_dir))

        result = reduce_selected_images(
            root_path=root_path,
            file_ids=file_ids,
            output_dir=output_dir,
            max_resolution=(max_width, max_height),
            quality=quality,
        )
        self.write_json(result)

    @require_pro
    def handle_convert(self, payload: dict) -> None:
        root_path = payload.get("root_path", "").strip()
        file_ids = payload.get("file_ids") or []
        if not root_path:
            raise ValueError("A scan root path is required.")
        if not isinstance(file_ids, list) or not file_ids:
            raise ValueError("Select at least one file to convert.")

        quality = int(payload.get("quality", DEFAULT_IMAGE_QUALITY))
        max_width = int(payload.get("max_width", HD_RESOLUTION[0]))
        max_height = int(payload.get("max_height", HD_RESOLUTION[1]))
        target_format = payload.get("target_format") or "webp"
        output_dir = payload.get("output_dir") or REDUCED_DIR
        output_dir = os.path.abspath(os.path.expanduser(output_dir))

        self.write_json(
            convert_image_format(
                root_path=root_path,
                file_ids=file_ids,
                target_format=target_format,
                output_dir=output_dir,
                max_resolution=(max_width, max_height),
                quality=quality,
            )
        )

    def handle_optimize_png(self, payload: dict) -> None:
        root_path = payload.get("root_path", "").strip()
        file_ids = payload.get("file_ids") or []
        if not root_path:
            raise ValueError("A scan root path is required.")
        if not isinstance(file_ids, list) or not file_ids:
            raise ValueError("Select at least one PNG file to optimize.")
        root = Path(root_path).expanduser().resolve()
        results = []
        for file_id in file_ids:
            path = (root / file_id).resolve()
            if not path.exists() or not path.is_file() or not str(path).lower().endswith(".png"):
                results.append({"id": file_id, "status": "skipped", "error": "PNG file not found."})
                continue
            if not is_path_within(path, root):
                results.append({"id": file_id, "status": "skipped", "error": "Path is outside scan root."})
                continue
            try:
                before, after = optimize_png_lossless(path)
            except RuntimeError as error:
                results.append({"id": file_id, "status": "unavailable", "error": str(error)})
                continue
            results.append(
                {
                    "id": file_id,
                    "status": "optimized",
                    "before_bytes": before,
                    "after_bytes": after,
                    "saved_bytes": max(before - after, 0),
                }
            )
        self.write_json({"results": results})

    @require_pro
    def handle_perceptual_scan_start(self, payload: dict) -> None:
        root_path = payload.get("root_path", "").strip()
        if not root_path:
            raise ValueError("A scan root path is required.")
        job_id = str(uuid.uuid4())
        with SCAN_JOBS_LOCK:
            SCAN_JOBS[job_id] = {
                "id": job_id,
                "status": "queued",
                "created_at": time.time(),
                "updated_at": time.time(),
                "files_scanned": 0,
                "current_path": "",
                "current_folder": "",
                "stage": "Waiting to start",
            }
        thread = threading.Thread(target=run_perceptual_scan_job, args=(job_id, payload), daemon=True)
        thread.start()
        self.write_json({"job_id": job_id, "status": "queued"})

    def handle_quarantine(self, payload: dict) -> None:
        root_path = payload.get("root_path", "").strip()
        file_ids = payload.get("file_ids") or []
        if not root_path:
            raise ValueError("A scan root path is required.")
        if not isinstance(file_ids, list) or not file_ids:
            raise ValueError("Select at least one file to move to review.")
        self.write_json(quarantine_selected_files(root_path, file_ids))

    def handle_restore(self, payload: dict) -> None:
        manifest_path = payload.get("manifest_path", "").strip()
        if not manifest_path:
            raise ValueError("A manifest path is required.")
        self.write_json(restore_quarantine(manifest_path))

    def handle_reveal(self, payload: dict) -> None:
        path = payload.get("path", "").strip()
        if not path:
            raise ValueError("A file path is required.")
        reveal_path_in_platform_file_manager(path)
        self.write_json({"status": "opened"})

    def write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def update_scan_job(job_id: str | None, updates: dict) -> None:
    if not job_id:
        return
    with SCAN_JOBS_LOCK:
        job = SCAN_JOBS.get(job_id)
        if job:
            job.update(updates)
            job["updated_at"] = time.time()


def run_scan(payload: dict, job_id: str | None = None) -> dict:
    def update_progress(progress: dict) -> None:
        progress["status"] = "scanning"
        progress["stage"] = "Reading files"
        update_scan_job(job_id, progress)

    root_path = payload.get("path", "").strip()
    if not root_path:
        raise ValueError("A folder path is required.")
    quality = int(payload.get("quality", DEFAULT_IMAGE_QUALITY))
    max_width = int(payload.get("max_width", HD_RESOLUTION[0]))
    max_height = int(payload.get("max_height", HD_RESOLUTION[1]))

    update_scan_job(job_id, {"status": "scanning", "stage": "Reading files"})
    files = scan_local_folder(root_path, update_progress)
    update_scan_job(job_id, {"status": "scanning", "stage": "Hashing duplicates"})
    files = attach_duplicate_verification(files)
    update_scan_job(job_id, {"status": "scanning", "stage": "Estimating reductions"})
    files_with_estimates = attach_reduction_estimates(files, (max_width, max_height), quality)
    update_scan_job(job_id, {"status": "scanning", "stage": "Building summary"})
    audit = build_storage_audit(files_with_estimates)
    estimated_reducible_bytes = sum(
        file["reduction"]["estimated_saved_bytes"]
        for file in files_with_estimates
        if file["reduction"]["supported"]
    )
    files_with_estimates.sort(key=lambda file: file["size_bytes"], reverse=True)

    result = {
        "root_path": str(Path(root_path).expanduser().resolve()),
        "audit": audit,
        "files": files_with_estimates,
        "estimated_reducible_bytes": estimated_reducible_bytes,
        "estimated_reducible_human": human_readable_size(estimated_reducible_bytes),
    }
    result["history_id"] = save_scan_history(result["root_path"], audit)
    return result


def run_scan_job(job_id: str, payload: dict) -> None:
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id]["status"] = "scanning"
        SCAN_JOBS[job_id]["stage"] = "Starting scan"
        SCAN_JOBS[job_id]["updated_at"] = time.time()
    try:
        result = run_scan(payload, job_id)
    except Exception as error:
        with SCAN_JOBS_LOCK:
            SCAN_JOBS[job_id].update(
                {
                    "status": "failed",
                    "error": str(error),
                    "updated_at": time.time(),
                }
            )
        return
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id].update(
            {
                "status": "complete",
                "result": result,
                "files_scanned": len(result["files"]),
                "current_path": "",
                "current_folder": "",
                "stage": "Complete",
                "updated_at": time.time(),
            }
        )


def run_perceptual_scan_job(job_id: str, payload: dict) -> None:
    def update_progress(progress: dict) -> None:
        progress["status"] = "scanning"
        progress["stage"] = "Reading images"
        update_scan_job(job_id, progress)

    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id]["status"] = "scanning"
        SCAN_JOBS[job_id]["stage"] = "Starting image scan"
        SCAN_JOBS[job_id]["updated_at"] = time.time()
    try:
        root_path = payload.get("root_path", "").strip()
        threshold = int(payload.get("threshold", 10))
        files = scan_local_folder(root_path, update_progress)
        update_scan_job(job_id, {"status": "scanning", "stage": "Estimating reductions"})
        files_with_estimates = attach_reduction_estimates(files)
        update_scan_job(job_id, {"status": "scanning", "stage": "Comparing images"})
        audit = build_storage_audit(files_with_estimates)
        groups = find_perceptual_duplicates(audit["top_files"] + files_with_estimates, threshold)
        result = {"perceptual_duplicate_groups": groups}
    except Exception as error:
        with SCAN_JOBS_LOCK:
            SCAN_JOBS[job_id].update(
                {
                    "status": "failed",
                    "error": str(error),
                    "updated_at": time.time(),
                }
            )
        return
    with SCAN_JOBS_LOCK:
        SCAN_JOBS[job_id].update(
            {
                "status": "complete",
                "result": result,
                "files_scanned": len(result["perceptual_duplicate_groups"]),
                "current_path": "",
                "current_folder": "",
                "stage": "Complete",
                "updated_at": time.time(),
            }
        )


def reveal_path_in_platform_file_manager(path: str) -> None:
    """Open the selected file's location in the user's platform file manager."""

    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    if sys.platform == "darwin":
        command = ["open", "-R", str(target)]
    elif sys.platform.startswith("win"):
        command = ["explorer", f"/select,{target}"]
    else:
        folder = target if target.is_dir() else target.parent
        command = ["xdg-open", str(folder)]

    subprocess.Popen(command)


def run(host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), CloudSaverRequestHandler)
    print(f"CloudSaver UI running at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CloudSaver local web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
