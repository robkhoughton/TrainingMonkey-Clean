Type: task
Status: open

## Question

What is the source for each ACWR band and risk figure in `app/Training_Metrics_Reference_Guide.md`, and does it hold up after the Impellizzeri et al. 2020 critique?

## Claims to trace

- Bands: < 0.8 undertraining, 0.8–1.3 optimal, 1.3–1.5 high risk, > 1.5 very high risk (guide § Load Ratios, and the table at line ~201)
- Risk figures: "~40% higher than optimal zone" (1.3–1.5) and "~70%+ higher" (> 1.5)
- Decision rules: "Both External & Internal > 1.3 → Reduce intensity/volume", "Both ACWR < 0.8 → Progressive load increase opportunity (10-15%)", "Reduce volume 25-40%"
- "Chronic Elevation: ACWR > 1.3 for 5+ consecutive days"

## Critiques to weigh

- Impellizzeri et al. 2020, *Sports Med*: ACWR is an inaccurate scaling index and should be dropped as an injury metric ([link](https://research.tees.ac.uk/en/publications/the-acute-to-chronic-workload-ratio-an-inaccurate-scaling-index-f/))
- Bayesian analysis: internal-load ACWR predicts no better than a synthetic ACWR built with a random denominator ([PMC9572878](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9572878/))
- Check the Zotero library (`Research/zotero-library.json`) for Gabbett 2016 and related sources first.

## Outcome for each claim

One of:
1. **Cited.** Add the source to the guide, with the critique noted where it applies.
2. **Product judgment call.** Relabel it as a YTM default and remove any risk percentage that implies an injury-rate finding.
3. **Remove.** Delete it if neither applies.

These thresholds are category-1 values under `llm-determinism.md`, so any change to a number must be followed through to the code that implements it.

## Done when

Every claim above is cited, relabelled, or removed in the guide.
