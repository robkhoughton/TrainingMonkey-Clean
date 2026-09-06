# 03 — Specification Clarity score: compute and expose it

**What to build:** A second score, structurally different from Data Reliability — presence-based rather than decaying, since a season goal set on day one is just as clear as one set on day 200. Components: athlete profile completeness, season-goal completeness (race or non-race — see ticket 01), weekly-schedule presence, **`recommendation_style` presence (see below — moved here from the excluded bucket)**. Answers "do we know who this athlete is and what they're training for," not "is today's data trustworthy" — it does not decay and it does not gate Rx generation on its own — the season-goal piece specifically is one of three hard floors in the Adequate Context Gate (ticket 04, merged from the original ticket 05), on equal footing with training-load depth and recent journaling, not a softer or separate concern.

A non-race goal (ticket 01) must score as fully "clear" here, not as a degraded or partial case relative to a race goal.

**Correction from a review pass (2026-09-05) — `recommendation_style` was miscategorized:**
the original redesign decision grouped `recommendation_style` with `coaching_tone`/`coaching_style_spectrum` as "pure tone, no reliability relevance," excluded from both scores. That's wrong specifically for `recommendation_style`: it's the input to `get_adjusted_thresholds()` (llm_recommendations_module.py:3402), which sets the actual safety thresholds — `acwr_high_risk`, `divergence_overtraining`, `divergence_moderate_risk` — differently per style (`conservative`/`balanced`/`adaptive`/`aggressive`), confirmed by reading that function directly. It also silently defaults to `'balanced'` when unset, which can quietly loosen a conservative athlete's actual floor without them knowing their stated preference was never captured. Move it into this score's profile-completeness component. `coaching_tone` and `coaching_style_spectrum` are still correctly excluded — they're genuinely pure tone/phrasing with no threshold effect.

**Blocked by:** 01 (non-race season goals must exist so this score doesn't penalize non-racing users)

**Status:** done (2026-09-06)

**Implementation:** `app/specification_clarity.py`, `compute_specification_clarity(user_id)`. A race goal with a known distance scores 100 on the season_goal component; a race goal without distance scores 50; a non-race goal scores 100 flat (no equivalent field to penalize it for lacking, per the non-negotiable requirement below). `recommendation_style` is read as a raw column check, not via `get_user_recommendation_style()` (which masks NULL with `'balanced'` for threshold purposes — that masking must not leak into this score). Verified live: a fresh test user with only a non-race season_goals row scored 100 on that component, 0 elsewhere (empty profile/schedule/style) — confirmed no penalty for lacking race-specific fields.

- [x] Score computed per user from profile completeness, season-goal completeness (any type), weekly-schedule presence, and `recommendation_style` presence
- [x] A non-race season goal scores identically to an equivalently-complete race goal — no penalty for lacking race-specific fields (live-verified)
- [x] `recommendation_style` unset (silently defaulting to 'balanced' at the threshold layer) counts as missing here, not as complete
- [x] Component breakdown available (what's specifically missing)
- [x] Score does not decay over time the way Data Reliability does (pure presence checks, no half-life math)
