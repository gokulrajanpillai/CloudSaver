import socket

import uvicorn


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


if __name__ == "__main__":
    port = find_free_port()
    print(f"CLOUDSAVER_PORT={port}", flush=True)
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
