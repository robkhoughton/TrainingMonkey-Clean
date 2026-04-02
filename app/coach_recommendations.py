#!/usr/bin/env python3
"""
Coach Recommendations Module for Training Monkey™ Coach Page.

This module generates divergence-optimized weekly training programs using:
- Race goals (A/B/C hierarchy)
- Race history and performance trends
- Training schedule and availability
- Current training stage
- Recent metrics (ACWR, divergence, TRIMP)
- Journal observations

Generates structured 7-day training programs via Claude API.
"""

import os
import json
import logging
import requests
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Import existing modules
from timezone_utils import get_app_current_date, get_current_week_start
from unified_metrics_service import UnifiedMetricsService
from db_utils import execute_query, upsert_week_strategic_summary
from llm_recommendations_module import (
    call_anthropic_api,
    load_training_guide,
    _select_guide_sections,
    get_athlete_model_context,
    get_user_coaching_spectrum,
    get_coaching_tone_instructions,
    get_user_recommendation_style,
    get_adjusted_thresholds,
    apply_athlete_model_to_thresholds,
    analyze_pattern_flags,
    get_recent_autopsy_insights,
    MODEL_HAIKU,
)
from acwr_configuration_service import ACWRConfigurationService
from prompt_constants import NORMALIZED_DIVERGENCE_FORMULA, format_divergence_for_prompt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('coach_recommendations')

# Constants
CACHE_EXPIRY_DAYS = 3  # Weekly programs valid for 3 days
DEFAULT_MAX_TOKENS = 4000  # Longer for structured 7-day programs

# Temperature settings optimized for different generation tasks
WEEKLY_PROGRAM_TEMPERATURE = 0.5  # Structured JSON output - needs consistency
STRATEGIC_CONTEXT_TEMPERATURE = 0.75  # Rich narrative analysis - benefits from creativity


def get_race_goals(user_id: int) -> List[Dict]:
    """Fetch user's race goals ordered by date."""
    query = """
        SELECT id, race_name, race_date, race_type, priority, target_time, notes, elevation_gain_feet, distance_miles
        FROM race_goals
        WHERE user_id = %s
        ORDER BY race_date ASC
    """
    results = execute_query(query, (user_id,), fetch=True)
    
    if not results:
        return []
    
    goals = []
    for row in results:
        goals.append({
            'id': row['id'],
            'race_name': row['race_name'],
            'race_date': row['race_date'].isoformat() if hasattr(row['race_date'], 'isoformat') else str(row['race_date']),
            'race_type': row['race_type'],
            'priority': row['priority'],
            'target_time': row['target_time'],
            'notes': row['notes'],
            'elevation_gain_feet': row['elevation_gain_feet'],
            'distance_miles': row['distance_miles'],
        })
    
    return goals


def get_race_history(user_id: int, limit: int = 10) -> List[Dict]:
    """Fetch user's race history (last 5 years, most recent first)."""
    query = """
        SELECT id, race_date, race_name, distance_miles, finish_time_minutes
        FROM race_history
        WHERE user_id = %s
        ORDER BY race_date DESC
        LIMIT %s
    """
    results = execute_query(query, (user_id, limit), fetch=True)
    
    if not results:
        return []
    
    history = []
    for row in results:
        history.append({
            'id': row['id'],
            'race_date': row['race_date'].isoformat() if hasattr(row['race_date'], 'isoformat') else str(row['race_date']),
            'race_name': row['race_name'],
            'distance_miles': float(row['distance_miles']),
            'finish_time_minutes': int(row['finish_time_minutes'])
        })
    
    return history


def get_training_schedule(user_id: int) -> Optional[Dict]:
    """Fetch user's training schedule from user_settings and cross-training disciplines."""
    query = """
        SELECT training_schedule_json, include_strength_training, strength_hours_per_week,
               include_mobility, mobility_hours_per_week, include_cross_training,
               cross_training_type, cross_training_hours_per_week
        FROM user_settings
        WHERE id = %s
    """
    results = execute_query(query, (user_id,), fetch=True)

    if not results or not results[0]:
        return None

    row = results[0]
    schedule_json = row['training_schedule_json']

    # Parse JSON if it's a string
    if isinstance(schedule_json, str):
        try:
            schedule_json = json.loads(schedule_json)
        except:
            schedule_json = None

    # Fetch multi-discipline cross-training data
    disciplines_query = """
        SELECT discipline, allocation_type, allocation_value
        FROM user_cross_training_disciplines
        WHERE user_id = %s AND enabled = TRUE
        ORDER BY discipline
    """
    disciplines_result = execute_query(disciplines_query, (user_id,), fetch=True)

    cross_training_disciplines = []
    if disciplines_result:
        for d in disciplines_result:
            cross_training_disciplines.append({
                'discipline': d['discipline'],
                'allocation_type': d['allocation_type'],
                'allocation_value': float(d['allocation_value'])
            })

    return {
        'schedule': schedule_json,
        'include_strength': row['include_strength_training'],
        'strength_hours': float(row['strength_hours_per_week']) if row['strength_hours_per_week'] else 0,
        'include_mobility': row['include_mobility'],
        'mobility_hours': float(row['mobility_hours_per_week']) if row['mobility_hours_per_week'] else 0,
        'cross_training_disciplines': cross_training_disciplines,
        # Legacy fields for backward compatibility
        'include_cross_training': row['include_cross_training'],
        'cross_training_type': row['cross_training_type'],
        'cross_training_hours': float(row['cross_training_hours_per_week']) if row['cross_training_hours_per_week'] else 0
    }


