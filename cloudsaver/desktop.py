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


def run_desktop(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run CloudSaver as a local desktop-style launcher."""

    port = find_available_port(host, port)
    server = ThreadingHTTPServer((host, port), CloudSaverRequestHandler)
    url = f"http://{host}:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"CloudSaver desktop launcher running at {url}")
    webbrowser.open(url)
    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the CloudSaver desktop launcher.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run_desktop(args.host, args.port)


if __name__ == "__main__":
    main()
