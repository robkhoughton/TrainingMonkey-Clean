"""
Recovery gate — decides whether a divergence breach (overtraining_risk) may be met with
Zone 1 easy sessions instead of rest only. Category-2 safety logic: deterministic first,
with an LLM journal-note veto that can only tighten the floor, never loosen it.

Pass requires BOTH:
  - Pain gate: the worst Pain Score (pain_percentage) in the last 3 days is below 40%,
    with at least one reading. 40 is the Training Metrics Reference Guide's
    "Tolerable — consider modifying" step; Zone 1 counts as a modification.
  - Journal-note veto: no journal note in the same window (rest days included) signals
    injury or pain. Tightness, soreness and swelling/edema are not injury signals
    unless the note also reports pain. A classifier error counts as a signal (fail safe).

Decided by Rob 2026-10-12. See .scratch/divergence-rest-projection/spec.md.
"""
from datetime import date, datetime, timedelta

PAIN_GATE_PCT = 40
GATE_WINDOW_DAYS = 3


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()


def evaluate_recovery_gate(journal_rows, target_date, classify_notes):
    """Evaluate the recovery gate for `target_date`.

    Args:
        journal_rows: iterable of {'date', 'pain_percentage', 'notes'} journal entries.
        target_date: the date the recommendation is for; the window is target_date and
            the GATE_WINDOW_DAYS - 1 days before it.
        classify_notes: callable(list of (date_str, note)) -> bool, True when any note
            signals injury or pain. May raise; an exception fails the gate.

    Returns:
        {'passed': bool,
         'reason': None | 'pain' | 'no_pain_readings' | 'journal_injury_signal' | 'veto_error',
         'max_pain': int | None,
         'pain_readings': int,
         'veto': 'negative' | 'positive' | 'error' | 'no_notes' | 'not_run',
         'window_start': 'YYYY-MM-DD', 'window_end': 'YYYY-MM-DD'}
    """
    target_date = _as_date(target_date)
    window_start = target_date - timedelta(days=GATE_WINDOW_DAYS - 1)
    in_window = [r for r in journal_rows if window_start <= _as_date(r['date']) <= target_date]

    readings = [r['pain_percentage'] for r in in_window if r.get('pain_percentage') is not None]
    result = {
        'passed': False,
        'reason': None,
        'max_pain': max(readings) if readings else None,
        'pain_readings': len(readings),
        'veto': 'not_run',
        'window_start': window_start.isoformat(),
        'window_end': target_date.isoformat(),
    }

    if not readings:
        result['reason'] = 'no_pain_readings'
        return result
    if result['max_pain'] >= PAIN_GATE_PCT:
        result['reason'] = 'pain'
        return result

    notes = [(_as_date(r['date']).isoformat(), r['notes'].strip())
             for r in in_window if r.get('notes') and r['notes'].strip()]
    if not notes:
        result['veto'] = 'no_notes'
        result['passed'] = True
        return result

    try:
        flagged = bool(classify_notes(notes))
    except Exception:
        result['veto'] = 'error'
        result['reason'] = 'veto_error'
        return result

    if flagged:
        result['veto'] = 'positive'
        result['reason'] = 'journal_injury_signal'
        return result

    result['veto'] = 'negative'
    result['passed'] = True
    return result
