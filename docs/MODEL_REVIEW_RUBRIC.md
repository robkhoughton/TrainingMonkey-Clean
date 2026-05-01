# YTM Model Review Rubric

**Purpose:** Periodic audit to ensure model IDs are current and task routing remains optimal as Anthropic releases new models.

**Cadence:** Monthly. Model families release roughly every 6 months; minor version IDs update more frequently.

---

## Step 1 — Inventory All Model References

Search the codebase for every hardcoded model ID:

```bash
grep -rn "claude-" app/ --include="*.py" --include="*.json"
```

Expected locations:
| File | Variable | Task |
|---|---|---|
| `app/config.json` | `llm_settings.model` | DEFAULT_MODEL fallback |
| `app/config.json` | `llm_settings.model_sonnet` | Daily + weekly recommendations |
| `app/config.json` | `llm_settings.model_haiku` | Autopsy analysis |
| `app/config.json` | `llm_settings.model_opus` | Weekly comprehensive |
| `app/llm_recommendations_module.py` | `DEFAULT_MODEL` constant | Hardcoded fallback (masked by config) |
| `app/llm_recommendations_module.py` | `MODEL_SONNET`, `MODEL_HAIKU`, `MODEL_OPUS` | Hardcoded fallbacks (masked by config) |
| `app/chat/service.py` | `CHAT_MODEL` | In-app chat responses |

---

## Step 2 — Check Currency Against Anthropic Releases

Check [https://docs.anthropic.com/en/docs/about-claude/models](https://docs.anthropic.com/en/docs/about-claude/models) for the latest model IDs.

**As of 2026-03-29:**
| Tier | Current ID |
|---|---|
| Haiku | `claude-haiku-4-5-20251001` |
| Sonnet | `claude-sonnet-4-6` |
| Opus | `claude-opus-4-6` |

Flag any model ID that:
- Uses a version number below the latest major (e.g., 3.x when 4.x exists)
- Uses an outdated date suffix (e.g., `-20241022` when `-20251001` is available)
- Is not the current recommended ID per the Anthropic docs

---

## Step 3 — Review Task Routing Logic

Current routing in `llm_recommendations_module.py → get_model_for_task()`:

| Task | Model | Rationale |
|---|---|---|
| `daily` | Sonnet | Quality coaching output — worth the cost |
| `autopsy` | Haiku | Structured parsing of workout data — speed + cost |
| `weekly` | Sonnet | Strategic planning — needs reasoning quality |
| `weekly_comprehensive` | Opus | Full season synthesis — max quality justified |
| `chat` (in-app) | Haiku | Conversational, low latency, many turns |

**Review questions:**
- Has Haiku quality improved enough to replace Sonnet for daily recommendations?
- Is Opus still needed for weekly_comprehensive, or has Sonnet closed the gap?
- Are there new task types that need routing decisions?

---

## Step 4 — Evaluate Extended Thinking

`config.json` has `"use_extended_thinking": false`.

Review quarterly: Is extended thinking now worth enabling for `weekly_comprehensive`?
Criteria: latency acceptable, output quality measurably better, cost justified by user tier.

---

## Step 5 — Apply Fixes

1. Update `config.json` model IDs (primary source of truth)
2. Update hardcoded constants in `llm_recommendations_module.py` (fallback alignment)
3. Update `chat/service.py` `CHAT_MODEL` (not config-driven — must be updated manually)
4. Test: trigger a daily recommendation and confirm `model_used` field in DB reflects new IDs
5. Commit and deploy

---

## Change Log

| Date | Change | Reviewer |
|---|---|---|
| 2026-03-29 | Initial audit. Updated `config.json` default from `claude-sonnet-4-5-20250929` → `claude-sonnet-4-6`. Updated `chat/service.py` from `claude-3-5-haiku-20241022` → `claude-haiku-4-5-20251001`. Updated `DEFAULT_MODEL` constant fallback. | Claude / Rob |
| 2026-05-01 | Anthropic docs page unavailable (HTTP 403) — no model ID changes made per rubric policy. Additional finding: `app/config.json` does not exist; fallback constants in `llm_recommendations_module.py` are the live source of truth. Current IDs: `claude-sonnet-4-6` (default/Sonnet), `claude-haiku-4-5-20251001` (Haiku), `claude-opus-4-6` (Opus), `claude-haiku-4-5-20251001` (chat). Verify and update against docs next cycle. | Scheduled agent |
