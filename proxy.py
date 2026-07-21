#!/usr/bin/env python3
"""Fallback same-origin proxy for the INSA mgate.exe endpoint.

Only needed if direct browser fetches from index.html still get blocked by
CORS after the "no custom headers" fix (some browsers/environments may
still trigger a preflight, e.g. via a browser extension adding headers).
This proxy runs on your machine, forwards POST bodies server-side (where
CORS doesn't apply), and adds permissive CORS headers to its own response.

Usage:
    python3 proxy.py            # serves on http://localhost:8000
    # then in index.html set HAFAS_ENDPOINT to "http://localhost:8000/mgate"
"""
import http.server
import urllib.request

UPSTREAM = "https://reiseauskunft.insa.de/bin/mgate.exe"


class Handler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        query = self.path.split("?", 1)[1] if "?" in self.path else ""
        url = f"{UPSTREAM}?{query}" if query else UPSTREAM
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                status = resp.status
        except urllib.error.HTTPError as e:
            data = e.read()
            status = e.code
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass  # keep stdout quiet


if __name__ == "__main__":
    addr = ("localhost", 8000)
    print(f"Proxy listening on http://{addr[0]}:{addr[1]} -> {UPSTREAM}")
    http.server.HTTPServer(addr, Handler).serve_forever()