def calculate_performance_trend(race_history: List[Dict]) -> Dict:
    """
    Analyze race history to determine performance trend.
    
    Returns:
        - trend: 'improving', 'stable', 'declining', 'insufficient_data'
        - details: summary string
    """
    if len(race_history) < 2:
        return {
            'trend': 'insufficient_data',
            'details': 'Need at least 2 race results to determine trend'
        }
    
    # Group by similar distances (within 20% of each other)
    distance_groups = {}
    for race in race_history:
        dist = race['distance_miles']
        # Find existing group or create new one
        found_group = False
        for key_dist in distance_groups.keys():
            if abs(dist - key_dist) / key_dist < 0.2:  # Within 20%
                distance_groups[key_dist].append(race)
                found_group = True
                break
        if not found_group:
            distance_groups[dist] = [race]
    
    # Analyze each distance group
    trends = []
    for dist, races in distance_groups.items():
        if len(races) < 2:
            continue
        
        # Sort by date
        races.sort(key=lambda x: x['race_date'])
        
        # Compare pace (min/mile) over time
        paces = [(r['finish_time_minutes'] / r['distance_miles'], r['race_date']) for r in races]
        
        # Simple trend: compare first and last
        first_pace, last_pace = paces[0][0], paces[-1][0]
        
        if last_pace < first_pace * 0.95:  # 5% improvement
            trends.append(('improving', dist, first_pace, last_pace))
        elif last_pace > first_pace * 1.05:  # 5% slower
            trends.append(('declining', dist, first_pace, last_pace))
        else:
            trends.append(('stable', dist, first_pace, last_pace))
    
    if not trends:
        return {
            'trend': 'insufficient_data',
            'details': 'No comparable race distances to determine trend'
        }
    
    # Overall trend is majority vote
    improving = sum(1 for t in trends if t[0] == 'improving')
    declining = sum(1 for t in trends if t[0] == 'declining')
    
    if improving > declining:
        overall = 'improving'
        detail_str = f"Performance improving across {improving} distance(s)"
    elif declining > improving:
        overall = 'declining'
        detail_str = f"Performance declining across {declining} distance(s)"
    else:
        overall = 'stable'
        detail_str = "Performance holding steady"
    
    return {
        'trend': overall,
        'details': detail_str,
        'distance_analysis': trends
    }


def get_current_training_stage(user_id: int) -> Dict:
    """
    Calculate current training stage based on race goals.
    This calls the existing training stage endpoint logic.
    """
    # Import here to avoid circular dependency
    from strava_app import _calculate_training_stage
    
    race_goals = get_race_goals(user_id)
    
    if not race_goals:
        return {
            'stage': 'Base',
            'weeks_to_race': None,
            'race_name': None,
            'details': 'No race goal set - focus on base building'
        }
    
    # Find A race (or first B/C race if no A)
    a_race = next((r for r in race_goals if r['priority'] == 'A'), None)
    if not a_race:
        b_race = next((r for r in race_goals if r['priority'] == 'B'), None)
        if b_race:
            a_race = b_race
        else:
            a_race = race_goals[0]
    
    current_date = get_app_current_date()
    race_date = datetime.strptime(a_race['race_date'], '%Y-%m-%d').date()
    
    stage_info = _calculate_training_stage(current_date, race_date)
    stage_info['race_name'] = a_race['race_name']
    stage_info['priority'] = a_race['priority']
    
    return stage_info


def get_recent_journal_observations(user_id: int, days: int = 7) -> List[Dict]:
    """Fetch recent journal entries for context."""
    query = """
        SELECT date, energy_level, rpe_score, pain_percentage, notes
        FROM journal_entries
        WHERE user_id = %s
        AND date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY date DESC
    """
    results = execute_query(query, (user_id, days), fetch=True)
    
    if not results:
        return []
    
    observations = []
    for row in results:
        observations.append({
            'date': row['date'].isoformat() if hasattr(row['date'], 'isoformat') else str(row['date']),
            'energy_level': row['energy_level'],
            'rpe_score': row['rpe_score'],
            'pain_percentage': row['pain_percentage'],
            'notes': row['notes']
        })
    
    return observations


def format_race_goals_for_prompt(race_goals: List[Dict]) -> str:
    """Format race goals as readable text for LLM prompt."""
    if not race_goals:
        return "No race goals currently set."
    
    lines = []
    for goal in race_goals:
        race_date = goal['race_date']
        days_away = (datetime.strptime(race_date, '%Y-%m-%d').date() - get_app_current_date()).days
        
        line = f"- [{goal['priority']} Priority] {goal['race_name']} - {race_date} ({days_away} days away)"
        if goal['race_type']:
            line += f" | {goal['race_type']}"
        if goal['target_time']:
            line += f" | Target: {goal['target_time']}"
        if goal['elevation_gain_feet']:
            line += f" | Vert: {goal['elevation_gain_feet']:,} ft"
        lines.append(line)
    
    return "\n".join(lines)


