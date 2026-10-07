# 04 — Lab/DEXA body-composition test entry

**What to build:** A user can manually log a body-composition/metabolic test
result — test date, test type, and whichever of measured BMR, body-fat
percentage/lean mass, or bone-density result the test provided — and see a
history of past entries.

**Blocked by:** 01

**Status:** ready-for-agent

- [ ] Entry form captures test date, test type, and the relevant subset of measured BMR / body-fat-or-lean-mass / bone-density fields for that type.
- [ ] Multiple entries over time are kept as history, never overwritten.
- [ ] Entry surface is hidden unless the user has opted into the nutrition module.
- [ ] No automatic sync attempted for this data — manual entry only, distinct from the daily wellness-sync pipeline.
