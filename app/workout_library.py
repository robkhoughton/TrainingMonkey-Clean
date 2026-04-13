"""
Workout Library — canonical prescriptions for YTM coaching.

Prescriptions are fixed. Pace is the emergent signal of improving fitness —
the HR target is the constant, not pace. As fitness develops, the athlete
covers more ground at the same internal load.

Interval rotation: one session per week, alternating protocols every other week
using ISO week parity (even week = Norwegian 4×4, odd week = Lactate Shuttle).

Strides: a neuromuscular stimulus added to the end of qualifying easy runs.
2-3 sessions per week. Placement is strategic — see STRIDE_PROTOCOL and
get_strides_placement_rules() for logic.

Aerobic Assessment (HR Drift Test): monthly diagnostic — see AEROBIC_ASSESSMENT_PROTOCOL
and get_aerobic_assessment_prompt_block() for scheduling logic and execution instructions.
"""

from datetime import date


WORKOUT_LIBRARY = {
    "norwegian_4x4": {
        "name": "Norwegian 4×4",
        "hard_session_type": "intervals",
        "rationale": (
            "Gold standard for VO2max development. 4 reps × 4 minutes at Zone 4 "
            "accumulates 16 minutes of high-quality cardiovascular stimulus with "
            "sufficient recovery to maintain output across all reps."
        ),
        "prescription": {
            "structure": "4 sets × 4 minutes",
            "work_effort": (
                "Zone 4 throughout each rep — HR between Zone 3 ceiling and VT2. "
                "Effort should feel hard but sustainable for the full 4 minutes. "
                "First rep will feel easy; do not chase pace."
            ),
            "rest": "3 minutes active recovery (Zone 1-2 jog/walk) between reps — full recovery matters",
            "total_quality_time": "16 minutes",
            "warm_up": "10-15 minutes easy (below VT1) before first rep",
            "cool_down": "10 minutes easy after final rep",
            "execution_note": (
                "Pace is not the target — HR zone compliance is. "
                "As fitness improves, the same HR effort will produce faster pace. "
                "Do not force pace targets that push HR above VT2."
            ),
        },
    },
    "lactate_shuttle": {
        "name": "Lactate Shuttle (Over-Unders)",
        "hard_session_type": "intervals",
        "rationale": (
            "Trains the body to produce and clear lactate repeatedly. By deliberately "
            "crossing VT2 and then recovering just below it, the athlete develops "
            "tolerance and clearance capacity at threshold — critical for sustained "
            "race efforts."
        ),
        "prescription": {
            "structure": "5-6 cycles of over-under alternations",
            "over": (
                "2 minutes in low Zone 4 — just above VT2, generating a lactate surge. "
                "This is not a sprint; it is a deliberate, controlled push just across threshold."
            ),
            "under": (
                "3 minutes in high Zone 2 / low Zone 3 — just below VT2, clearing lactate. "
                "HR should drop but not fully recover — stay active, not passive."
            ),
            "total_quality_time": "25-30 minutes of alternations",
            "warm_up": "15 minutes easy (below VT1) before first over",
            "cool_down": "10 minutes easy after final under",
            "execution_note": (
                "The transition across VT2 is the stimulus. "
                "The 'over' phase is not a sprint — keep it controlled. "
                "The 'under' phase is not rest — keep moving at high Zone 2. "
                "Pace will rise in both phases as lactate tolerance improves."
            ),
        },
    },
}


