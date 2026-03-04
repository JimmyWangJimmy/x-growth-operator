from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCRIPTS_DIR = ROOT / "scripts"


def load_local_env() -> Path | None:
    env_path = SCRIPTS_DIR / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
    return env_path


def ensure_parent(path: str | os.PathLike[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def load_json(path: str | os.PathLike[str]) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | os.PathLike[str], payload: Any) -> Path:
    target = ensure_parent(path)
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return target


def append_jsonl(path: str | os.PathLike[str], payload: Any) -> Path:
    target = ensure_parent(path)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return target


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().split())


def mission_focus_terms(mission: dict[str, Any], limit: int = 8) -> list[str]:
    phrases: list[str] = []
    for field in ("primary_topics", "watch_keywords", "audience"):
        value = mission.get(field, [])
        if isinstance(value, list):
            phrases.extend(normalize_text(str(item)) for item in value if normalize_text(str(item)))

    seen: set[str] = set()
    ordered: list[str] = []
    for phrase in phrases:
        lowered = phrase.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(phrase)
        if len(ordered) >= limit:
            break
    return ordered


def mission_search_query(mission: dict[str, Any], limit: int = 6) -> str:
    phrases = mission_focus_terms(mission, limit=limit)
    if not phrases:
        fallback = normalize_text(mission.get("goal", ""))
        if fallback:
            phrases = [fallback]

    query_parts: list[str] = []
    for phrase in phrases[:limit]:
        if " " in phrase:
            query_parts.append(f'"{phrase}"')
        else:
            query_parts.append(phrase)
    return " OR ".join(query_parts)


def mission_markers(mission: dict[str, Any]) -> set[str]:
    markers: set[str] = set()
    handle = normalize_text(str(mission.get("account_handle", ""))).lower().lstrip("@")
    if handle:
        markers.add(handle)
        markers.add(f"@{handle}")

    for phrase in mission_focus_terms(mission, limit=12):
        lowered = phrase.lower()
        if len(lowered) >= 3:
            markers.add(lowered)
        for token in lowered.replace("/", " ").replace("-", " ").split():
            token = token.strip()
            if len(token) >= 4:
                markers.add(token)
    return markers