def format_race_history_for_prompt(race_history: List[Dict], trend: Dict) -> str:
    """Format race history with trend analysis for LLM prompt."""
    if not race_history:
        return "No race history available."
    
    lines = [f"Performance Trend: {trend['trend'].upper()} - {trend['details']}\n"]
    lines.append("Recent Race Results:")
    
    for race in race_history[:5]:  # Show last 5
        pace = race['finish_time_minutes'] / race['distance_miles']
        hours = int(race['finish_time_minutes'] // 60)
        mins = int(race['finish_time_minutes'] % 60)
        
        lines.append(
            f"- {race['race_date']}: {race['race_name']} "
            f"({race['distance_miles']:.1f} mi) - {hours}h {mins}m "
            f"(~{pace:.1f} min/mi)"
        )
    
    return "\n".join(lines)


def format_training_schedule_for_prompt(schedule_data: Optional[Dict]) -> str:
    """Format training schedule for LLM prompt with multi-discipline support."""
    if not schedule_data or not schedule_data.get('schedule'):
        return "Training schedule not configured - assume 5-6 days/week availability."

    sched = schedule_data['schedule']
    lines = []

    if sched.get('total_hours_per_week'):
        lines.append(f"Total Weekly Training Time: {sched['total_hours_per_week']} hours")

    if sched.get('available_days'):
        days = ', '.join(sched['available_days'])
        lines.append(f"Available Days: {days}")

    if sched.get('long_run_days'):
        long_run_days = ', '.join(sched['long_run_days'])
        lines.append(f"Long Run Days (90+ min): {long_run_days}")

    if sched.get('constraints'):
        lines.append(f"Constraints: {sched['constraints']}")

    # Supplemental training
    supps = []
    if schedule_data.get('include_strength'):
        supps.append(f"Strength: {schedule_data['strength_hours']}h/week")
    if schedule_data.get('include_mobility'):
        supps.append(f"Mobility: {schedule_data['mobility_hours']}h/week")

    # Multi-discipline cross-training
    cross_training_disciplines = schedule_data.get('cross_training_disciplines', [])
    if cross_training_disciplines:
        for d in cross_training_disciplines:
            discipline_name = d['discipline'].replace('_', ' ').title()
            if d['allocation_type'] == 'hours':
                supps.append(f"{discipline_name}: {d['allocation_value']}h/week")
            else:
                supps.append(f"{discipline_name}: {d['allocation_value']}% of training time")
    elif schedule_data.get('include_cross_training'):
        # Fallback to legacy single cross-training for backward compatibility
        supps.append(f"{schedule_data['cross_training_type']}: {schedule_data['cross_training_hours']}h/week")

    if supps:
        lines.append(f"Supplemental Training: {', '.join(supps)}")

    return "\n".join(lines)


def format_journal_observations_for_prompt(observations: List[Dict]) -> str:
    """Format recent journal observations for LLM prompt."""
    if not observations:
        return "No recent journal entries."
    
    lines = ["Recent Training Response:"]
    for obs in observations[:5]:  # Last 5 days
        energy = obs.get('energy_level', 'N/A')
        rpe = obs.get('rpe_score', 'N/A')
        pain = obs.get('pain_percentage')
        
        line = f"- {obs['date']}: Energy {energy}/5, RPE {rpe}/10"
        if pain is not None and pain > 0:
            line += f", Pain {pain}%"
        if obs.get('notes'):
            line += f" | Notes: {obs['notes'][:50]}"
        lines.append(line)
    
    return "\n".join(lines)


def get_prior_week_summaries(user_id: int, target_week_start, n: int = 3) -> list:
    """Return last n completed weeks of strategic_summary + synthesis for training arc context."""
    rows = execute_query(
        """
        SELECT week_start_date, strategic_summary, weekly_synthesis
        FROM weekly_programs
        WHERE user_id = %s
          AND week_start_date < %s
          AND strategic_summary IS NOT NULL
        ORDER BY week_start_date DESC
        LIMIT %s
        """,
        (user_id, str(target_week_start), n),
        fetch=True
    )
    return rows or []


def _divergence_trend_label(activities: list, days: int = 7) -> str:
    """Return directional divergence trajectory label from recent activity data.

    Compares first-half vs second-half of recent divergence readings to determine
    whether internal stress is accumulating, clearing, or stable.
    Returns one of: 'accumulating (trending negative, Δ{x})',
                    'clearing (trending positive, Δ{x})',
                    'balanced (stable, Δ{x})', or 'insufficient data'.
    """
    cutoff = str(date.today() - timedelta(days=days))
    recent = []
    for a in activities:
        a_date = a.get('date')
        div = a.get('normalized_divergence')
        if a_date and str(a_date) >= cutoff and div is not None:
            try:
                recent.append(float(div))
            except (TypeError, ValueError):
                pass
    if len(recent) < 3:
        return 'insufficient data'
    mid = len(recent) // 2
    first_avg = sum(recent[:mid]) / mid
    second_avg = sum(recent[mid:]) / (len(recent) - mid)
    delta = second_avg - first_avg
    if delta < -0.05:
        return f'accumulating (trending negative, \u0394{delta:.2f})'
    elif delta > 0.05:
        return f'clearing (trending positive, \u0394{delta:.2f})'
    return f'balanced (stable, \u0394{delta:.2f})'


def _derive_assessment_category(pattern_flags: dict, current_metrics: dict, thresholds: dict) -> str:
    """Map current athlete state to one of six assessment categories for guide filtering.

    Priority order mirrors the risk hierarchy used in daily recommendations.
    Uses athlete-personalized thresholds from apply_athlete_model_to_thresholds().
    """
    red_flags = pattern_flags.get('red_flags', [])
    warnings = pattern_flags.get('warnings', [])
    divergence = current_metrics.get('normalized_divergence') or 0.0

    if any('ACWR elevation' in f or 'mandatory' in f.lower() for f in red_flags):
        return 'mandatory_rest'
    if any('DIVERGENCE DRIFT' in f for f in red_flags):
        return 'overtraining_risk'
    if (current_metrics.get('external_acwr') or 0) > thresholds.get('acwr_high_risk', 1.5):
        return 'high_acwr_risk'
    if any('insufficient' in f.lower() for f in red_flags + warnings):
        return 'recovery_needed'
    if divergence > abs(thresholds.get('divergence_overtraining', 0.15)):
        return 'undertraining_opportunity'
    return 'normal_progression'


def format_training_progression_for_prompt(prior_weeks: list) -> str:
    """Format last N weeks of strategic_summary + synthesis as a compact training arc block."""
    if not prior_weeks:
        return "No prior week data available."
    lines = []
    for row in reversed(prior_weeks):  # oldest first
        d = dict(row)
        week_date = d.get('week_start_date')
        if hasattr(week_date, 'strftime'):
            week_label = week_date.strftime('%b %d')
        else:
            week_label = str(week_date)
        summary = d.get('strategic_summary') or {}
        if isinstance(summary, str):
            try:
                summary = json.loads(summary)
            except (json.JSONDecodeError, ValueError):
                summary = {}
        stage = summary.get('training_stage', '?')
        intensity = summary.get('weekly_intensity_target', '?')
        load_low = summary.get('load_target_low', '?')
        load_high = summary.get('load_target_high', '?')
        key_sessions = summary.get('key_sessions', [])
        ks_str = ', '.join(
            f"{s.get('day','?')} — {s.get('type','?')}" for s in key_sessions
        ) if key_sessions else 'none'
        synthesis = d.get('weekly_synthesis') or ''
        # One-sentence snippet: first sentence of synthesis
        snippet = synthesis.split('.')[0].strip() + '.' if synthesis else 'no synthesis'
        lines.append(
            f"{week_label} ({stage}/{intensity}, ACWR {load_low}–{load_high}): "
            f"Key: {ks_str} | {snippet}"
        )
    return "\n".join(lines)


def build_weekly_program_prompt(
    user_id: int,
    target_week_start: date
) -> str:
    """
    Build comprehensive prompt for weekly training program generation.
    
    Returns:
        Prompt string for Claude API
    """
    logger.info(f"Building weekly program prompt for user {user_id}, week starting {target_week_start}")

    # Fetch all context data
    current_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)
    activities = UnifiedMetricsService.get_recent_activities_for_analysis(days=28, user_id=user_id)

    # Compute long run ceiling from last 30 days of running activities
    activities_30d = execute_query(
        """
        SELECT distance_miles FROM activities
        WHERE user_id = %s
          AND date >= CURRENT_DATE - INTERVAL '30 days'
          AND (sport_type = 'running' OR sport_type IS NULL)
          AND distance_miles IS NOT NULL AND distance_miles > 0
        ORDER BY distance_miles DESC
        LIMIT 1
        """,
        (user_id,),
        fetch=True
    )
    max_30d_long_run = float(activities_30d[0]['distance_miles']) if activities_30d else None
    long_run_ceiling = round(max_30d_long_run * 1.1, 1) if max_30d_long_run else None
    race_goals = get_race_goals(user_id)
    race_history = get_race_history(user_id)
    perf_trend = calculate_performance_trend(race_history)
    training_schedule = get_training_schedule(user_id)
    training_stage = get_current_training_stage(user_id)
    journal_obs = get_recent_journal_observations(user_id)

    # Get personalization data (from Dashboard LLM system)
    risk_tolerance = get_user_recommendation_style(user_id)
    thresholds = get_adjusted_thresholds(risk_tolerance)
    thresholds = apply_athlete_model_to_thresholds(thresholds, user_id)
    autopsy_insights = get_recent_autopsy_insights(user_id, days=28)
    pattern_flags = analyze_pattern_flags(activities, current_metrics, user_id, thresholds)

    # Filter training guide to state-relevant sections
    assessment_category = _derive_assessment_category(pattern_flags, current_metrics, thresholds)
    training_guide = _select_guide_sections(load_training_guide(), assessment_category)
    logger.info(f"Training guide filtered for category: {assessment_category}")

    # Get coaching tone
    spectrum_value = get_user_coaching_spectrum(user_id)
    tone_instructions = get_coaching_tone_instructions(spectrum_value)

    # Get athlete model context block (personalized divergence window, alignment history)
    athlete_model_context = get_athlete_model_context(user_id)

    # Get user's ACWR configuration for accurate load window labels
    try:
        acwr_config = ACWRConfigurationService().get_user_configuration(user_id)
        chronic_days = acwr_config['chronic_period_days'] if acwr_config else 28
        decay_rate = acwr_config['decay_rate'] if acwr_config else None
    except Exception:
        chronic_days = 28
        decay_rate = None

    # Get athlete profile fields not covered by other fetches
    athlete_profile_data = execute_query(
        "SELECT training_experience, age FROM user_settings WHERE id = %s",
        (user_id,),
        fetch=True
    )

    # Get prior week: strategic_summary + synthesis in one query
    prior_week_rows = execute_query(
        """
        SELECT strategic_summary, weekly_synthesis, deviation_log, week_start_date
        FROM weekly_programs
        WHERE user_id = %s
          AND week_start_date < %s
          AND strategic_summary IS NOT NULL
        ORDER BY week_start_date DESC
        LIMIT 1
        """,
        (user_id, str(target_week_start)),
        fetch=True
    )
    prior_week = prior_week_rows[0] if prior_week_rows else None

    # Get last 3 weeks of strategic summaries for training arc context
    prior_weeks = get_prior_week_summaries(user_id, target_week_start, n=3)

    athlete_experience = athlete_profile_data[0]['training_experience'].capitalize() if (athlete_profile_data and athlete_profile_data[0].get('training_experience')) else "Intermediate"
    athlete_age = athlete_profile_data[0]['age'] if (athlete_profile_data and athlete_profile_data[0].get('age')) else None

    # Build prompt sections
    week_end = target_week_start + timedelta(days=6)

    # Format metrics with proper handling of None/missing values
    def format_metric(value, format_spec):
        """Format a metric value or return 'N/A' if not a number."""
        if value is not None and isinstance(value, (int, float)):
            return format(value, format_spec)
        return 'N/A'

    ext_acwr = format_metric(current_metrics.get('external_acwr'), '.2f')
    int_acwr = format_metric(current_metrics.get('internal_acwr'), '.2f')
    norm_div = format_divergence_for_prompt(current_metrics.get('normalized_divergence'))
    seven_day = format_metric(current_metrics.get('seven_day_avg'), '.1f')
    twentyeight_day = format_metric(current_metrics.get('twentyeight_day_avg'), '.1f')
    days_since_rest = current_metrics.get('days_since_rest', 'N/A')

    # Format personalized divergence thresholds
    div_moderate_risk = thresholds.get('divergence_moderate_risk', -0.05)
    div_overtraining = thresholds.get('divergence_overtraining', -0.15)

    # Divergence trajectory from recent activity data
    div_trend = _divergence_trend_label(activities or [], days=7)

    # Format prior week structured targets
    if prior_week:
        pw = dict(prior_week)
        pw_summary = pw.get('strategic_summary') or {}
        if isinstance(pw_summary, str):
            try:
                pw_summary = json.loads(pw_summary)
            except (json.JSONDecodeError, ValueError):
                pw_summary = {}
        pw_date = pw.get('week_start_date')
        pw_label = pw_date.strftime('%b %d') if hasattr(pw_date, 'strftime') else str(pw_date)
        pw_stage = pw_summary.get('training_stage', '?')
        pw_intensity = pw_summary.get('weekly_intensity_target', '?')
        pw_load_low = pw_summary.get('load_target_low', '?')
        pw_load_high = pw_summary.get('load_target_high', '?')
        pw_key = ', '.join(
            f"{s.get('day','?')} — {s.get('type','?')}"
            for s in (pw_summary.get('key_sessions') or [])
        ) or 'none'
        pw_notes = pw_summary.get('strategic_notes', '')
        pw_synthesis = pw.get('weekly_synthesis') or ''
        pw_deviations = len(pw.get('deviation_log') or [])
        prior_week_section = (
            f"Week of {pw_label}: Stage={pw_stage} | Intensity={pw_intensity} | "
            f"ACWR target={pw_load_low}–{pw_load_high}\n"
            f"Key sessions: {pw_key}\n"
            f"Notes: \"{pw_notes}\"\n"
            f"Deviations logged: {pw_deviations}\n"
            f"Synthesis: {pw_synthesis}"
        )
    else:
        prior_week_section = "No prior week data available — this is either the first week or synthesis has not yet run."

    decay_str = f" | Decay rate: {decay_rate:.3f}" if decay_rate is not None else ""
    
    prompt = f"""You are an expert ultra-trail running coach creating a divergence-optimized weekly training program.

**ATHLETE PROFILE**

Training Week: {target_week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}
Athlete Age: {f"{athlete_age} years old" if athlete_age else "Not specified"}
Experience Level: {athlete_experience}
Risk Tolerance: {risk_tolerance.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days

**PRIMARY METRICS**

DIVERGENCE SIGN CONVENTION: {NORMALIZED_DIVERGENCE_FORMULA}

PRIMARY SIGNAL — Normalized Divergence: {norm_div}
(Positive = untapped capacity; Negative = internal stress accumulating)
Productive window: divergence > {div_moderate_risk:.3f} | Breakdown floor: {div_overtraining:.3f}
Recent trajectory (7d): {div_trend}

External ACWR: {ext_acwr} | Internal ACWR: {int_acwr} | Days Since Rest: {days_since_rest}
Acute load (7d): {seven_day} mi | Chronic load ({chronic_days}d): {twentyeight_day} mi{decay_str}

**ATHLETE MODEL**

{athlete_model_context if athlete_model_context else "Athlete model not yet available — using population defaults."}

**PATTERN ANALYSIS**

Red Flags: {', '.join(pattern_flags['red_flags']) if pattern_flags.get('red_flags') else 'None detected'}
Positive Patterns: {', '.join(pattern_flags['positive_patterns']) if pattern_flags.get('positive_patterns') else 'None identified'}
Warnings: {', '.join(pattern_flags['warnings']) if pattern_flags.get('warnings') else 'None'}
Guide context: {assessment_category}

**AUTOPSY LEARNING (last 28 days)**

{f"Analyses: {autopsy_insights['count']} autopsies | Avg Alignment: {autopsy_insights['avg_alignment']}/10 | Trend: {autopsy_insights.get('alignment_trend', [])}" if autopsy_insights else "No autopsy data available"}
{(lambda rb: f"Deviation causes: {', '.join(f'{v} {k}' for k, v in rb.items() if v > 0) or 'none classified'}")(autopsy_insights['reason_breakdown']) if autopsy_insights and autopsy_insights.get('reason_breakdown') else ""}
{f"Key learning: {autopsy_insights['latest_insights']}" if autopsy_insights and autopsy_insights.get('latest_insights') else ""}

**PRIOR WEEK PLAN TARGETS**

{prior_week_section}

**TRAINING ARC (last 3 weeks)**

{format_training_progression_for_prompt(prior_weeks)}

**RACE GOALS**

{format_race_goals_for_prompt(race_goals)}

**PERFORMANCE HISTORY**

{format_race_history_for_prompt(race_history, perf_trend)}

**CURRENT TRAINING STAGE**

Stage: {training_stage.get('stage', 'Unknown')}
Weeks to Primary Race: {training_stage.get('weeks_to_race', 'N/A')}
Race: {training_stage.get('race_name', 'N/A')}
Focus: {training_stage.get('details', 'N/A')}

**TRAINING SCHEDULE & AVAILABILITY**

{format_training_schedule_for_prompt(training_schedule)}

**RECENT TRAINING RESPONSE**

{format_journal_observations_for_prompt(journal_obs)}

**TRAINING REFERENCE FRAMEWORK**

{training_guide if training_guide else "Use evidence-based ultrarunning training principles"}

**COACHING TONE**

{tone_instructions}

**YOUR TASK**

Generate a divergence-optimized 7-day training program for the week of {target_week_start.strftime('%B %d, %Y')}.

**KEY PRINCIPLES:**

1. **Divergence-First Planning**: Primary target is normalized divergence above {div_moderate_risk:.3f} (productive window). Below {div_overtraining:.3f} = breakdown risk — reduce load or intensity. Use the athlete model's personalized window, not population defaults.
2. **ACWR Safety Rails**: Keep external ACWR 0.8–1.3; never exceed {thresholds['acwr_high_risk']} for this athlete.
3. **Training Arc Continuity**: Build on the prior week's prescription. Assess whether to progress, consolidate, or recover based on the training arc and synthesis.
4. **Schedule Integration**: Respect athlete's availability and time constraints.
5. **Race Goal Alignment**: Structure the week toward the primary race goal given current stage and weeks remaining.
6. **Recovery Integration**: Plan rest/easy days based on current divergence trajectory and days since rest.
7. **Long Run Distance Ceiling (HARD CONSTRAINT)**: {f"The athlete's longest run in the past 30 days is {max_30d_long_run:.1f} miles. The prescribed long run must not exceed {long_run_ceiling:.1f} miles ({max_30d_long_run:.1f} × 1.10). It must also not exceed 1/3 of your planned total weekly mileage — check this after setting weekly volume and reduce if needed." if long_run_ceiling else "No recent long run data available — be conservative; prescribe no more than 10 miles for a long run until training history is established."}
8. **Hard Session Recovery Buffer (HARD CONSTRAINT)**: High-intensity sessions (Tempo Run, Interval/Speed Work, Hill Repeats) and Long Runs all require 48 hours of recovery before the next hard session. Never place two hard sessions on consecutive days. A Long Run on Saturday means Friday must be Easy/Recovery/Rest, and Sunday must be Easy/Recovery/Rest.

**REQUIRED OUTPUT FORMAT (JSON):**

Return your response as a valid JSON object with this exact structure:

{{
  "week_start_date": "{target_week_start.isoformat()}",
  "week_summary": "2-3 sentences: this week's focus, why, and how it builds toward the race goal.",
  "predicted_metrics": {{
    "acwr_estimate": 1.05,
    "external_acwr_estimate": 1.05,
    "internal_acwr_estimate": 0.98,
    "divergence_estimate": 0.02,
    "total_weekly_miles": 45
  }},
  "daily_program": [
    {{
      "day": "Sunday",
      "date": "{target_week_start.isoformat()}",
      "workout_type": "Easy Run",
      "description": "6 miles easy, conversational pace, flat terrain",
      "duration_estimate": "60-70 minutes",
      "intensity": "Low",
      "distance_miles": 6.0,
      "elevation_gain_feet": 200,
      "key_focus": "Recovery from weekend, maintain aerobic base",
      "terrain_notes": "Flat trails or road"
    }}
  ],
  "key_workouts_this_week": [
    "Tuesday: Long run building toward race distance",
    "Thursday: Tempo work for lactate threshold development"
  ],
  "nutrition_reminder": "Brief nutrition guidance for this week's training load",
  "injury_prevention_note": "Key consideration for staying healthy this week"
}}

**IMPORTANT:**
- Return ONLY the JSON object, no markdown formatting, no extra text
- Ensure all 7 days (Sunday-Saturday) are included in daily_program
- Workout types: Long Run, Easy Run, Tempo Run, Interval/Speed Work, Hill Repeats, Recovery Run, Rest Day, Cross-Training
- Intensity levels: Low, Moderate, High
- Be specific with distances, paces, and terrain rationale
- Ensure the program is realistic for the athlete's current fitness and schedule
- For external_acwr_estimate and internal_acwr_estimate: use the External ACWR and Internal ACWR values provided in the athlete metrics above as your starting point, adjusted for the planned weekly load

Generate the weekly program now:"""

    return prompt


