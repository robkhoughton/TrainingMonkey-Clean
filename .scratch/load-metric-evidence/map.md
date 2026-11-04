Label: wayfinder:map

## Destination

Establish how well YTM's load metrics are backed by evidence: what the literature supports, where a confound distorts a metric, and how YTM's own hypotheses will be tested against athlete data. The effort ends when every load threshold in `app/Training_Metrics_Reference_Guide.md` is sourced, labelled as a product judgment call, or has a validation plan. This map makes no code changes.

## Notes

**Origin:** `docs/reference/intervals_icu_forum_review.md` (2026-11-04), a review of forum.intervals.icu threads on load, ACWR, and AI coaching.

**Settled framing:**
- Normalized Divergence is Rob's own hypothesis. No external literature supports or refutes it, and none is expected. Its evidence must come from YTM athlete data. The ACWR literature applies to divergence's inputs (rolling 7d/28d ratios), not to the hypothesis itself.
- Divergence reduces to `2(x−1)/(x+1)`, where `x = r_chronic / r_acute` and `r` is TRIMP per load mile. Volume cancels, so divergence measures the change in internal cost per unit of external work. See `CONTEXT.md` § Normalized Divergence.
- The single-stream ACWR bands and risk percentages in the reference guide are the part exposed to the Impellizzeri et al. 2020 critique.

**Related, outside this effort:** `.scratch/session-classification-intervals/issues/01-measure-interval-misclassification.md` covers HR lag in session *classification* (Z4+Z5 share). Ticket 01 here covers HR lag in *load* (TRIMP) and its effect on divergence. It reuses that ticket's interval-session set.

## Decisions so far

(none yet)

## Fog

- Whether YTM has enough athletes with long enough histories for any validation beyond user 1.
- Whether injury and pain data are logged consistently enough to serve as outcomes.
