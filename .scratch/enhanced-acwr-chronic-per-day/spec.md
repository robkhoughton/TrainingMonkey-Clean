Status: ready-for-agent

# Enhanced ACWR: Chronic Average Per Day, Not Per Activity Row

## Problem Statement

The enhanced (exponential-decay) ACWR path produces acute and chronic averages in different
units. The acute average is per calendar day (7-day sum ÷ 7). The chronic average is per
activity row: Σ(w·load) ÷ Σw over every row in the chronic window, where w = e^(−decay × days_ago).
So the chronic average is off whenever a day doesn't have exactly one row:

- a day with several rows (a double session, or a `rest` placeholder row written alongside a
  real activity, as on user 1's 2026-09-19) adds extra weight to the denominator, which lowers
  the chronic average and inflates both ACWRs
- a day with no row has the opposite effect

Normalized Divergence is not affected: external and internal load share the same weights, so the
error cancels in the ratio. External and Internal ACWR are affected, and so are every threshold
read against them (`acwr_high_risk`, `acwr_undertraining`, the injury risk score's ACWR
contribution).

Only user 1 is assigned an enhanced configuration (`default_enhanced`: 42-day chronic period,
decay 0.05). Every other user is on the standard 28-day path, which sums by date and is correct.
On 2026-10-11, user 1's stored External ACWR was 0.61; with a per-day chronic average it would be
0.59. The error grows with the number of rows per day and can get large: user 1 logged 74 rows in
30 days in December 2025, and stored External ACWR read ~3.3 when the per-day value was ~1.3.

A dry run over user 1's 397 dates since the configuration was assigned (2025-09-09) found
External ACWR changes on 384 dates (max shift 2.27). Divergence changes too (max 0.072), but only
on pre-February-2026 dates whose stored values came from older code or stale inputs. From
February 2026 on, stored values match the per-row formula exactly. The recompute doesn't move the
athlete model's divergence calibration: no physical-distress days feed the breakdown threshold,
and the healthy-day changes are at high positive values that can't shift the P20 edge.

A second, dead defect sits next to it. The decay engine's own enhanced-ACWR method (and its
module-level convenience wrapper) divides the acute sum by the *number of activities* in the
window instead of by 7. Nothing in production calls it; production goes through the configuration
service, which divides by 7 correctly.

## Solution

The chronic average becomes a per-calendar-day exponentially weighted average:
Σ(w·load) ÷ Σ_{i=0}^{n−1} e^(−decay × i), with n = the configured chronic period. Days with no
row count as zero-load days, and multiple rows on one day add to that day's load instead of
adding weight. Acute and chronic are then both per-day, matching the standard path.

The dead engine method that divides acute by activity count is removed. It shouldn't be fixed,
because keeping it leaves a second, divergent enhanced-ACWR implementation for someone to call
later.

After the fix, recompute user 1's stored enhanced ACWR values over the full history, so the
dashboard and the athlete model's calibration don't mix the two definitions.

## Acceptance

- For the enhanced path, External/Internal ACWR are the same whether a day's load arrives as one
  row or several rows summing to the same total.
- A day with no row and a day with a single zero-load `rest` row give the same result.
- Normalized Divergence is unchanged (to rounding) for any history, since this fix touches only
  ACWR.
- User 1, 2026-10-11 fixture: External ACWR 0.59, Internal ACWR 0.69, divergence −0.143.
- No caller remains for the engine's activity-count enhanced-ACWR method.
- User 1's stored rows are recomputed, and a follow-up query confirms the change landed.

## Out of Scope

- Changing the default chronic period or decay rate.
- Rolling the enhanced configuration out to more users.
- Why a `rest` placeholder row gets written on a day that already has an activity (user 1,
  2026-09-19). That's a data-hygiene question for the rest-day writer; this fix makes the ACWR
  calculation robust to it either way.

## Related

- `.scratch/divergence-rest-projection/spec.md`: its divergence projection must use the
  athlete's configured ACWR method (standard 28-day or enhanced decay). Its numbers are
  unaffected by this fix because divergence ignores the chronic denominator.