def parse_weekly_program_response(response_text: str) -> Dict:
    """
    Parse Claude's response to extract weekly program JSON.
    
    Returns:
        Parsed program dictionary or raises ValueError
    """
    import re
    
    # Strip markdown code fences if present (Claude sometimes wraps JSON in ```json)
    cleaned_text = response_text.strip()
    json_match = re.search(r'```json\s*(.*?)\s*```', cleaned_text, re.DOTALL)
    if json_match:
        cleaned_text = json_match.group(1).strip()
        logger.info("Stripped markdown code fences from response")
    
    try:
        # Try to parse as JSON directly
        program = json.loads(cleaned_text)
        
        # Validate required fields
        required_fields = ['week_start_date', 'week_summary', 'predicted_metrics', 'daily_program']
        for field in required_fields:
            if field not in program:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate daily_program has 7 days
        if len(program['daily_program']) != 7:
            logger.warning(f"Expected 7 days in program, got {len(program['daily_program'])}")
        
        logger.info("Successfully parsed weekly program JSON")
        return program
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Response text: {response_text[:500]}")
        
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                program = json.loads(json_match.group(1))
                logger.info("Extracted JSON from markdown code block")
                return program
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not parse weekly program response: {e}")


def generate_weekly_program(
    user_id: int,
    target_week_start: Optional[date] = None,
    force_regenerate: bool = False
) -> Dict:
    """
    Generate a weekly training program using Claude API.
    
    Args:
        user_id: User ID
        target_week_start: Sunday of target week (defaults to current or most recent Sunday)
        force_regenerate: If True, bypass cache and regenerate (used for mid-week adjustments)

    Returns:
        Dictionary containing program data and metadata
    """
    # Default to the current week's Sunday (week structure is Sunday-Saturday)
    if target_week_start is None:
        target_week_start = get_current_week_start()
    
    logger.info(f"Generating weekly program for user {user_id}, week starting {target_week_start}")
    
    # Build prompt
    prompt = build_weekly_program_prompt(user_id, target_week_start)
    
    # Call Claude API with extended timeout for complex weekly program generation
    try:
        response_text = call_anthropic_api(
            prompt,
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=WEEKLY_PROGRAM_TEMPERATURE,  # Use optimized temperature for JSON structure
            timeout=90  # Extended timeout: weekly programs are complex and take longer
        )
        
        # Parse response
        program = parse_weekly_program_response(response_text)
        
        # Fix dates to match week_start_date (LLM might generate incorrect dates)
        # Calculate correct dates for Sunday-Saturday of the target week
        days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        for i, workout in enumerate(program.get('daily_program', [])):
            correct_date = target_week_start + timedelta(days=i)
            workout['date'] = correct_date.strftime('%Y-%m-%d')
            # Ensure day name matches the actual calendar date
            workout['day'] = days_of_week[i]
        
        # Override LLM-generated totals with server-side sums of structured per-day fields
        _apply_structured_totals(program)

        # Ensure week_start_date matches target
        program['week_start_date'] = target_week_start.strftime('%Y-%m-%d')
        
        # Add metadata
        program['generated_at'] = datetime.now().isoformat()
        program['user_id'] = user_id
        program['raw_response'] = response_text
        
        logger.info(f"Successfully generated weekly program for week starting {target_week_start}")
        return program
        
    except Exception as e:
        logger.error(f"Failed to generate weekly program: {e}", exc_info=True)
        raise


