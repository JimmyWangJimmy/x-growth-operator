from __future__ import annotations

import html
import re

from scripts.common import normalize_text


def clean_text(value: str) -> str:
    return " ".join(html.unescape(value or "").split())


def strip_leading_mentions(text: str) -> str:
    cleaned = clean_text(text)
    return re.sub(r"^(?:@\w+\s+)+", "", cleaned).strip()


def infer_theme(text: str) -> str:
    lowered = clean_text(text).lower()
    if any(token in lowered for token in ("memory", "markdown", "weights", "context", "knowledge")):
        return "memory"
    if any(token in lowered for token in ("marketplace", "persona", "workflow", "team", "playbook")):
        return "workflow-market"
    if any(token in lowered for token in ("security", "safeguard", "phishing", "destructive", "guardrail")):
        return "safety"
    if any(token in lowered for token in ("video", "slop vibe", "movie", "image")):
        return "media"
    if any(token in lowered for token in ("gpu", "profit", "cost", "bill", "margin")):
        return "economics"
    return "general"


def detect_stance(text: str) -> str:
    lowered = clean_text(text).lower()
    if "real money" in lowered or "profit" in lowered or "mrr" in lowered or "roi" in lowered:
        return "monetization"
    if "memory" in lowered or "markdown" in lowered or "weights" in lowered:
        return "memory"
    if "marketplace" in lowered or "workflow" in lowered or "persona" in lowered:
        return "workflow-market"
    if "security" in lowered or "safeguard" in lowered or "guardrail" in lowered:
        return "safety"
    if "video" in lowered or "movie" in lowered or "image" in lowered:
        return "media"
    return "general"


def extract_hooks(text: str) -> list[str]:
    cleaned = strip_leading_mentions(text)
    parts = re.split(r"[.!?]\s+", cleaned)
    hooks = [part.strip(" .") for part in parts if len(part.strip()) > 24]
    return hooks[:3]


def summarize_hook(hook: str) -> str:
    cleaned = strip_leading_mentions(hook)
    lowered = cleaned.lower()
    if "i use it" in lowered or "i use" in lowered:
        return "operators are describing repeatable real-world usage"
    if cleaned.startswith(("but ", "yes ", "no ", "and ")):
        return ""
    words = cleaned.split()
    if len(words) < 5:
        return ""
    return " ".join(words[:10]).rstrip(" ,.;:!?")


def concise_cta(cta: str) -> str:
    normalized = clean_text(cta)
    if not normalized:
        return ""
    return normalized[0].upper() + normalized[1:]


def mission_topic_label(mission: dict) -> str:
    for field in ("primary_topics", "watch_keywords"):
        values = mission.get(field, [])
        if isinstance(values, list):
            for value in values:
                cleaned = clean_text(str(value))
                if cleaned:
                    return cleaned
    goal = clean_text(mission.get("goal", ""))
    return goal or "this space"


def mission_audience_label(mission: dict) -> str:
    audience = mission.get("audience", [])
    if isinstance(audience, list) and audience:
        return clean_text(str(audience[0]))
    return "the right audience"


def mission_goal_style(mission: dict) -> str:
    goal = clean_text(mission.get("goal", "")).lower()
    if any(token in goal for token in ("lead", "signup", "pipeline", "sale", "revenue", "demo")):
        return "connect attention to proof and a concrete next step"
    if any(token in goal for token in ("trust", "credibility", "authority", "position")):
        return "show evidence, specificity, and follow-through"
    if any(token in goal for token in ("community", "engagement", "discussion", "conversation")):
        return "create useful discussion and stay present in the thread"
    if any(token in goal for token in ("awareness", "visibility", "reach", "discover")):
        return "earn attention with a clear point of view and timely follow-up"
    return "turn attention into repeatable outcomes"


def topic_specific_angle(theme: str, stance: str) -> str:
    if stance == "monetization":
        return "tie the conversation to measurable outcomes instead of vague interest"
    if theme == "memory":
        return "show how the idea changes actual decision-making, not just storage"
    if theme == "workflow-market":
        return "make the workflow repeatable instead of leaving it as a one-off insight"
    if theme == "safety":
        return "pair capability with clear controls and recovery paths"
    if theme == "economics":
        return "translate the shift into pricing, margin, or operating leverage"
    if theme == "media":
        return "connect the creative angle to why people will keep paying attention"
    return "turn the point of view into something specific, useful, and repeatable"


