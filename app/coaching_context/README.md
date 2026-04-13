# Coaching Context Library

Files in this directory are injected state-gated into LLM prompts at inference time. They are written **for the model** — compact, imperative assertions, not human narrative.

The Dockerfile copies this directory wholesale. **No Dockerfile change is needed when adding new files.**

---

## Current Files and Gating Conditions

Gating logic lives in `_load_coaching_context()` in `llm_recommendations_module.py`.

| File | Injected when |
|------|---------------|
| `trail_specifics.md` | Always |
| `intensity_zones.md` | Always |
| `strength_integration.md` | Always |
| `neuromuscular.md` | Always — hill sprints, strides principle, overstriding form |
| `readiness.md` | Readiness state != GREEN |
| `periodization.md` | Race ≤ 28 days away |
| `zone2_training.md` | Race > 28 days away, or no race goal |
| `aerobic_assessment.md` | Race > 28 days away, or no race goal |
| `muscular_endurance.md` | Race > 56 days away, or no race goal |

---

## Adding a New File — 3 Required Steps

1. **Write** `app/coaching_context/<topic>.md` — directive assertions, model-facing tone
2. **Add a gating condition** to `_load_coaching_context()` in `llm_recommendations_module.py` with a rationale comment
3. **Verify injection reaches all active LLM call sites:**
   - Daily recommendation: `create_enhanced_prompt_with_tone()`
   - Agentic chat: `llm_recommendations_module.py` ~line 4321
   - Journal endpoint: `strava_app.py` ~line 6108

---

## Writing Guidelines

- **Audience is the model, not a human.** Strip narrative. Keep assertions.
- **Imperative voice.** "Do X when Y" not "Athletes should consider X."
- **No source citations or background theory** — those belong in `docs/reference/`.
- **Include thresholds and decision rules explicitly** — the model cannot infer them.

---

## Paired Reference Documents

Each context file has a human-readable counterpart in `docs/reference/` with source URLs, background theory, and full tables. Wiki-links connect them.

| Context file | Reference doc |
|---|---|
| `zone2_training.md` | `docs/reference/ZONE_2_PROTOCOL.md` |
| `muscular_endurance.md` | `docs/reference/MUSCULAR_ENDURANCE_PROTOCOL.md` |
| `neuromuscular.md` | `docs/reference/NEUROMUSCULAR_context.md` |
| `aerobic_assessment.md` | `docs/reference/AEROBIC_ASSESSMENT_context.md` |

When adding new protocol coverage, create both files.

---

## What This Is Not

- Not a task tracker
- Not a place for human-readable training guides
- Not a substitute for `app/Training_Metrics_Reference_Guide.md` (developer threshold reference)