def _extract_and_store_strategic_summary(user_id: int, week_start, program_data: Dict) -> None:
    """Extract a structured strategic_summary from the generated plan via Haiku.

    Makes a single short Haiku call to parse the weekly plan into a compact
    JSON context snapshot, then persists it via upsert_week_strategic_summary.

    This is an internal helper — never call directly. Always wrapped in
    try/except by save_weekly_program so extraction failure is non-fatal.

    Args:
        user_id: User ID (used for logging only here).
        week_start: Sunday date of the target week.
        program_data: Full program dict from generate_weekly_program.
    """
    # Build a compact text representation of the plan for Haiku to parse
    plan_text_parts = []
    plan_text_parts.append(f"Week start: {program_data.get('week_start_date', str(week_start))}")

    if program_data.get('training_phase'):
        plan_text_parts.append(f"Training phase: {program_data['training_phase']}")
    if program_data.get('weekly_overview'):
        plan_text_parts.append(f"Overview: {program_data['weekly_overview']}")

    daily = program_data.get('daily_program', [])
    for day_plan in daily:
        day_name = day_plan.get('day', '')
        workout_type = day_plan.get('workout_type', day_plan.get('type', ''))
        notes = day_plan.get('description', day_plan.get('notes', ''))
        plan_text_parts.append(f"  {day_name}: {workout_type} — {notes}")

    predicted = program_data.get('predicted_metrics', {})
    if predicted:
        plan_text_parts.append(
            f"Predicted ACWR: {predicted.get('acwr_estimate')}, "
            f"Divergence: {predicted.get('divergence_estimate')}"
        )

    plan_text = "\n".join(plan_text_parts)

    extraction_prompt = f"""You are a training analytics assistant. Given the weekly training plan below, extract a JSON object with EXACTLY these fields. Return ONLY the JSON — no explanation, no markdown fences.

{{
  "training_stage": "<string: e.g. base, build, peak, taper, recovery>",
  "weeks_to_a_race": <integer or null>,
  "weekly_intensity_target": "<easy|moderate|hard|peak>",
  "key_sessions": [
    {{"day": "<day name>", "type": "<session type>", "notes": "<brief notes>"}}
  ],
  "load_target_low": <float between 0.5 and 1.5>,
  "load_target_high": <float between 0.5 and 1.5>,
  "strategic_notes": "<one concise sentence of coaching rationale>"
}}

Rules:
- key_sessions: include only the 1–3 most important sessions (not rest days).
- weekly_intensity_target: infer from overall session mix.
- load_target_low / load_target_high: ACWR range this week targets (e.g. 0.85 / 1.05).
- strategic_notes: max 120 characters.
- weeks_to_a_race: null if no race goal is evident.

Weekly plan:
{plan_text}
"""

    response_text = call_anthropic_api(
        extraction_prompt,
        model=MODEL_HAIKU,
        temperature=0.1,
        max_tokens=400,
        timeout=20,
    )

    if not response_text or not response_text.strip():
        raise ValueError("Empty response from Haiku for strategic summary extraction")

    # Strip any accidental markdown fences before parsing
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    strategic_summary = json.loads(clean)

    # Validate required keys are present
    required_keys = {
        'training_stage', 'weeks_to_a_race', 'weekly_intensity_target',
        'key_sessions', 'load_target_low', 'load_target_high', 'strategic_notes'
    }
    missing = required_keys - set(strategic_summary.keys())
    if missing:
        raise ValueError(f"Strategic summary missing required keys: {missing}")

    upsert_week_strategic_summary(user_id, week_start, strategic_summary)
    logger.info(
        f"Strategic summary stored for user {user_id}, week {week_start}: "
        f"stage={strategic_summary.get('training_stage')}, "
        f"intensity={strategic_summary.get('weekly_intensity_target')}"
    )


