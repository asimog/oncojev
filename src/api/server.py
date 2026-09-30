"""Thin, read-only application API over append-only research records.

The API is a projection of application read models. It has no mutation routes,
cannot admit evidence, and cannot bypass domain policy.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlparse

from src.application.service import ResearchApplication


class ResearchApiHandler(BaseHTTPRequestHandler):
    application: ResearchApplication
    server_version = "OncoJevAPI/1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        """Keep the API quiet; observability comes from records, not access logs."""

    def do_GET(self) -> None:  # noqa: N802 - stdlib signature
        segments = [unquote(part) for part in urlparse(self.path).path.split("/") if part]
        if segments == ["health"]:
            return self._json(200, self.application.health())
        if segments == ["api", "overview"]:
            return self._json(200, self.application.overview())
        if segments == ["api", "blocks"]:
            return self._json(200, {"blocks": list(self.application.blocks())})
        if segments == ["api", "research-memory"]:
            return self._json(200, {"research_memory": list(self.application.research_memory())})
        if len(segments) == 3 and segments[:2] == ["api", "blocks"]:
            return self._json(200, self.application.reconstruction(segments[2]).model_dump(mode="json"))
        if len(segments) == 4 and segments[:2] == ["api", "blocks"] and segments[3] == "reconstruction":
            return self._json(200, self.application.reconstruction(segments[2]).model_dump(mode="json"))
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - stdlib signature
        self._json(405, {"error": "read_only_api"})

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST

    def _json(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def create_server(
    application: ResearchApplication, host: str = "127.0.0.1", port: int = 8080
) -> ThreadingHTTPServer:
    handler = type("BoundResearchApiHandler", (ResearchApiHandler,), {"application": application})
    return ThreadingHTTPServer((host, port), handler)


def serve(application: ResearchApplication, host: str = "127.0.0.1", port: int = 8080) -> None:
    create_server(application, host, port).serve_forever()