STRIDE_PROTOCOL = {
    "name": "Strides",
    "purpose": (
        "Neuromuscular stimulus that recruits fast-twitch muscle fibers and maintains "
        "leg speed without a taxing cardiovascular load. Counteracts the trail shuffle "
        "that develops from sustained grinding on steep terrain."
    ),
    "prescription": {
        "count": "4-6 strides",
        "duration": "20-25 seconds each at a controlled fast effort — not a sprint. "
                    "Smooth, relaxed acceleration to roughly 85-90% of max speed, then decelerate.",
        "recovery": "90 seconds easy walk or jog between strides — full recovery is the point",
        "placement": "At the end of the easy run, after the main aerobic work is complete",
        "terrain": "Flat or gently rolling — avoid technical or steep terrain for strides",
        "execution_note": (
            "Form is the stimulus, not raw speed. Tall posture, quick turnover, relaxed shoulders. "
            "These should feel controlled and snappy — not labored. If legs feel flat or heavy, "
            "reduce to 4 strides and keep effort honest."
        ),
    },
    "placement_rules": {
        "priority_1": (
            "The easy run immediately before the interval session (CNS primer). "
            "Wakes up neural pathways so the first hard interval doesn't feel flat or shocked."
        ),
        "priority_2": (
            "One mid-week easy run for leg speed maintenance — particularly important during "
            "heavy trail volume weeks where stride naturally shortens and slow-twitch patterns dominate."
        ),
        "max_per_week": 3,
        "never": [
            "The day after a long run — muscles carry micro-damage; strides increase injury risk "
            "and interrupt recovery. Let that easy run be purely restorative.",
            "Immediately after a hard interval session — the quality work is already done.",
        ],
    },
}


def get_strides_placement_rules():
    """Return the stride placement rules as a prompt-ready string for weekly plan injection."""
    rules = STRIDE_PROTOCOL["placement_rules"]
    never_list = "\n".join(f"  - {n}" for n in rules["never"])
    return f"""STRIDES — STRATEGIC PLACEMENT RULES:
Strides are a neuromuscular stimulus (4-6 × 20-25 seconds, fast but controlled, 90 sec recovery).
Add strides: true to qualifying easy run days. Maximum {rules['max_per_week']} stride sessions per week.

Place strides on:
1. The easy run immediately before the interval session — always, if an interval session is in the week. This is the CNS primer.
2. One additional mid-week easy run — leg speed maintenance, especially important for trail athletes logging heavy vertical.

Never place strides on:
{never_list}

When strides: true is set, the daily recommendation will inject full execution instructions."""