def save_weekly_program(
    user_id: int,
    week_start: date,
    program_data: Dict,
    generation_type: str = 'scheduled'
) -> int:
    """
    Save weekly program to database.
    
    Args:
        user_id: User ID
        week_start: Sunday of the week
        program_data: Program dictionary from generate_weekly_program
        generation_type: 'scheduled' or 'manual'
    
    Returns:
        ID of saved program
    """
    query = """
        INSERT INTO weekly_programs 
        (user_id, week_start_date, program_json, predicted_acwr, predicted_divergence, 
         generated_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id, week_start_date) 
        DO UPDATE SET 
            program_json = EXCLUDED.program_json,
            predicted_acwr = EXCLUDED.predicted_acwr,
            predicted_divergence = EXCLUDED.predicted_divergence,
            generated_at = NOW()
        RETURNING id
    """
    
    # Extract predictions
    predicted_metrics = program_data.get('predicted_metrics', {})
    predicted_acwr = predicted_metrics.get('acwr_estimate')
    predicted_divergence = predicted_metrics.get('divergence_estimate')
    
    # Convert program to JSON string
    program_json = json.dumps(program_data)
    
    result = execute_query(
        query,
        (user_id, week_start, program_json, predicted_acwr, predicted_divergence),
        fetch=True
    )
    
    if result and len(result) > 0:
        # Handle both dict and tuple result formats
        program_id = result[0]['id'] if hasattr(result[0], 'keys') else result[0][0]
    else:
        program_id = None
    
    logger.info(f"Saved weekly program {program_id} for user {user_id}, week {week_start}")

    # --- Phase A: Extract and store strategic_summary via Haiku ---
    # Wrap in try/except so extraction failure never breaks weekly plan generation.
    try:
        _extract_and_store_strategic_summary(user_id, week_start, program_data)
    except Exception as summary_err:
        logger.warning(
            f"Strategic summary extraction failed for user {user_id}, "
            f"week {week_start} — plan saved successfully, summary skipped: {summary_err}"
        )

    return program_id


