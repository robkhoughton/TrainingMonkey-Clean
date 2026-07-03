# TrainingMonkey Docs

Index of the live documentation set. Historical/superseded material has been moved to
[`_archive/`](_archive/) (see its README for the full list and restore instructions).

Authoritative project rules live in `.claude/CLAUDE.md` and `.claude/rules/` — this folder is
supporting reference, not the source of truth for coding standards.

## Architecture
- [`APPLICATION_ARCHITECTURE.md`](APPLICATION_ARCHITECTURE.md) — system overview
- [`ARCHITECTURE_QUICK_REFERENCE.md`](ARCHITECTURE_QUICK_REFERENCE.md) — quick lookup
- [`architecture/`](architecture/) — YTM Roadmap, coaching-pipeline map + QC audit
- [`methodology/dynamic_aet.md`](methodology/dynamic_aet.md) — dynamic/effective-AeT methodology

## Coaching model & references
- [`reference/`](reference/) — the coaching reference library (paired with `app/coaching_context/`):
  Zone 2, aerobic assessment (HR drift + LT1), neuromuscular, muscular endurance, training
  philosophy, athlete model. Threshold source of truth is `app/Training_Metrics_Reference_Guide.md`.
- [`features/COACHING_FRAMEWORK_GAPS.md`](features/COACHING_FRAMEWORK_GAPS.md) — coaching framework roadmap / gap plan
- [`MODEL_REVIEW_RUBRIC.md`](MODEL_REVIEW_RUBRIC.md) — LLM output review rubric

## Branding
- [`branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md`](branding/YOUR_TRAINING_MONKEY_BRAND_FRAMEWORK.md) — brand single source of truth (referenced in CLAUDE.md)
- [`branding/`](branding/) — application guide, app description, brand kit, visual style examples

## Database
- [`database/`](database/) — access guide, connection quick-start, security, schema-verification, migration instructions, SQL syntax

## Deployment & setup
- [`deployment/`](deployment/) — deployment checklist, dev guide, environment setup, Dockerfile requirements, Anthropic API key, static-files troubleshooting

## Commands
- [`commands/`](commands/) — `/verify-ui` command reference

## Session summaries
- [`session_summaries/`](session_summaries/) — dated session logs (target of the `/summarize-chat` skill)
