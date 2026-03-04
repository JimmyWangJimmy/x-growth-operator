# X Growth Operator

`X Growth Operator` is an OpenClaw-style skill for running review-first X growth workflows.

It turns a brief into a structured mission, pulls live opportunities from X, ranks them, drafts posts or interactions, and can execute approved actions through official X OAuth credentials.

## What It Does

- Parse a brief or prompt into a reusable mission
- Pull opportunities from Desearch, sample JSON, or manual surf notes
- Score opportunities for relevance, urgency, and risk
- Draft `post`, `reply`, or `quote_post` actions
- Execute approved actions through the official X API
- Persist an audit trail and lightweight memory loop

## Skill Layout

- `SKILL.md`: skill entrypoint and operating rules
- `agents/openai.yaml`: UI metadata
- `scripts/`: workflow, scoring, and execution scripts
- `references/`: mission schema and scoring reference
- `examples/`: sample briefs, notes, and opportunity data

## Install

Clone the repo or drop the packaged skill folder into your local skills directory.

Install Node dependencies:

```bash
cd scripts
npm install
```

Create `scripts/.env` from `scripts/.env.example` and fill:

- `X_API_KEY`
- `X_API_SECRET`
- `X_ACCESS_TOKEN`
- `X_ACCESS_TOKEN_SECRET`
- `DESEARCH_API_KEY`

If you need a proxy for X, also set:

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `ALL_PROXY`
- `NO_PROXY`

## Quick Start

Build a mission:

```bash
python3 scripts/ingest_goal.py \
  --doc examples/brand_brief.md \
  --mission data/mission.json
```

Search live X and build a ranked plan:

```bash
python3 scripts/live_search_and_plan.py \
  --mission data/mission.json \
  --query "openclaw OR local agent OR coding agent" \
  --count 10
```

Draft one action:

```bash
python3 scripts/propose_action.py \
  --mission data/mission.json \
  --opportunities data/opportunities_scored.json \
  --opportunity-id YOUR_OPPORTUNITY_ID \
  --output data/action.json
```

Execute an approved action:

```bash
python3 scripts/execute_action.py \
  --mission data/mission.json \
  --action data/action.json \
  --log data/execution_log.jsonl \
  --approved \
  --mode x-api
```

## Current Status

What works today:

- Mission ingestion
- Live X search through Desearch
- Opportunity scoring and action planning
- Approved original post execution through X OAuth
- Local execution logs and memory updates

Current limits:

- `reply` and `quote_post` can be rejected by X conversation permissions
- Opportunity filtering is still tuned for review-first operation, not full autonomy

## Package The Skill

Build a clean bundle without secrets or generated state:

```bash
python3 scripts/build_skill_bundle.py
```

This writes:

`dist/x-growth-operator-skill.zip`

## Next

The roadmap for turning this skill into a larger product is in `ROADMAP.md`.
