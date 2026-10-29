import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data, content_type="application/json; charset=utf-8"):
        body = data.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Test-Origin", "waf-test-site")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/":
            self.respond(200, (ROOT / "index.html").read_text(encoding="utf-8"), "text/html; charset=utf-8")
        elif url.path == "/health":
            self.respond(200, json.dumps({"status": "ok", "service": "waf-test-site"}))
        elif url.path == "/api/echo":
            # Echo as JSON only. No SQL execution, shell execution or HTML reflection.
            self.respond(200, json.dumps({
                "origin": "waf-test-site", "method": "GET", "path": url.path,
                "query": parse_qs(url.query, keep_blank_values=True),
                "host": self.headers.get("Host"),
                "forwarded_for": self.headers.get("X-Forwarded-For"),
                "forwarded_proto": self.headers.get("X-Forwarded-Proto"),
            }, ensure_ascii=False))
        else:
            self.respond(404, json.dumps({"error": "Not found"}))


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
