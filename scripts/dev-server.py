#!/usr/bin/env python3
"""Serve the static site on the first available port (default scan from 8080)."""
import socket
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler


def find_port(start: int = 8080, attempts: int = 50) -> int:
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found in range {start}-{start + attempts - 1}")


def main() -> None:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    port = find_port(start)
    server = HTTPServer(("", port), SimpleHTTPRequestHandler)
    print(f"Serving adongclinic at http://localhost:{port}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
