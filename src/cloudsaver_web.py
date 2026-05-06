import argparse
import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from src.cloudsaver import (
    DEFAULT_IMAGE_QUALITY,
    HD_RESOLUTION,
    REDUCED_DIR,
    attach_reduction_estimates,
    build_storage_audit,
    human_readable_size,
    reduce_selected_images,
    scan_local_folder,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_ROOT = PROJECT_ROOT / "web"


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


class CloudSaverRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/locations":
            self.write_json({"locations": common_scan_locations()})
            return
        if parsed.path == "/api/health":
            self.write_json({"status": "ok"})
            return
        if parsed.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json()
            if parsed.path == "/api/scan":
                self.handle_scan(payload)
                return
            if parsed.path == "/api/reduce":
                self.handle_reduce(payload)
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

    def handle_scan(self, payload: dict) -> None:
        root_path = payload.get("path", "").strip()
        if not root_path:
            raise ValueError("A folder path is required.")
        quality = int(payload.get("quality", DEFAULT_IMAGE_QUALITY))
        max_width = int(payload.get("max_width", HD_RESOLUTION[0]))
        max_height = int(payload.get("max_height", HD_RESOLUTION[1]))

        files = scan_local_folder(root_path)
        files_with_estimates = attach_reduction_estimates(
            files, (max_width, max_height), quality
        )
        audit = build_storage_audit(files_with_estimates)
        estimated_reducible_bytes = sum(
            file["reduction"]["estimated_saved_bytes"]
            for file in files_with_estimates
            if file["reduction"]["supported"]
        )
        files_with_estimates.sort(key=lambda file: file["size_bytes"], reverse=True)

        self.write_json(
            {
                "root_path": str(Path(root_path).expanduser().resolve()),
                "audit": audit,
                "files": files_with_estimates,
                "estimated_reducible_bytes": estimated_reducible_bytes,
                "estimated_reducible_human": human_readable_size(estimated_reducible_bytes),
            }
        )

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

    def write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


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
