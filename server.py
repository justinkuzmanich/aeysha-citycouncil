#!/usr/bin/env python3
"""
Local development server for Corio for Concord website.
Serves static files and provides a read/write API for the endorsements CMS.

Usage: python server.py
Then open: http://localhost:3000
Admin panel: http://localhost:3000/admin.html
"""

import http.server
import json
import os
import urllib.parse
from pathlib import Path

PORT = 3000
BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "endorsements.json"

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css; charset=utf-8",
    ".js":   "application/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2":"font/woff2",
}


class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"  {self.command} {self.path} → {args[1]}")

    # ── GET ────────────────────────────────────────────────────────────────

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/endorsements":
            self._send_json(200, json.loads(DATA_FILE.read_text("utf-8")))
            return

        # Static file serving
        if path == "/" or path == "":
            path = "/index.html"

        file_path = BASE_DIR / path.lstrip("/")

        if not file_path.exists() or not file_path.is_file():
            self._send_text(404, "404 Not Found")
            return

        ext = file_path.suffix.lower()
        content_type = MIME_TYPES.get(ext, "application/octet-stream")
        self._send_file(200, content_type, file_path.read_bytes())

    # ── POST ───────────────────────────────────────────────────────────────

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path

        if path == "/api/endorsements":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                DATA_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")
                self._send_json(200, {"ok": True})
            except Exception as e:
                self._send_json(400, {"ok": False, "error": str(e)})
            return

        self._send_text(404, "404 Not Found")

    # ── Helpers ────────────────────────────────────────────────────────────

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._send_file(status, "application/json; charset=utf-8", body)

    def _send_text(self, status, text):
        self._send_file(status, "text/plain; charset=utf-8", text.encode("utf-8"))

    def _send_file(self, status, content_type, data: bytes):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    os.chdir(BASE_DIR)
    server = http.server.HTTPServer(("", PORT), Handler)
    print(f"\n  Site:   http://localhost:{PORT}")
    print(f"  Admin:  http://localhost:{PORT}/admin.html\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
