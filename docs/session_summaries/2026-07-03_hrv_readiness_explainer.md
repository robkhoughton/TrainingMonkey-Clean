# Conversation Summary: HRV vs Recovery — Readiness Card Explainer & Help Center Scoping
**Date**: 2026-07-03
**Session Focus**: Synthesize Morpheus HRV-vs-Recovery article, add user-facing explainer copy to the Training Readiness card, and scope adding HRV background content to the Help Center.

---

## Main Objectives
- Review and synthesize the Morpheus "HRV vs Recovery" support article.
- Draft and wire user-facing explanation copy for the Training Readiness card.
- Begin adding HRV "background" content to the tutorials/Help Center; assess reskin scope.

## Key Discussions
- **Article thesis**: "HRV is the input. Recovery is the decision." HRV = raw autonomic signal; Recovery = interpreted verdict (HRV-vs-baseline + RHR + history + load).
- Cross-referenced YTM's existing `readiness_engine.py` (z-score ANS model, four-state matrix). YTM is *ahead* of the article — notably the DEEP_HOLE / parasympathetic-overdrive case (HRV↑ + RHR↓ together = deep fatigue, not freshness), which the article's simpler framing would misread as a "recovery trend."
- Article validates YTM's architecture; no model changes needed.

## Code Changes
- **Files Modified**: `frontend/src/TodayPage.tsx`
- **Features Added** (in `TrainingReadinessCard`):
  - `READINESS_FALLBACK` map — deterministic per-state narratives (GREEN / CAUTION / DEEP HOLE / OVERREACHING); used when backend `readiness_narrative` is null.
  - `READINESS_INFO` — 3-paragraph explainer carrying the input-vs-decision framing.
  - `showInfo` state + "What's this?/Hide" toggle (no emoji, `aria-expanded`) revealing a collapsible explainer panel (BG/MUTED/FONT tokens, left-aligned).
  - Narrative line now: `p.readiness_narrative ?? READINESS_FALLBACK[key] ?? ''`.

## Issues Identified
- `HelpOverlay.tsx` (Help Center modal, ~730 lines) is legacy pre-brand UI: white modal, ~14 emoji section icons, App-Blue accents — conflicts with current brand (no emoji, dark/tactical registers). Sidebar requires an emoji `icon` per section, so a new section can't opt out cleanly.
- Difficulty/status badges use light pastels designed for white bg — would need WCAG-safe dark-bg variants in any reskin.
- `ContextualTutorialTriggers.tsx` (floating tip toast) is same legacy/emoji style — adjacent seam if reskinning modal only.
- Open Brain MCP calls failing (no output) at session end — likely Supabase free-tier auto-pause waking up.

## Solutions Implemented
- Readiness card (a) fallbacks and (b) collapsible explainer are implemented and in the working tree (not yet built/deployed).

## Decisions Made
- HRV "background" content = a new **Help section** in `HelpOverlay.tsx` (expository), not an interactive API-driven tutorial.
- Reskin scope assessed: **medium** — single self-contained file, all inline styles, no backend/data changes. Main risk is badge-contrast rework + verification surface, not complexity.

## Next Steps
- **User decision pending**: HRV section style — (1) match legacy modal, (2) brand-aligned section only, or (3) reskin whole modal. *Not yet chosen.*
- User runs build + copy (builds are user-only), then Playwright visual check of TodayPage (toggle open/closed, DEEP HOLE state) before any deploy.
- Confirm mock server wellness payload sets `readiness_state` (and null `readiness_narrative`) to exercise the fallback path on screen.
- Consider `ContextualTutorialTriggers.tsx` if modal reskin proceeds.

## Technical Details
- Card fallback wiring: `p.readiness_narrative ?? READINESS_FALLBACK[key] ?? ''` — backend narrative still wins; card never renders blank.
- States: `GREEN | YELLOW_SYMPATHETIC | YELLOW_PARASYMPATHETIC (DEEP HOLE) | RED | UNKNOWN`.
- Reference: `readiness_engine.py` — HRV 7d/30d, RHR 3d/60d z-scores; sleep + SpO2 modifiers.
