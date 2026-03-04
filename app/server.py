from __future__ import annotations

import json
import mimetypes
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.storage import LocalStateStore

APP_DIR = ROOT / "app"
STATIC_DIR = APP_DIR / "static"
DATA_DIR = ROOT / "data"
STORE = LocalStateStore(DATA_DIR)


def load_json_safe(name: str, default):
    payload = STORE.load_json(name, default=default)
    return payload if payload is not None else default


def load_execution_log(limit: int = 25) -> list[dict]:
    path = DATA_DIR / "execution_log.jsonl"
    if not path.exists():
        return []
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    events: list[dict] = []
    for raw in lines[-limit:]:
        try:
            events.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return list(reversed(events))


def load_generated_files() -> list[str]:
    if not DATA_DIR.exists():
        return []
    interesting = []
    for path in sorted(DATA_DIR.glob("*.json")):
        if path.name == ".gitkeep":
            continue
        interesting.append(path.name)
    if (DATA_DIR / "execution_log.jsonl").exists():
        interesting.append("execution_log.jsonl")
    return interesting


def build_dashboard_state() -> dict:
    scored = load_json_safe("opportunities_scored.json", {"items": []})
    plan = load_json_safe("action_plan.json", {"items": []})
    action = load_json_safe("action.json", {})
    return {
        "mission": load_json_safe("mission.json", {}),
        "memory": load_json_safe("memory.json", {}),
        "action_plan": plan,
        "current_action": action,
        "opportunities_scored": scored,
        "feedback_report": load_json_safe("feedback_report.json", {}),
        "execution_log": load_execution_log(),
        "generated_files": load_generated_files(),
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "XGrowthDashboard/1.0"

    def do_GET(self) -> None:  # noqa: N802
        self.handle_request(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self.handle_request(include_body=False)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def handle_request(self, *, include_body: bool) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        if parsed.path == "/api/state":
            self.respond_json(build_dashboard_state(), include_body=include_body)
            return
        if parsed.path == "/api/files":
            self.respond_json({"files": load_generated_files()}, include_body=include_body)
            return

        file_path = STATIC_DIR / ("index.html" if parsed.path == "/" else parsed.path.lstrip("/"))
        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        payload = file_path.read_bytes()
        mime_type, _ = mimetypes.guess_type(file_path.name)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def respond_json(self, payload: dict, *, include_body: bool = True) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        if include_body:
            self.wfile.write(encoded)


def main() -> int:
    host = "127.0.0.1"
    port = 8787
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