def get_phase_interval_rules(stage, weeks_to_race=None, target_date=None):
    """Return phase-appropriate interval and strides guidance as a prompt-ready block.

    Args:
        stage: training stage string — 'base', 'build', 'specificity', 'taper', 'peak', 'recovery'
               (case-insensitive; 'Base' is accepted)
        weeks_to_race: float or None — weeks remaining to A race (from _calculate_training_stage)
        target_date: datetime.date for ISO week rotation (defaults to today)

    Returns:
        dict with:
            'interval_allowed': bool
            'protocol_key': str|None — 'norwegian_4x4', 'lactate_shuttle', or None
            'strides_per_week_max': int — max stride sessions this phase
            'prompt_block': str — ready for injection into weekly plan prompt
            'log_summary': str — one-line summary for logging
    """
    stage_lower = (stage or 'base').lower()
    if target_date is None:
        target_date = date.today()

    iso_week = target_date.isocalendar()[1]

    # ── BASE ──────────────────────────────────────────────────────────────────
    if stage_lower == 'base':
        protocol = WORKOUT_LIBRARY["lactate_shuttle"]
        p = protocol["prescription"]
        prompt_block = (
            "INTERVAL PROTOCOL — BASE PHASE:\n"
            "Norwegian 4×4 is not appropriate during base — the CNS demand outweighs the aerobic return "
            "when aerobic infrastructure is still being built.\n\n"
            "Lactate Shuttle (Over-Unders) is cleared: include ONE session every 10-14 days — not weekly.\n"
            f"Structure: {p['structure']}\n"
            f"Over phase: {p['over']}\n"
            f"Under phase: {p['under']}\n"
            f"Quality time: {p['total_quality_time']}\n"
            f"Warm-up: {p['warm_up']} | Cool-down: {p['cool_down']}\n"
            f"Note: {p['execution_note']}\n\n"
            + get_strides_placement_rules()
        )
        return {
            'interval_allowed': True,
            'protocol_key': 'lactate_shuttle',
            'strides_per_week_max': 3,
            'prompt_block': prompt_block,
            'log_summary': 'base → Lactate Shuttle every 10-14 days, strides 2-3×/wk',
        }

    # ── BUILD / SPECIFICITY ───────────────────────────────────────────────────
    if stage_lower in ('build', 'specificity'):
        key = "norwegian_4x4" if iso_week % 2 == 0 else "lactate_shuttle"
        protocol = WORKOUT_LIBRARY[key]
        p = protocol["prescription"]
        other = "Lactate Shuttle" if key == "norwegian_4x4" else "Norwegian 4×4"
        if key == "norwegian_4x4":
            detail_lines = [
                f"Structure: {p['structure']}",
                f"Work effort: {p['work_effort']}",
                f"Recovery: {p['rest']}",
                f"Quality time: {p['total_quality_time']}",
                f"Warm-up: {p['warm_up']} | Cool-down: {p['cool_down']}",
                f"Note: {p['execution_note']}",
            ]
        else:
            detail_lines = [
                f"Structure: {p['structure']}",
                f"Over phase: {p['over']}",
                f"Under phase: {p['under']}",
                f"Quality time: {p['total_quality_time']}",
                f"Warm-up: {p['warm_up']} | Cool-down: {p['cool_down']}",
                f"Note: {p['execution_note']}",
            ]
        prompt_block = (
            f"INTERVAL PROTOCOL — {stage_lower.upper()} PHASE (ISO week {iso_week}):\n"
            f"THIS WEEK: {protocol['name']}\n"
            + "\n".join(detail_lines)
            + f"\n\nNext week rotates to {other}. One interval session per week.\n\n"
            + get_strides_placement_rules()
        )
        return {
            'interval_allowed': True,
            'protocol_key': key,
            'strides_per_week_max': 2,
            'prompt_block': prompt_block,
            'log_summary': f'{stage_lower} → {protocol["name"]} (ISO week {iso_week} rotation), strides 1-2×/wk',
        }

    # ── TAPER ─────────────────────────────────────────────────────────────────
    if stage_lower == 'taper':
        wtr = float(weeks_to_race) if weeks_to_race is not None else 3.0
        # Lactate Shuttle window: approximately 10 days out (1.0–2.0 weeks to race)
        if wtr <= 2.0:
            p = WORKOUT_LIBRARY["lactate_shuttle"]["prescription"]
            prompt_block = (
                "INTERVAL PROTOCOL — TAPER PHASE:\n"
                f"Approximately {round(wtr * 7)} days to race — this is the Lactate Shuttle window.\n"
                "ONE Lactate Shuttle session this week at REDUCED VOLUME: 4 cycles (not 5-6).\n"
                f"Structure: 4 cycles of over-under alternations (reduced from {p['structure']})\n"
                f"Over phase: {p['over']}\n"
                f"Under phase: {p['under']}\n"
                f"Warm-up: {p['warm_up']} | Cool-down: {p['cool_down']}\n"
                "This is the last hard session before race day. Execution must be controlled — "
                "do not chase intensity.\n\n"
                + get_strides_placement_rules()
            )
            return {
                'interval_allowed': True,
                'protocol_key': 'lactate_shuttle',
                'strides_per_week_max': 2,
                'prompt_block': prompt_block,
                'log_summary': f'taper ({round(wtr * 7)}d out) → Lactate Shuttle reduced volume, strides 2×/wk',
            }
        else:
            prompt_block = (
                "INTERVAL PROTOCOL — TAPER PHASE:\n"
                f"Approximately {round(wtr * 7)} days to race — too far out for a hard interval session.\n"
                "No interval session this week. Volume is reducing; preserve freshness.\n"
                "The Lactate Shuttle window opens approximately 10 days before race day.\n\n"
                + get_strides_placement_rules()
            )
            return {
                'interval_allowed': False,
                'protocol_key': None,
                'strides_per_week_max': 2,
                'prompt_block': prompt_block,
                'log_summary': f'taper ({round(wtr * 7)}d out) → no interval, Lactate Shuttle window not yet open, strides 2×/wk',
            }

    # ── PEAK ──────────────────────────────────────────────────────────────────
    if stage_lower == 'peak':
        wtr = float(weeks_to_race) if weeks_to_race is not None else 1.0
        prompt_block = (
            "INTERVAL PROTOCOL — PEAK PHASE:\n"
            f"Race is approximately {round(wtr * 7)} days away. No interval sessions this week.\n"
            "The body needs to arrive at the start line fresh and primed — not recovering from hard work.\n"
            "Strides are the only neuromuscular stimulus this week: keep them short, sharp, and relaxed.\n\n"
            + get_strides_placement_rules()
        )
        return {
            'interval_allowed': False,
            'protocol_key': None,
            'strides_per_week_max': 2,
            'prompt_block': prompt_block,
            'log_summary': f'peak ({round(wtr * 7)}d out) → no intervals, strides only',
        }

    # ── RECOVERY ──────────────────────────────────────────────────────────────
    if stage_lower == 'recovery':
        # weeks_to_race is negative in recovery (days since race)
        days_since_race = abs(int(weeks_to_race * 7)) if weeks_to_race is not None else 7
        weeks_since_race = days_since_race / 7.0

        if weeks_since_race < 2:
            prompt_block = (
                "INTERVAL PROTOCOL — RECOVERY PHASE:\n"
                f"Approximately {days_since_race} days post-race. No intervals and no strides this week.\n"
                "The body is repairing micro-damage and restoring hormonal balance. "
                "Any neuromuscular stimulus now competes with recovery, not fitness.\n"
                "All sessions this week: easy aerobic only, below VT1.\n"
            )
            return {
                'interval_allowed': False,
                'protocol_key': None,
                'strides_per_week_max': 0,
                'prompt_block': prompt_block,
                'log_summary': f'recovery (week {int(weeks_since_race) + 1}) → no intervals, no strides',
            }
        else:
            prompt_block = (
                "INTERVAL PROTOCOL — RECOVERY PHASE:\n"
                f"Approximately {days_since_race} days post-race — neuromuscular reintroduction is appropriate.\n"
                "No interval sessions yet. Strides may be reintroduced: 4 strides only on one easy run day.\n"
                "Keep effort controlled and relaxed — this is reconnection, not training stimulus.\n\n"
                + get_strides_placement_rules()
            )
            return {
                'interval_allowed': False,
                'protocol_key': None,
                'strides_per_week_max': 1,
                'prompt_block': prompt_block,
                'log_summary': f'recovery (week {int(weeks_since_race) + 1}) → no intervals, 4 strides reintroduction',
            }

    # ── FALLBACK (unknown stage) ───────────────────────────────────────────────
    key = "norwegian_4x4" if iso_week % 2 == 0 else "lactate_shuttle"
    protocol = get_interval_protocol_for_week(target_date)
    return {
        'interval_allowed': True,
        'protocol_key': key,
        'strides_per_week_max': 2,
        'prompt_block': (
            f"THIS WEEK'S INTERVAL PROTOCOL: {protocol['name']} (ISO week rotation)\n\n"
            + get_strides_placement_rules()
        ),
        'log_summary': f'unknown stage → fallback ISO rotation ({protocol["name"]})',
    }


