from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import normalize_text, utc_now_iso, write_json


SECTION_ALIASES = {
    "goals": "goals",
    "goal": "goals",
    "audience": "audience",
    "target audience": "audience",
    "voice": "voice",
    "tone": "voice",
    "priority topics": "priority topics",
    "topics": "priority topics",
    "focus topics": "priority topics",
    "watch keywords": "watch keywords",
    "keywords": "watch keywords",
    "watch accounts": "watch accounts",
    "accounts": "watch accounts",
    "watchlist": "watch accounts",
    "banned topics": "banned topics",
    "avoid": "banned topics",
    "preferred cta": "preferred cta",
    "cta": "preferred cta",
    "call to action": "preferred cta",
    "risk tolerance": "risk tolerance",
    "risk": "risk tolerance",
}

TOPIC_HINTS = (
    "ai",
    "agent",
    "agents",
    "beauty",
    "b2b",
    "climate",
    "commerce",
    "community",
    "creator",
    "devtools",
    "education",
    "enterprise",
    "fashion",
    "fintech",
    "fitness",
    "health",
    "infra",
    "ingredient",
    "launch",
    "local",
    "luxury",
    "marketplace",
    "media",
    "parenting",
    "productivity",
    "refillable",
    "saas",
    "security",
    "skincare",
    "software",
    "sustainable",
    "wellness",
    "workflow",
)