def get_cached_weekly_program(
    user_id: int,
    week_start: date
) -> Optional[Dict]:
    """
    Get cached weekly program if it exists and is recent.
    
    Args:
        user_id: User ID
        week_start: Sunday of target week
    
    Returns:
        Program dictionary or None if not cached/expired
    """
    query = """
        SELECT program_json, generated_at
        FROM weekly_programs
        WHERE user_id = %s
        AND week_start_date = %s
        AND generated_at >= NOW() - INTERVAL '%s days'
        ORDER BY generated_at DESC
        LIMIT 1
    """
    
    result = execute_query(query, (user_id, week_start, CACHE_EXPIRY_DAYS), fetch=True)
    
    if not result:
        logger.info(f"No cached program found for user {user_id}, week {week_start}")
        return None
    
    # Handle both dict and tuple result formats
    row = result[0]
    if hasattr(row, 'keys'):
        program_json = row['program_json']
        generated_at = row['generated_at']
    else:
        program_json = row[0]
        generated_at = row[1]
    
    # Parse JSON
    if isinstance(program_json, str):
        program = json.loads(program_json)
    else:
        program = program_json
    
    logger.info(f"Found cached program for user {user_id}, week {week_start}, generated {generated_at}")
    return program


def get_or_generate_weekly_program(
    user_id: int,
    week_start: Optional[date] = None,
    force_regenerate: bool = False
) -> Dict:
    """
    Get weekly program from cache or generate new one.
    
    Args:
        user_id: User ID
        week_start: Sunday of target week (defaults to current or most recent Sunday)
        force_regenerate: Force new generation even if cached

    Returns:
        Program dictionary with metadata
    """
    # Default to the current week's Sunday (week structure is Sunday-Saturday)
    if week_start is None:
        week_start = get_current_week_start()

    # Check cache first
    if not force_regenerate:
        cached = get_cached_weekly_program(user_id, week_start)
        if cached:
            cached['from_cache'] = True
            _apply_structured_totals(cached)
            return cached

    # Generate new program
    logger.info(f"Generating new weekly program for user {user_id}, week {week_start}")
    program = generate_weekly_program(user_id, week_start)

    # Save to database
    try:
        save_weekly_program(user_id, week_start, program)
        program['from_cache'] = False
    except Exception as e:
        logger.error(f"Failed to save program to database: {e}")
        # Return program anyway, just don't cache it
        program['from_cache'] = False

    return program