# ── AEROBIC ASSESSMENT (HR DRIFT TEST) ────────────────────────────────────────

AEROBIC_ASSESSMENT_PROTOCOL = {
    "name": "HR Drift Test",
    "purpose": (
        "Diagnostic test to establish Aerobic Threshold (AeT) bpm — the Zone 2 ceiling. "
        "Not a training session. Generates no adaptive stimulus. "
        "Replaces one Zone 2 easy run in the week it is scheduled."
    ),
    "retest_interval_days": 42,       # 6-week target; window opens at 28 days
    "retest_window_open_days": 28,    # before this: current, no action needed
    "blocked_phases": ("taper", "peak", "recovery"),  # never schedule in these phases
    "prerequisites": [
        "Well-rested — do not schedule within 2 days of a long run or hard session",
        "Not during taper, peak, or recovery phase",
        "Athlete must not be carrying injury that affects running economy",
    ],
    "protocol": {
        "warmup": "10 minutes at easy conversational pace (nose breathing). Do not skip.",
        "steady_state": (
            "60 minutes at constant effort. Lock in a starting HR and hold it. "
            "Do not adjust effort during the test — HR drift is the signal."
        ),
        "terrain_indoor": (
            "Treadmill or StairMaster. Set speed and grade, then do not touch either. "
            "Constant external load is mandatory — any adjustment invalidates the test."
        ),
        "terrain_outdoor": (
            "Flat loop course only. Minimal cumulative elevation change (< 70ft per hour). "
            "Out-and-back routes are invalid — asymmetric grade changes corrupt the HR response."
        ),
        "starting_hr_guidance": (
            "Target a HR approximately 10 bpm below your estimated AeT. "
            "If no prior test: start at the upper limit of comfortable nose breathing. "
            "If prior test was valid (drift 1.5–5%): use that AeT bpm as the starting target. "
            "If prior test drifted too high (>5%): start 3–5 bpm lower than last time. "
            "If prior test drifted too low (<1.5%): start 3–5 bpm higher than last time."
        ),
        "analysis": (
            "After the run, submit the activity in the Aerobic Assessment panel on the Season page. "
            "The system will compute drift %, AeT bpm, and gap status automatically from the HR stream."
        ),
    },
}


