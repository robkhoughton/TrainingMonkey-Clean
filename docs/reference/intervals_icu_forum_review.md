# intervals.icu Forum Review: Relevance to YTM

Date: 2026-11-04
Scope: forum.intervals.icu threads on training load, ACWR, trail running, decoupling, readiness, and AI coaching tools. Forum posts are user and developer claims, not validated evidence. Most threads were read in part, not in full.

## Summary

The forum largely supports YTM's architecture. The design users ask for (deterministic statistics with LLM interpretation, elevation-aware trail load, a restrained daily decision) is already being built by community projects such as Section 11 and athletedata.health. intervals.icu itself has no internal-versus-external load comparison, so divergence is open ground. The scientific challenges to watch are the ACWR literature and HR-lag undercounting of internal load on short intervals. The strategic risk is commoditization: an official intervals.icu MCP server is at the spec stage.

## Support

### Deterministic computation, LLM interpretation
- [Section 11](https://forum.intervals.icu/t/section-11-open-protocol-for-ai-endurance-coaching-chatgpt-claude-grok-mistral/120602) is an open protocol that computes CTL/ATL/TSB, phase detection, and hard-day counts in a sync script, puts the signals in tiers ("Secondary never overrides primary readiness"), and has a safety rule ("HRV and sleep never recommend DNS"). The LLM interprets the precomputed JSON. This matches categories 1 and 2 in `.claude/rules/llm-determinism.md`.
- A heavy Section 11 user reports that "progression pathways are not applied correctly by the AI coach." This is evidence that a rule stated only in the prompt does not hold, and it supports enforcing rules after generation (`enforce_safety_floor`).
- In [The AI coach we (self-coached athletes) want](https://forum.intervals.icu/t/the-ai-coach-we-self-coached-athletes-want/116591), a user asks for "code for statistics, AI for interpretation" and describes existing MCP servers as thin wrappers around the API.

### Trail load needs elevation
- [Customized training load (for trail running)](https://forum.intervals.icu/t/customized-training-load-for-trail-running/12738): on a 33 km run with 2,100 m of gain, power load was 169 and HR load was 306. HR and power load are described as accurate on flat road but blind to climbing. The developer's answer is gradient-adjusted pace or editing the load by hand. YTM's load miles answer this directly.

### Internal versus external load as separate signals
- [Run training load priority: HR over pace?](https://forum.intervals.icu/t/run-training-load-priority-hr-over-pace/16629): pace or power load "will be the same regardless of your state of recovery because it measures output," while HR load can rise with fatigue. intervals.icu asks the user to pick one load source by priority and never computes the gap between them. YTM's divergence is this gap, measured over time.

### Restraint and personalization
- Recurring complaints about AI coaches are generic advice (default 80/20), verbosity, repetitive plans, and unsolicited messages. athletedata.health added deduplication and a "suppress responses" option after users found it spammy ([thread](https://forum.intervals.icu/t/your-ai-coach-messages-you-first-intervals-icu-garmin-whoop-oura/126280)).
- In the [AI tools comparison thread](https://forum.intervals.icu/t/any-reviews-or-comparisons-of-the-wealth-of-ai-tools-for-intervals/123739), one user says hosted AI coach chat is "worse than if I just fed the same data to ChatGPT or Claude manually." Another argues that subscription tools are pushed toward cheaper models and limited context.
- These complaints support YTM's single daily Rx and its learning from autopsies of the athlete's own responses.

## Contradiction and Caution

### The ACWR literature
- The forum's [ACWR thread](https://forum.intervals.icu/t/acwr-option-in-custom-chart/5812) uses population bands (below 0.8 under-training, 0.8–1.3 safe, above 1.5 red).
- Critiques: [Impellizzeri et al. 2020](https://research.tees.ac.uk/en/publications/the-acute-to-chronic-workload-ratio-an-inaccurate-scaling-index-f/) argues ACWR is an inaccurate scaling index and should be dropped as an injury metric. A [Bayesian analysis](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9572878/) found internal-load ACWR no better than a synthetic ACWR built with a random denominator.
- How the critique applies to YTM:
  - **Divergence.** It largely misses. Divergence reduces to `2(x−1)/(x+1)`, where `x = r_chronic / r_acute` and `r` is TRIMP per load mile. Volume cancels, so divergence measures the change in internal cost per unit of external work, not a workload spike. The critique's main target, ACWR as an injury predictor from a load spike, is not what divergence claims.
  - **Divergence, mechanically.** It still applies in part. Divergence remains a ratio of rolling ratios. The critique's mechanical points (the acute window sits inside the chronic window, and ratios amplify noise when denominators are small) apply to its inputs. Divergence is an original YTM hypothesis, so no published literature exists to support or refute it. Its evidence has to come from YTM athlete data.
  - **Raw ACWR in YTM.** It applies directly. `app/Training_Metrics_Reference_Guide.md` uses single-stream ACWR bands (0.8–1.3 optimal, 1.3–1.5 "~40% higher" risk, above 1.5 "~70%+ higher") in the decision framework ("Both External & Internal > 1.3 → Reduce intensity/volume"). The risk percentages come from the Gabbett-era literature that Impellizzeri challenges.

### HR lag undercounts internal load on short intervals
- [Running load: threshold intervals vs easy runs](https://forum.intervals.icu/t/running-load-threshold-intervals-vs-easy-runs/100899): HR-based load "often underestimates the true intensity because HR lags behind actual effort, especially for reps under 1 km."
- For YTM, lower TRIMP per load mile on interval days lowers `r_acute`, which pushes divergence toward positive (read as recovery) during interval blocks.

### Decoupling on terrain
- [Decoupling for running](https://forum.intervals.icu/t/decoupling-for-running/24856): decoupling works on long steady efforts and is distorted by hills ("power for ascending does not have same efficiency as power for flat running"). This is a risk for the planned `trail_aerobic_decoupling` metric and is consistent with the rule that pace-at-HR is invalid for trail running.

## Development Opportunities

- **Readiness rules.** HRV and resting HR are the main daily readiness signal on the forum. The ImReady4 rule set flags acute fatigue when resting HR drops by 2 or more standard deviations with normal or elevated HRV ([thread](https://forum.intervals.icu/t/how-to-guide-imready4-app-for-hrv-guided-training/25778)). intervals.icu does not compute readiness. It stores the values wearables report. YTM already computes readiness: HRV and RHR from `journal_entries` feed `get_ans_readiness()` (a z-score assessment with overreaching-trend detection) and Dynamic AeT. The ImReady4 pattern (sharp RHR drop with normal or high HRV indicating acute fatigue) is worth checking against `get_ans_readiness()`.
- **Competitive position.** The official intervals.icu MCP server is at the spec stage ([thread](https://forum.intervals.icu/t/official-mcp-support-for-ai-tools-chatgpt-claude/126164)). Several Claude-based coaches already run on intervals.icu: LeCoach, IntervalCoach, Sharma AI Coach, athletedata.health ($299/yr). YTM's defensible ground is elevation-aware trail load, divergence, and athlete-specific learning. A chat interface on its own is not defensible.
- **Masters athletes.** No forum thread on masters or older-athlete training turned up in these searches. The niche appears unserved by the intervals.icu AI tools.

## Open Questions

Tracked in `.scratch/load-metric-evidence/`:

1. Does HR lag move divergence measurably during interval blocks? See `issues/01-hr-lag-divergence-effect.md`. This is separate from session classification, which `.scratch/session-classification-intervals/issues/01-measure-interval-misclassification.md` covers.
2. Should the ACWR bands and risk percentages in the reference guide be re-sourced, given the Impellizzeri critique? See `issues/02-acwr-band-sourcing.md`.
3. How should divergence be tested against YTM athlete data as an original hypothesis? See `issues/03-divergence-validation-design.md`.