def dedupe_keep_order(values: list[str], *, lower: bool = True) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = normalize_text(value)
        if not cleaned:
            continue
        key = cleaned.lower() if lower else cleaned
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def split_phrase_list(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    normalized = re.sub(r"\band\b", ",", normalized, flags=re.IGNORECASE)
    parts = [part.strip(" .,:;") for part in normalized.split(",")]
    return [part for part in parts if part]


def parse_sections(raw_text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"summary": []}
    current = "summary"

    for line in raw_text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower().rstrip(":")
        canonical = SECTION_ALIASES.get(lowered)
        if canonical:
            current = canonical
            sections.setdefault(current, [])
            continue
        if stripped.startswith("- "):
            sections.setdefault(current, []).append(stripped[2:].strip())
        elif stripped:
            sections.setdefault(current, []).append(stripped)

    return sections


def first_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", normalize_text(text))
    return parts[0] if parts else normalize_text(text)


def compact_name(text: str) -> str:
    sentence = first_sentence(text).lstrip("# ").strip()
    words = sentence.split()
    if len(words) <= 8:
        return sentence
    return " ".join(words[:8]).rstrip(" ,.;:!?")


def find_goal(summary: str) -> str:
    patterns = [
        r"(?:the goal(?: over [^.]*)? is to|goal is to)\s+([^.!?]+)",
        r"(?:we want to|we need to|we're trying to|we are trying to)\s+([^.!?]+)",
        r"(?:increase|grow|drive|earn|build|improve)\s+([^.!?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, summary, flags=re.IGNORECASE)
        if match:
            return normalize_text(match.group(0)).rstrip(".")
    return first_sentence(summary)


def find_risk(summary: str) -> str:
    match = re.search(r"risk tolerance should stay (low|medium|high)", summary, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"\b(low|medium|high)\s+risk tolerance\b", summary, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    if "stay conservative" in summary.lower():
        return "low"
    return "medium"


def find_cta(summary: str) -> str:
    patterns = [
        r"(?:steer readers toward|invite readers to|encourage people to)\s+([^.!?]+)",
        r"(?:cta is to|call to action is to)\s+([^.!?]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, summary, flags=re.IGNORECASE)
        if match:
            phrase = normalize_text(match.group(0)).rstrip(".")
            return phrase[0].upper() + phrase[1:] if phrase else ""
    return ""


def find_voice(summary: str) -> list[str]:
    match = re.search(r"(?:voice|tone)\s+(?:should|to)?\s*(?:feel|be)?\s*([^.!?]+)", summary, flags=re.IGNORECASE)
    if match:
        raw = match.group(1)
        raw = re.sub(r"^(like|as)\s+", "", raw.strip(), flags=re.IGNORECASE)
        return dedupe_keep_order(split_phrase_list(raw))
    return []


def find_topics(summary: str) -> list[str]:
    patterns = [
        r"(?:monitor discussions around|watch discussions around|focus on|prioritize|priority topics include)\s+([^.!?]+)",
        r"(?:topics include|keywords include)\s+([^.!?]+)",
    ]
    results: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, summary, flags=re.IGNORECASE):
            results.extend(split_phrase_list(match.group(1)))

    if results:
        return dedupe_keep_order(results)

    candidates: list[str] = []
    lowered = summary.lower()
    for phrase in re.findall(r"\b[a-z][a-z0-9-]*(?:\s+[a-z0-9-]+){0,3}\b", lowered):
        phrase = phrase.strip()
        if any(hint in phrase for hint in TOPIC_HINTS):
            candidates.append(phrase)
    return dedupe_keep_order(candidates)[:8]


def find_accounts(summary: str) -> list[str]:
    accounts = re.findall(r"@([A-Za-z0-9_]{2,30})", summary)
    text_matches = re.search(r"(?:keep an eye on)\s+([^.!?]+)", summary, flags=re.IGNORECASE)
    text_accounts: list[str] = []
    if text_matches:
        for part in split_phrase_list(text_matches.group(1)):
            normalized = part.strip()
            if " " not in normalized and 2 <= len(normalized) <= 30:
                text_accounts.append(normalized.lstrip("@"))
    return dedupe_keep_order(accounts + text_accounts)


def find_audience(summary: str) -> list[str]:
    patterns = [
        r"(?:among|for)\s+([^.!?]+?)(?:\s+who\b|\.|,)",
        r"(?:target audience is|audience is)\s+([^.!?]+)",
    ]
    results: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, summary, flags=re.IGNORECASE):
            chunk = match.group(1)
            if len(chunk.split()) < 2:
                continue
            results.extend(split_phrase_list(chunk))
    filtered = [
        item for item in dedupe_keep_order(results)
        if "launch" not in item.lower() and len(item.split()) >= 2
    ]
    return filtered[:6]


def find_banned_topics(summary: str) -> list[str]:
    patterns = [
        r"(?:avoid|do not touch|don't touch|never touch)\s+([^.!?]+)",
        r"(?:stay away from)\s+([^.!?]+)",
    ]
    results: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, summary, flags=re.IGNORECASE):
            results.extend(split_phrase_list(match.group(1)))
    return dedupe_keep_order(results)


def fill_from_freeform(sections: dict[str, list[str]], raw_text: str) -> dict[str, list[str]]:
    summary = normalize_text(" ".join(sections.get("summary", [])) or raw_text)
    filled = {key: list(value) for key, value in sections.items()}

    if not filled.get("goals"):
        filled["goals"] = [find_goal(summary)]
    if not filled.get("audience"):
        filled["audience"] = find_audience(summary)
    if not filled.get("voice"):
        filled["voice"] = find_voice(summary)
    if not filled.get("priority topics"):
        filled["priority topics"] = find_topics(summary)
    if not filled.get("watch keywords"):
        filled["watch keywords"] = list(filled.get("priority topics", []))
    if not filled.get("watch accounts"):
        filled["watch accounts"] = find_accounts(summary)
    if not filled.get("banned topics"):
        filled["banned topics"] = find_banned_topics(summary)
    if not filled.get("preferred cta"):
        cta = find_cta(summary)
        filled["preferred cta"] = [cta] if cta else []
    if not filled.get("risk tolerance"):
        filled["risk tolerance"] = [find_risk(summary)]
    return filled


def mission_from_text(raw_text: str) -> dict:
    sections = fill_from_freeform(parse_sections(raw_text), raw_text)
    summary = " ".join(sections.get("summary", []))
    goals = dedupe_keep_order(sections.get("goals", []))
    audience = dedupe_keep_order(sections.get("audience", []))
    voice = dedupe_keep_order(sections.get("voice", []))
    topics = dedupe_keep_order(sections.get("priority topics", []))
    keywords = dedupe_keep_order(sections.get("watch keywords", []))
    accounts = dedupe_keep_order(sections.get("watch accounts", []))
    banned = dedupe_keep_order(sections.get("banned topics", []))
    cta = " ".join(dedupe_keep_order(sections.get("preferred cta", [])))
    risk_tolerance = normalize_text(" ".join(sections.get("risk tolerance", ["medium"]))).lower()

    headline = sections.get("summary", ["Untitled mission"])[0].lstrip("# ").strip()
    if headline and len(headline.split()) > 12:
        headline = compact_name(headline)
    goal = goals[0] if goals else normalize_text(summary)

    mission = {
        "name": headline or "Untitled mission",
        "goal": goal or "Grow targeted X awareness",
        "account_handle": "",
        "audience": audience,
        "voice": ", ".join(voice) if voice else "direct, clear, credible",
        "primary_topics": topics,
        "watch_keywords": keywords or topics,
        "watch_accounts": accounts,
        "banned_topics": banned,
        "cta": cta or "Invite qualified readers to learn more",
        "risk_tolerance": risk_tolerance if risk_tolerance in {"low", "medium", "high"} else "medium",
        "autonomy_mode": "review",
        "source_summary": normalize_text(summary),
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
    }
    return mission


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a mission.json from a brief or prompt.")
    parser.add_argument("--doc", help="Path to a source brief or uploaded document text export.")
    parser.add_argument("--prompt", help="Inline natural language mission prompt.")
    parser.add_argument("--mission", default="data/mission.json", help="Output mission JSON path.")
    args = parser.parse_args()

    if not args.doc and not args.prompt:
        parser.error("Provide either --doc or --prompt.")

    raw_text = args.prompt or Path(args.doc).read_text(encoding="utf-8")
    mission = mission_from_text(raw_text)
    output_path = write_json(args.mission, mission)

    print(f"Wrote mission to {output_path}")
    print(f"Mission goal: {mission['goal']}")
    print(f"Watching {len(mission['watch_accounts'])} accounts and {len(mission['watch_keywords'])} keywords")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
