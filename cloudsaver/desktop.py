import argparse
import socket
import threading
import webbrowser
from http.server import ThreadingHTTPServer

from cloudsaver.web_server import CloudSaverRequestHandler


def find_available_port(host: str, preferred_port: int) -> int:
    """Return ``preferred_port`` when available, otherwise ask the OS for a free port."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if probe.connect_ex((host, preferred_port)) != 0:
            return preferred_port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind((host, 0))
        return int(probe.getsockname()[1])


def start_local_server(host: str, port: int) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    """Start the local CloudSaver backend and return the server plus URL."""

    port = find_available_port(host, port)
    server = ThreadingHTTPServer((host, port), CloudSaverRequestHandler)
    url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, url


def run_webview(url: str) -> bool:
    """Run CloudSaver in an embedded desktop webview when pywebview is available."""

    try:
        import webview
    except ImportError:
        return False

    webview.create_window(
        "CloudSaver",
        url,
        width=1280,
        height=860,
        min_size=(960, 680),
    )
    webview.start()
    return True


def run_desktop(host: str = "127.0.0.1", port: int = 8765, browser: bool = False) -> None:
    """Run CloudSaver as a local desktop app using the same web UI."""

    server, thread, url = start_local_server(host, port)
    print(f"CloudSaver desktop app running at {url}")
    if not browser and run_webview(url):
        server.shutdown()
        return

    print("Embedded desktop shell is unavailable; opening the browser fallback.")
    webbrowser.open(url)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CloudSaver desktop launcher.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--browser", action="store_true", help="Open the UI in a browser.")
    args = parser.parse_args()
    run_desktop(args.host, args.port, args.browser)


if __name__ == "__main__":
    main()