def _apply_structured_totals(program: Dict) -> None:
    """Override LLM-guessed totals with server-side sums of per-day structured fields.

    Mutates program in-place. No-ops if daily_program has no distance_miles data
    (old plans without structured fields retain their LLM-generated values).
    """
    daily = program.get('daily_program', [])
    total_miles = sum(float(w.get('distance_miles') or 0) for w in daily)
    total_vert = sum(float(w.get('elevation_gain_feet') or 0) for w in daily)
    if 'predicted_metrics' not in program:
        program['predicted_metrics'] = {}
    if total_miles > 0:
        program['predicted_metrics']['total_weekly_miles'] = round(total_miles, 1)
    if total_vert > 0:
        program['predicted_metrics']['total_weekly_elevation_feet'] = round(total_vert)


def generate_weekly_synthesis(user_id: int, week_start: date) -> Optional[str]:
    """Generate a retrospective weekly synthesis narrative for the completed week.

    Compares what was planned (strategic_summary) against what actually happened
    (activities + journal entries). Returns a 150-200 word narrative or None on failure.
    Called by the Saturday cron — non-fatal if it fails.
    """
    try:
        week_end = week_start + timedelta(days=6)

        # --- What was planned ---
        planned_row = execute_query(
            """
            SELECT strategic_summary, program_json
            FROM weekly_programs
            WHERE user_id = %s AND week_start_date = %s
            """,
            (user_id, str(week_start)),
            fetch=True
        )
        strategic_summary = None
        if planned_row and planned_row[0]:
            raw = planned_row[0].get('strategic_summary')
            if isinstance(raw, dict):
                strategic_summary = raw
            elif isinstance(raw, str):
                try:
                    strategic_summary = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    pass

        # --- What actually happened ---
        activities = execute_query(
            """
            SELECT date, type, total_load_miles, distance_miles, elevation_gain_feet,
                   trimp, acute_chronic_ratio, normalized_divergence
            FROM activities
            WHERE user_id = %s AND date >= %s AND date <= %s
            ORDER BY date
            """,
            (user_id, str(week_start), str(week_end)),
            fetch=True
        )

        journal_obs = get_recent_journal_observations(user_id, days=7)

        # --- Current metrics for context ---
        metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)

        # --- Build prompt ---
        plan_section = "No plan was recorded for this week." if not strategic_summary else (
            f"Training stage: {strategic_summary.get('training_stage', 'unknown')}\n"
            f"Intensity target: {strategic_summary.get('weekly_intensity_target', 'unknown')}\n"
            f"Load target: {strategic_summary.get('load_target_low', '?')}–{strategic_summary.get('load_target_high', '?')} ACWR\n"
            f"Strategic notes: {strategic_summary.get('strategic_notes', 'none')}"
        )

        activity_lines = []
        total_load = 0.0
        for a in (activities or []):
            d = dict(a)
            load = float(d.get('total_load_miles') or 0)
            total_load += load
            div = d.get('normalized_divergence')
            div_str = f", div {div:.2f}" if div is not None else ""
            activity_lines.append(
                f"  {d['date']}: {d.get('type','?')} {load:.1f}mi load "
                f"(ACWR {d.get('acute_chronic_ratio') or 0:.2f}{div_str})"
            )
        activity_section = "\n".join(activity_lines) if activity_lines else "No activities recorded."

        journal_section = format_journal_observations_for_prompt(journal_obs) if journal_obs else "No journal entries this week."

        metrics_section = (
            f"End-of-week ACWR: {metrics.get('external_acwr', 'N/A')}\n"
            f"Divergence: {format_divergence_for_prompt(metrics.get('normalized_divergence'))}\n"
            f"Days since rest: {metrics.get('days_since_rest', 'N/A')}"
        ) if metrics else "Metrics unavailable."

        prompt = f"""You are an expert trail running coach writing a concise end-of-week synthesis for your athlete.

Week: {week_start.strftime('%B %d')} – {week_end.strftime('%B %d, %Y')}
Total training load: {total_load:.1f} load miles

WHAT WAS PLANNED:
{plan_section}

WHAT ACTUALLY HAPPENED:
{activity_section}

ATHLETE OBSERVATIONS THIS WEEK:
{journal_section}

END-OF-WEEK METRICS:
{metrics_section}

Write a retrospective synthesis of 150-200 words covering:
1. What the athlete actually did vs what was planned (alignment assessment)
2. Key physiological patterns that emerged (ACWR trend, divergence signals, fatigue)
3. What this week teaches us about the athlete's current adaptation state
4. One forward-looking observation for next week

Write in second person ("you"), use plain text (no markdown), coaching tone. Be specific — reference actual numbers and dates. Do not list these as numbered points; write as flowing prose."""

        response = call_anthropic_api(prompt, max_tokens=400)
        if not response:
            return None

        synthesis = response.strip()

        # Persist to DB
        execute_query(
            """
            UPDATE weekly_programs
            SET weekly_synthesis = %s, synthesis_generated_at = NOW()
            WHERE user_id = %s AND week_start_date = %s
            """,
            (synthesis, user_id, str(week_start)),
            fetch=False
        )

        logger.info(f"Weekly synthesis stored for user {user_id}, week {week_start}")
        return synthesis

    except Exception as e:
        logger.error(f"Error generating weekly synthesis for user {user_id}: {e}")
        return None