def get_aerobic_assessment_prompt_block(days_since_test: int, stage: str, last_drift_pct: float = None) -> dict:
    """Return scheduling status and prompt block for the aerobic assessment.

    Thresholds:
        ≤ 28 days  → current, no action
        29–42 days → window open, suggest scheduling
        > 42 days  → overdue, prescribe this week (if phase allows)

    Args:
        days_since_test: Days since last valid test. Use 9999 if no test on record.
        stage:           Training stage string (base, build, specificity, taper, peak, recovery).
        last_drift_pct:  Drift % from most recent test (to personalise starting HR guidance).

    Returns:
        dict with:
            status:       'current' | 'window_open' | 'overdue' | 'blocked'
            prompt_block: str ready for injection into weekly plan prompt
            log_summary:  one-line summary for logging
    """
    proto = AEROBIC_ASSESSMENT_PROTOCOL
    stage_lower = (stage or 'base').lower()
    phase_blocked = stage_lower in proto["blocked_phases"]

    if days_since_test <= 28:
        return {
            'status': 'current',
            'prompt_block': '',
            'log_summary': f'AeT test current ({days_since_test}d ago) — no action',
        }

    if phase_blocked:
        return {
            'status': 'blocked',
            'prompt_block': '',
            'log_summary': f'AeT test overdue ({days_since_test}d) but blocked in {stage_lower} phase',
        }

    # Build starting HR guidance based on last result
    if last_drift_pct is None:
        hr_guidance = proto["protocol"]["starting_hr_guidance"].split("If prior")[0].strip()
    elif last_drift_pct > 5.0:
        hr_guidance = "Start 3–5 bpm lower than last test — previous drift was too high."
    elif last_drift_pct < 1.5:
        hr_guidance = "Start 3–5 bpm higher than last test — previous drift was too low."
    else:
        hr_guidance = "Use your recorded AeT bpm as the starting HR target — last test was valid."

    p = proto["protocol"]
    execution_block = (
        f"AEROBIC ASSESSMENT — HR DRIFT TEST PROTOCOL:\n"
        f"Replaces one Zone 2 easy run this week. Schedule on a day with fresh legs "
        f"(not within 2 days of a long run or hard session).\n\n"
        f"Warm-up: {p['warmup']}\n"
        f"Steady state: {p['steady_state']}\n"
        f"Indoor: {p['terrain_indoor']}\n"
        f"Outdoor: {p['terrain_outdoor']}\n"
        f"Starting HR: {hr_guidance}\n"
        f"After the run: {p['analysis']}\n"
    )

    if days_since_test <= 42:
        return {
            'status': 'window_open',
            'prompt_block': (
                f"AEROBIC ASSESSMENT — RETEST WINDOW OPEN ({days_since_test} days since last test):\n"
                f"The retest window is open (target: every 6 weeks). "
                f"Suggest the athlete schedules a drift test this week or next if conditions are good.\n\n"
                + execution_block
            ),
            'log_summary': f'AeT test window open ({days_since_test}d) — suggest scheduling',
        }

    return {
        'status': 'overdue',
        'prompt_block': (
            f"AEROBIC ASSESSMENT — OVERDUE ({days_since_test} days since last test):\n"
            f"The drift test is overdue. Prescribe it this week. "
            f"It replaces one Zone 2 run — do not add it on top of the existing load.\n\n"
            + execution_block
        ),
        'log_summary': f'AeT test overdue ({days_since_test}d) — prescribe this week',
    }


