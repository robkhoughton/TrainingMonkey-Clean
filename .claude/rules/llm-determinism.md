# LLM vs Deterministic Logic — Boundary Rules

How to decide what belongs in deterministic code, what belongs in the prompt, and
what to leave to LLM judgment — written so the boundary holds as models improve.

## Core principle

There are **two different reasons** to make something deterministic, and **only one
of them is about model capability:**

- **Correctness / safety / single-source-of-truth** → deterministic *permanently*,
  regardless of how capable the model becomes. This is about guarantees and liability,
  not about whether the model is "smart enough."
- **Compensating for a current model weakness** → deterministic (or prompt-scaffolded)
  *temporarily*; revisit and prune as capability improves.

The trap to avoid: **"the model is smarter now, let it handle that."** That reasoning
is only ever valid for the second category. Never migrate a correctness or safety
concern to LLM judgment because the model got better.

## The four categories

| # | Category | Where it lives | Lifespan |
|---|----------|----------------|----------|
| 1 | **Authoritative facts & computations** — any value with a single correct answer (thresholds, metric classifications, date filters, the race list, weeks-to-race) | Deterministic code; **injected into the prompt as stated fact**, never re-derived by the model | Permanent |
| 2 | **Safety constraints** — non-negotiable floors (e.g. rest when overtraining) | Deterministic code **+ a post-generation guardrail that enforces it** (not just a prompt instruction) | Permanent |
| 3 | **Judgment, synthesis, voice** — weighing multiple signals in context, prose, coaching tone | LLM | — |
| 4 | **Compensatory scaffolding** — format enforcement, anti-self-correction rules, "don't invent a threshold" nudges, word-count limits | Prompt, tagged `[COMP]` | Temporary — review on each model upgrade |

## Rules

1. **Never let the LLM re-derive a category-1 value.** If it has one correct answer,
   compute it in code and inject it as a fact. Even strong models fabricate and
   mis-transcribe numbers in long prose. (See `format_metric_verdict_block` injecting
   the verdict; `repair_metric_citations` repairing prose numbers against
   `metrics_snapshot`.)
2. **Safety floors are enforced, not requested.** Compute the floor in code and verify
   the model's output against it after generation; regenerate or fall back on violation.
   A safety guarantee must not depend on the model "usually" complying. (See
   `enforce_safety_floor`.)
3. **Tag every load-bearing prompt instruction** `[COMP]` (compensates for current
   weakness — prune as models improve) or `[DOMAIN]` (encodes physiology/coaching rules
   — keep indefinitely). This makes the temporary vs permanent distinction auditable.
4. **On a model upgrade, prune category 4 — only category 4.** Re-test whether each
   `[COMP]` scaffold is still needed; delete what the model no longer requires. Do **not**
   touch categories 1 and 2. Capability evolution should only ever *shrink* the
   compensatory layer.
5. **When a category-4 weakness touches a category-1/2 value, add a deterministic
   backstop** and keep it until the weakness is proven gone. Example:
   `repair_metric_citations` exists because number-transcription (a weakness) corrupts
   the authoritative metrics (correctness). The *need* is permanent; the
   *implementation* can retire if/when the weakness does.

## Long-term direction (how category 4 shrinks)

As models improve, shift the prompt from **reasoning instructions toward information
richness**: give the model better data (athlete state, history, autopsy/response
patterns) and fewer instructions on *how* to reason. Accumulated individual response
data eventually outperforms population-average rules and hard-coded heuristics — prefer
feeding it over encoding it. This is the primary mechanism by which the compensatory
layer (category 4) shrinks over time. (Note: this shifts categories 3→better, and 4→
smaller; it does **not** touch categories 1 and 2.)

## Worked example — the daily Rx

- Category 1: calibrated divergence/ACWR thresholds, `assessment_category`, the
  `### TODAY'S METRIC VERDICT` block, `get_upcoming_race_goals`.
- Category 2: the rest/reduce floor + `enforce_safety_floor` regenerate-or-fallback.
- Category 3: which session to prescribe within the floor, tuning by the alignment
  number, the coaching prose and tone.
- Category 4: the 10-element format, "no self-correction in prose", "copy numbers
  exactly", REST-DAY framing rule — all `[COMP]`, all candidates for pruning later.