def build_reply(mission: dict, theme: str, stance: str, hooks: list[str], source: str, include_question: bool, cta: str) -> tuple[str, str]:
    topic_label = mission_topic_label(mission)
    audience_label = mission_audience_label(mission)
    goal_style = mission_goal_style(mission)
    anchor = summarize_hook(hooks[0]) if hooks else "that point"
    draft = (
        f"The key part is {anchor}. In {topic_label}, the accounts that win with {audience_label} are the ones that {goal_style}."
    )
    draft += f" The stronger move is to {topic_specific_angle(theme, stance)}."
    if include_question:
        draft += " What signal do you think matters most here?"
    if cta:
        draft += f" {cta}"
    rationale = f"Reply is favored because {source} already has momentum and the mission prefers timely participation."
    return draft, rationale


def build_quote(mission: dict, theme: str, stance: str, hooks: list[str], cta: str) -> tuple[str, str]:
    topic_label = mission_topic_label(mission)
    goal_style = mission_goal_style(mission)
    anchor = summarize_hook(hooks[0]) if hooks else "the core claim"
    draft = f"What this gets right: {anchor}. In {topic_label}, the stronger move is to {goal_style}."
    draft += f" That usually means you need to {topic_specific_angle(theme, stance)}."
    if cta:
        draft += f" {cta}"
    rationale = "Quote post is favored because the opportunity is strong but benefits from adding a distinct point of view."
    return draft, rationale


def build_post(mission: dict, theme: str, stance: str, hooks: list[str], cta: str) -> tuple[str, str]:
    topic_label = mission_topic_label(mission)
    audience_label = mission_audience_label(mission)
    goal_style = mission_goal_style(mission)
    draft = f"Hot take: in {topic_label}, growth compounds when teams {goal_style}."
    draft += f" The winners with {audience_label} will be the ones that {topic_specific_angle(theme, stance)}."
    if hooks:
        draft += f" The market signal here is {summarize_hook(hooks[0])}."
    if cta:
        draft += f" {cta}"
    rationale = "Standalone post is favored because the topic is aligned but not urgent enough to attach to a single source post."
    return draft, rationale


def build_post_from_signal(mission: dict, theme: str, stance: str, hooks: list[str], cta: str) -> tuple[str, str]:
    topic_label = mission_topic_label(mission)
    audience_label = mission_audience_label(mission)
    goal_style = mission_goal_style(mission)
    anchor = summarize_hook(hooks[0]) if hooks else ""
    anchor_text = anchor or "operators are starting to describe concrete, repeatable usage"
    draft = f"Seeing more evidence that in {topic_label}, {anchor_text}."
    draft += f" The teams that win with {audience_label} will be the ones that {goal_style}."
    draft += f" The practical edge is to {topic_specific_angle(theme, stance)}."
    if cta:
        draft += f" {cta}"
    rationale = "Standalone post is favored because the source signal is useful, but interaction readiness is too constrained for a direct reply or quote."
    return draft, rationale


def build_draft(mission: dict, opportunity: dict) -> tuple[str, str]:
    voice = mission.get("voice", "direct, clear, credible")
    cta = concise_cta(mission.get("cta", ""))
    source = opportunity.get("source_account", "the source")
    text = clean_text(opportunity.get("text", ""))
    action = opportunity.get("recommended_action", "observe")
    hints = opportunity.get("algorithm_hints", {})
    reply_window_open = bool(hints.get("reply_window_open"))
    interaction_readiness = hints.get("interaction_readiness", "open")
    theme = infer_theme(text)
    stance = detect_stance(text)
    hooks = extract_hooks(text)

    if action == "reply":
        draft, rationale = build_reply(mission, theme, stance, hooks, source, reply_window_open, cta)
    elif action == "quote_post":
        draft, rationale = build_quote(mission, theme, stance, hooks, cta)
    elif action == "post":
        if interaction_readiness in {"restricted", "thread_reply"}:
            draft, rationale = build_post_from_signal(mission, theme, stance, hooks, cta)
        else:
            draft, rationale = build_post(mission, theme, stance, hooks, cta)
    else:
        draft = ""
        rationale = "Observe is favored because the risk is too high or the fit is too weak."

    if hints.get("avoid_link_in_main_post"):
        rationale += " Keep any external link in a follow-up reply, not in the main post."

    notes = (
        f"Voice: {voice}. Theme: {theme}. Stance: {stance}. Source account: {source}. "
        f"Mission topic: {normalize_text(mission_topic_label(mission))}. Interaction readiness: {interaction_readiness}. "
        f"Source text summary: {text[:180]}"
    )
    return draft, f"{rationale} {notes}"
