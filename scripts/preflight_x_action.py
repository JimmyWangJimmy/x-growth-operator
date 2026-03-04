from __future__ import annotations

import argparse
import json
import subprocess
from urllib.parse import urlparse

from common import load_json, write_json


def tweet_id_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if len(parts) >= 3 and parts[-2] == "status":
        return parts[-1]
    return None


def run_cli(args: list[str]) -> dict:
    completed = subprocess.run(
        ["node", "scripts/x_oauth_cli.js", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    raw = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0:
        raise SystemExit(raw or "X CLI command failed")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Failed to decode X CLI output: {exc}") from exc


def mentions_user(tweet: dict, username: str) -> bool:
    username = username.lower().lstrip("@")
    entities = tweet.get("entities") or {}
    mentions = entities.get("mentions") or []
    for mention in mentions:
        if isinstance(mention, dict) and str(mention.get("username", "")).lower() == username:
            return True
    return False


def assess_action(action: dict, me: dict, tweet: dict) -> tuple[str, list[str]]:
    action_type = action.get("action_type")
    reasons: list[str] = []
    reply_settings = (tweet.get("reply_settings") or "everyone").lower()
    my_user_id = str(me.get("id", ""))
    my_username = str(me.get("username", ""))
    target_author_id = str(tweet.get("author_id", ""))
    referenced = tweet.get("referenced_tweets") or []
    is_reply_tweet = any(ref.get("type") == "replied_to" for ref in referenced if isinstance(ref, dict))
    mentioned = mentions_user(tweet, my_username)

    if action_type == "reply":
        if is_reply_tweet and not mentioned and target_author_id != my_user_id:
            reasons.append("target tweet is itself part of a reply thread, and this account is not mentioned in that sub-conversation")
            return "block", reasons
        if reply_settings == "everyone":
            reasons.append("target tweet allows replies from everyone")
            return "allow", reasons
        if reply_settings == "mentionedusers":
            if mentioned:
                reasons.append("target tweet only allows mentioned users, and the account is mentioned")
                return "allow", reasons
            reasons.append("target tweet only allows mentioned users, and this account is not mentioned")
            return "block", reasons
        if reply_settings == "following":
            if target_author_id and target_author_id == my_user_id:
                reasons.append("reply is to the account's own tweet")
                return "allow", reasons
            reasons.append("target tweet only allows replies from followed accounts; cannot verify this via current preflight")
            return "block", reasons
        reasons.append(f"unrecognized reply_settings value: {reply_settings}")
        return "review", reasons

    if action_type == "quote_post":
        if is_reply_tweet and not mentioned and target_author_id != my_user_id:
            reasons.append("target tweet is a reply inside an active conversation, which has correlated with quote restrictions in current tests")
            return "block", reasons
        if reply_settings != "everyone":
            reasons.append(f"target tweet reply_settings is {reply_settings}, which correlates with quote restrictions in current tests")
            return "block", reasons
        reasons.append("target tweet is public and has no restrictive reply_settings signal")
        return "allow", reasons

    reasons.append("preflight not required for this action type")
    return "allow", reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight an X action to reduce avoidable 403 failures.")
    parser.add_argument("--action", default="data/action.json", help="Action JSON path.")
    parser.add_argument("--output", help="Optional output JSON path for the preflight result.")
    args = parser.parse_args()

    action = load_json(args.action)
    action_type = action.get("action_type")
    target_url = action.get("target_url", "")
    target_id = tweet_id_from_url(target_url)

    result = {
        "ok": True,
        "action_id": action.get("id"),
        "action_type": action_type,
        "target_url": target_url,
        "decision": "allow",
        "reasons": [],
    }

    if action_type not in {"reply", "quote_post"}:
        result["reasons"].append("No interaction preflight needed for this action type.")
    elif not target_id:
        result["ok"] = False
        result["decision"] = "block"
        result["reasons"].append("Target URL does not contain a tweet id.")
    else:
        me_payload = run_cli(["me"])
        tweet_payload = run_cli(["tweet", "--id", target_id])
        me = me_payload.get("user", {})
        tweet = tweet_payload.get("tweet", {})
        decision, reasons = assess_action(action, me, tweet)
        result["decision"] = decision
        result["reasons"] = reasons
        result["me"] = {
            "id": me.get("id"),
            "username": me.get("username"),
        }
        result["target_tweet"] = {
            "id": tweet.get("id"),
            "author_id": tweet.get("author_id"),
            "conversation_id": tweet.get("conversation_id"),
            "reply_settings": tweet.get("reply_settings"),
            "text": tweet.get("text", ""),
        }
        if decision == "block":
            result["ok"] = False

    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["decision"] != "block" else 2


if __name__ == "__main__":
    raise SystemExit(main())
