Type: grilling
Status: open
Blocked by: 01

## Question

How should YTM test its own hypothesis that Normalized Divergence is a fatigue signal, using athlete data alone?

## Framing

Divergence is Rob's hypothesis, original to YTM. No external literature supports it, and none is expected, so this ticket is not a literature search. Its evidence base is what YTM's own data shows. The goal is a falsifiable test: state in advance what result would count against the hypothesis.

It is blocked by 01 because an HR-lag confound in TRIMP would contaminate any validation.

## Decisions to make

- **Claim.** What exactly does divergence predict, and over what lead time? For example, a negative breach precedes a pain-score rise, a reported injury, or a poor autopsy response within N days.
- **Outcomes.** Which are logged consistently enough to use: pain scores, autopsy outcomes, RPE, journal notes, missed sessions?
- **Comparison.** What does divergence have to beat to earn its place? Candidates: raw internal ACWR alone, raw external ACWR alone, or a shuffled-date null (the same random-denominator test applied to ACWR in the literature).
- **Sample.** Are user 1's history plus other athletes with long histories enough? What minimum is needed before drawing any conclusion?
- **Refutation.** What result would lead to retiring or redefining divergence?

## Done when

There is a written test plan with a pre-stated claim, outcomes, comparison, sample threshold, and refutation criterion, ready to run as its own analysis ticket.
