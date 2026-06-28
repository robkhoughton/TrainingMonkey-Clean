# Dynamic Aerobic Threshold — How Your Training Monkey Adapts Your Zones Every Day

*Methodology note for athletes. Plain-language companion to the technical reference
(`app/Training_Metrics_Reference_Guide.md`) and the design record
(`docs/design_dynamic_aet_2026-06-27.md`).*

## The short version

Your aerobic threshold (AeT) — the heart rate at the top of your easy "Zone 2" — is not a
fixed number. It drifts up and down day to day with how recovered your nervous system is.
Your Training Monkey now treats it that way: each morning it nudges your AeT based on your
overnight heart-rate variability (HRV), and uses that **effective AeT** to judge your easy
runs and to measure your true internal strain.

The practical upshot: on a well-recovered day your easy ceiling sits where you'd expect; on
a day when your body is run down, the ceiling drops a few beats — so the same 130 bpm effort
that was "easy" yesterday is correctly counted as moderate today, and the app tells you to
ease off rather than grind through.

## Why this matters

Most platforms set your zones once and leave them. But a fixed Zone 2 ceiling quietly
betrays you on tired days: you hold the "right" heart rate while your body is actually
working harder than the number implies, accumulating fatigue without the adaptation you
wanted. By moving the ceiling with your readiness, the Monkey keeps easy days genuinely
easy — which is the whole point of polarized training.

## How it works (without the math)

**1. A calibrated baseline.** Your AeT starts from the best measurement available — a recent
HR drift test if you've done one, otherwise your lab-tested setting, otherwise a formula.
This is your "true" aerobic threshold as last established.

**2. A daily correction.** Each morning your overnight HRV is compared to your own recent
baseline. If it's clearly suppressed, the effective AeT is nudged **down** (by up to ~8
bpm). If it's strong, it's nudged **up** a little (less — we're cautious about granting more
intensity off one good reading). Small day-to-day wobble is ignored, so the ceiling doesn't
jump around on noise.

**3. Safety first.** If your readiness shows the "deep hole" pattern (deceptively high HRV
with a suppressed resting heart rate — a sign of deep fatigue), the system will **never**
raise your ceiling, no matter what the raw number says. And if HRV is missing or stale, it
simply holds at baseline and tells you so — it never pretends to a measurement it doesn't
have.

**4. Only the easy ceiling moves.** We adjust the Zone 2/Zone 3 line because that's what
HRV gives us a daily read on. Your threshold (Zone 4/5) boundaries stay put — we don't
invent movement we can't measure.

## What you'll see

- **On easy days:** an HR target that reflects *today's* ceiling ("keep HR below 142 today,
  not 148"), with a note explaining why if it shifted.
- **In your workout autopsy:** an easy run that drifted into moderate territory is flagged as
  such relative to *that day's* ceiling — so the feedback matches how the day actually felt.
- **Honesty when data is thin:** if your overnight HRV didn't sync, you'll see that the AeT
  was held at baseline rather than a fabricated daily number.

## Measuring strain more honestly (coming online)

Beyond zones, the Monkey is building a second, parallel measure of internal training load
that uses these dynamic zones — so a hard effort on a depleted day registers as the higher
strain it truly is. This runs quietly alongside the existing load metric for now and will
take over your fatigue/overtraining signal only after it has proven itself against your own
history. Nothing about your current numbers changes until that switch is made deliberately.

## A note on novelty

Treating AeT as a daily, HRV-driven value that feeds *both* your zone feedback *and* your
internal-load measurement is, as far as we're aware, unusual among training platforms. We
prefer to let the method speak for itself rather than make claims about what other tools do
internally — but if you've felt that fixed zones don't respect how different two days can
feel, this is built precisely for that.