def get_interval_protocol_for_week(target_date=None):
    """Return the interval protocol for the week containing target_date.

    Rotation uses ISO week number parity:
        Even week → Norwegian 4×4
        Odd week  → Lactate Shuttle

    Args:
        target_date: datetime.date or None (defaults to today)

    Returns:
        dict with keys: 'key', 'name', 'hard_session_type', 'rationale', 'prescription'
    """
    if target_date is None:
        target_date = date.today()

    iso_week = target_date.isocalendar()[1]
    key = "norwegian_4x4" if iso_week % 2 == 0 else "lactate_shuttle"
    protocol = WORKOUT_LIBRARY[key]
    return {"key": key, **protocol}


def format_interval_protocol_for_prompt(protocol, vt1_bpm=None, vt2_bpm=None):
    """Format a protocol dict as a prompt-ready string with zone-anchored HR values.

    Args:
        protocol: dict from get_interval_protocol_for_week()
        vt1_bpm: athlete's VT1 (Zone 2 ceiling) in bpm, or None
        vt2_bpm: athlete's VT2 (Zone 4 ceiling) in bpm, or None

    Returns:
        str ready for prompt injection
    """
    p = protocol["prescription"]
    name = protocol["name"]

    zone_anchor = ""
    if vt1_bpm and vt2_bpm:
        zone_anchor = (
            f"\nZONE REFERENCE (this athlete): "
            f"VT1 = {vt1_bpm} bpm (Zone 2 ceiling), "
            f"VT2 = {vt2_bpm} bpm (Zone 4 ceiling). "
            f"Zone 4 work targets the band between Zone 3 and {vt2_bpm} bpm. "
            f"Do not prescribe HR numbers below {vt1_bpm} bpm as Zone 4."
        )

    if protocol["key"] == "norwegian_4x4":
        lines = [
            f"THIS WEEK'S INTERVAL PROTOCOL: {name}",
            f"Structure: {p['structure']}",
            f"Work effort: {p['work_effort']}",
            f"Recovery: {p['rest']}",
            f"Quality time: {p['total_quality_time']}",
            f"Warm-up: {p['warm_up']}",
            f"Cool-down: {p['cool_down']}",
            f"Note: {p['execution_note']}",
        ]
    else:  # lactate_shuttle
        lines = [
            f"THIS WEEK'S INTERVAL PROTOCOL: {name}",
            f"Structure: {p['structure']}",
            f"Over phase: {p['over']}",
            f"Under phase: {p['under']}",
            f"Quality time: {p['total_quality_time']}",
            f"Warm-up: {p['warm_up']}",
            f"Cool-down: {p['cool_down']}",
            f"Note: {p['execution_note']}",
        ]

    return "\n".join(lines) + zone_anchor
