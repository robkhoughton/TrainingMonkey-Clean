# Coaching Context Library

Files in this directory are injected state-gated into LLM prompts at inference time. They are written **for the model** — compact, imperative assertions, not human narrative.

The Dockerfile copies this directory wholesale. **No Dockerfile change is needed when adding new files.**

---

## Current Files and Gating Conditions

Gating logic lives in `_load_coaching_context()` in `llm_recommendations_module.py`.

| File | Injected when |
|------|---------------|
| `_context_index.md` | Always — injected first; LLM orientation and conflict priority |
| `trail_specifics.md` | Always |
| `intensity_zones.md` | Always |
| `strength_integration.md` | Always |
| `neuromuscular.md` | Always — hill sprints, strides principle, overstriding form |
| `fueling.md` | Always — carb timing for hard vs. easy sessions |
| `readiness.md` | Readiness state != GREEN |
| `periodization.md` | Race ≤ 28 days away |
| `zone2_training.md` | Race > 28 days away, or no race goal |
| `aerobic_assessment.md` | Race > 28 days away, or no race goal |
| `muscular_endurance.md` | Race > 56 days away, or no race goal |
| `bone_health.md` | Race > 56 days away, or no race goal |

---

## Adding a New File — 2 Required Steps

1. **Write** `app/coaching_context/<topic>.md` — directive assertions, model-facing tone
2. **Add a gating condition** to `_load_coaching_context()` in `llm_recommendations_module.py` with a rationale comment

There is no longer a third "verify every call site" step for the daily recommendation.
`_load_coaching_context()` is called once, inside `assemble_daily_context()` — the shared
context seam every daily prompt builder assembles through — so a newly gated file reaches
those paths by construction. `app/tests/test_daily_context.py` fails the build if a builder
stops consuming a shared signal.

This step used to read "verify injection reaches all active LLM call sites" and then list
three, silently omitting `create_autopsy_informed_decision_prompt()` — which is exactly how
the journal-triggered path (the most frequently hit one) ended up receiving none of these
files. A manual checklist of call sites is the failure mode, not the fix.

**Still outside the seam:** `generate_recommendations_agentic()` (feature-flag gated) and
`generate_activity_autopsy_enhanced()` (the post-workout autopsy, a different prompt) each
call `_load_coaching_context()` themselves. Check those two directly until they are
migrated.

---

## Writing Guidelines

- **Audience is the model, not a human.** Strip narrative. Keep assertions.
- **Imperative voice.** "Do X when Y" not "Athletes should consider X."
- **No source citations or background theory** — those belong in `docs/reference/`.
- **Include thresholds and decision rules explicitly** — the model cannot infer them.
- **Never cross-reference other context files by name.** The LLM does not know which files are present. If a rule requires context from another file, repeat the relevant constraint inline. A reference to `zone2_training.md` is a dangling pointer when that file is gated out.
- **Write as if this file is the only one injected.** Each directive must stand alone.

---

## Cross-file Dependencies and Known Overlaps

When editing any file, check its overlap partners for consistency. Conflicts here are invisible to the LLM — it receives both and must reconcile them.

| File | Overlapping topic | Partner files to check |
|------|-------------------|------------------------|
| `intensity_zones.md` | Zone 2 ceiling / VT1 | `zone2_training.md`, `readiness.md` |
| `intensity_zones.md` | Strides classification | `neuromuscular.md` |
| `intensity_zones.md` | Hard session intensity defaults | `readiness.md` (readiness overrides when present) |
| `fueling.md` | Zone 4–5 session prescription | `intensity_zones.md` |
| `strength_integration.md` | CNS/ANS fatigue load | `readiness.md`, `intensity_zones.md` |

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
