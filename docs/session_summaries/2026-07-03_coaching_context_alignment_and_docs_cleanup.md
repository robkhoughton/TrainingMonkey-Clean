# Conversation Summary: Coaching Context Alignment & Docs Cleanup
**Date**: 2026-07-03
**Session Focus**: Reconcile the `coaching_context/` LLM-runtime layer with the authoritative metrics guide, audit `docs/reference/`, then clean up the entire `docs/` tree.

---

## Main Objectives
- Verify `app/coaching_context/` is aligned with `app/Training_Metrics_Reference_Guide.md`.
- Check whether context/metrics overlooked or contradicted anything useful in `docs/reference/`.
- Clean up and reorganize the whole `docs/` directory.

## Key Discussions
- Two-layer model: `coaching_context/` (model-facing, interpretive) vs `Training_Metrics_Reference_Guide.md` (authoritative thresholds). Context yields to the guide when they diverge (per `.claude/rules/llm-determinism.md`).
- `docs/reference/` docs are the citation/source homes; audited for overlooked/contradictory/redundant content.

## Code Changes
- **`coaching_context/intensity_zones.md`**: dynamic-AeT framing (use injected `TODAY'S EFFECTIVE AeT`, band slides Path 2, lowered ceiling = recovery signal); Zone 5 fixed to "Above ~95% HRmax"; masters recovery buffer 72h→48h; new "Distribution Shifts By Phase" section.
- **`coaching_context/zone2_training.md`**, **`aerobic_assessment.md`**: dynamic-AeT (baseline vs daily effective value).
- **`llm_recommendations_module.py`**: wired `bone_health.md` into `_load_coaching_context()` gating (base period: race >56d or none); added `_context_index.md` + `fueling.md` + `bone_health.md` to `_COACHING_CONTEXT_FILES` validation.
- **`Training_Metrics_Reference_Guide.md`**: footnote on zone-distribution table (Build-phase steady state, modulates by phase).
- **`docs/` cleanup**: ~180 files → 54 live + 126 archived; new `docs/README.md` index; `docs/_archive/README.md`.

## Issues Identified
- Dynamic AeT (shipped feature) not reflected in context files (treated AeT as static) or the FAQ-generation reference docs.
- `bone_health.md` orphaned (never injected) despite Rob's osteopenia risk.
- Zone 5/4 boundary overlap error; masters buffer mismatch with guide.
- `docs/README.md` was upstream "AI Dev Tasks" boilerplate; ~150 stale/historical docs; misfiled dev/business docs.
- Anomaly: `docs/session_summaries/` vanished from working tree (external sync, not a run command); restored from HEAD — no loss.

## Solutions Implemented
- Reconciled all four context↔metrics misalignments; wired bone_health.
- Extracted phase-modulated intensity distribution (the one overlooked-useful item) into context + guide.
- Archived 3 raw Gemini notes (`docs/reference/_archive/`) and ~126 historical docs (`docs/_archive/`), all via `git mv` (reversible).
- Relocated lone-file docs: `dynamic_aet.md` → `reference/`, `COACHING_FRAMEWORK_GAPS.md` → `architecture/`.

## Decisions Made
- Archive (not hard-delete) stale docs; hard-delete only 2 junk files.
- Gate `bone_health.md` to base period (mirrors `muscular_endurance.md`).
- `docs/reference/` for athlete-facing explainers; `docs/architecture/` for roadmap/planning.

## Next Steps
- **Deferred**: refresh FAQ-gen docs `reference/TRAINING_PHILOSOPHY.md` + `reference/ATHLETE_MODEL_AND_MODEL_CONFIDENCE.md` for shipped dynamic AeT.
- Still-open architectural gap (unchanged): coaching context reaches only the daily recommendation — not agentic chat (~line 4321) or journal endpoint (`strava_app.py` ~line 6108).
- Optional: relocate/handle flagged misfiled `reference/` docs (`TMI_executive_summary.md`, `CODE_QUALITY_CHECK_TEMPLATE.md`).

## Technical Details
- Commits on master: `68aa557` (context↔metrics), `52b0ffe` (references audit), `7a76c01` (docs cleanup), `6402c3a` (doc relocations).
- `ADD_GOOGLE_ANALYTICS_GUIDE.md` is gitignored (GA id) — relocated on disk only.
- Pre-existing untouched working-tree changes: `aerobic_assessment_engine.py`, `db_utils.py`, `strava_app.py`, `SeasonPage.tsx`.
- No Dockerfile/frontend build needed; all changes are docs/prompt-context.
