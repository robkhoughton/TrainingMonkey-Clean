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
from timezone_utils import get_app_current_date
from unified_metrics_service import UnifiedMetricsService
from db_utils import execute_query
from llm_recommendations_module import call_anthropic_api, load_training_guide, get_user_coaching_spectrum, get_coaching_tone_instructions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('coach_recommendations')

# Constants
CACHE_EXPIRY_DAYS = 3  # Weekly programs valid for 3 days
DEFAULT_MAX_TOKENS = 4000  # Longer for structured 7-day programs


def get_race_goals(user_id: int) -> List[Dict]:
    """Fetch user's race goals ordered by date."""
    query = """
        SELECT id, race_name, race_date, race_type, priority, target_time, notes
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
            'notes': row['notes']
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
    """Fetch user's training schedule from user_settings."""
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
    
    return {
        'schedule': schedule_json,
        'include_strength': row['include_strength_training'],
        'strength_hours': float(row['strength_hours_per_week']) if row['strength_hours_per_week'] else 0,
        'include_mobility': row['include_mobility'],
        'mobility_hours': float(row['mobility_hours_per_week']) if row['mobility_hours_per_week'] else 0,
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
        SELECT activity_date, energy_level, rpe_score, pain_percentage, user_notes
        FROM journal_entries
        WHERE user_id = %s
        AND activity_date >= CURRENT_DATE - INTERVAL '%s days'
        ORDER BY activity_date DESC
    """
    results = execute_query(query, (user_id, days), fetch=True)
    
    if not results:
        return []
    
    observations = []
    for row in results:
        observations.append({
            'date': row['entry_date'].isoformat() if hasattr(row['entry_date'], 'isoformat') else str(row['entry_date']),
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
    """Format training schedule for LLM prompt."""
    if not schedule_data or not schedule_data.get('schedule'):
        return "Training schedule not configured - assume 5-6 days/week availability."
    
    sched = schedule_data['schedule']
    lines = []
    
    if sched.get('total_hours_per_week'):
        lines.append(f"Total Weekly Training Time: {sched['total_hours_per_week']} hours")
    
    if sched.get('available_days'):
        days = ', '.join(sched['available_days'])
        lines.append(f"Available Days: {days}")
    
    if sched.get('constraints'):
        lines.append(f"Constraints: {sched['constraints']}")
    
    # Supplemental training
    supps = []
    if schedule_data.get('include_strength'):
        supps.append(f"Strength: {schedule_data['strength_hours']}h/week")
    if schedule_data.get('include_mobility'):
        supps.append(f"Mobility: {schedule_data['mobility_hours']}h/week")
    if schedule_data.get('include_cross_training'):
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
        pain = obs.get('pain_percentage', 0)
        
        line = f"- {obs['date']}: Energy {energy}/5, RPE {rpe}/10"
        if pain > 0:
            line += f", Pain {pain}%"
        if obs.get('notes'):
            line += f" | Notes: {obs['notes'][:50]}"
        lines.append(line)
    
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
    race_goals = get_race_goals(user_id)
    race_history = get_race_history(user_id)
    perf_trend = calculate_performance_trend(race_history)
    training_schedule = get_training_schedule(user_id)
    training_stage = get_current_training_stage(user_id)
    journal_obs = get_recent_journal_observations(user_id)
    training_guide = load_training_guide()
    
    # Get coaching tone
    spectrum_value = get_user_coaching_spectrum(user_id)
    tone_instructions = get_coaching_tone_instructions(spectrum_value)
    
    # Build prompt sections
    week_end = target_week_start + timedelta(days=6)
    
    prompt = f"""You are an expert ultra-trail running coach creating a divergence-optimized weekly training program.

**ATHLETE PROFILE & CURRENT STATUS**

Training Week: {target_week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}

Current Training Metrics (Last 28 Days):
- External ACWR: {current_metrics.get('external_acwr', 'N/A'):.2f}
- Internal ACWR: {current_metrics.get('internal_acwr', 'N/A'):.2f}
- Normalized Divergence: {current_metrics.get('normalized_divergence', 'N/A'):.3f}
- Days Since Rest: {current_metrics.get('days_since_rest', 'N/A')}
- 7-Day Avg Training Load: {current_metrics.get('seven_day_avg', 'N/A'):.1f} miles
- 28-Day Avg Training Load: {current_metrics.get('twentyeight_day_avg', 'N/A'):.1f} miles

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

1. **Divergence Optimization**: Target normalized divergence between -0.15 and +0.15 for the week
2. **ACWR Management**: Keep external ACWR between 0.8-1.3 (optimal) or provide rationale if exceeding
3. **Training Stage Alignment**: Structure workouts appropriate for current stage
4. **Schedule Integration**: Respect athlete's availability and time constraints
5. **Progressive Loading**: Build smartly toward race goals while managing fatigue
6. **Recovery Integration**: Plan rest/easy days based on current metrics and recent response

**REQUIRED OUTPUT FORMAT (JSON):**

Return your response as a valid JSON object with this exact structure:

{{
  "week_start_date": "{target_week_start.isoformat()}",
  "week_summary": "Brief overview of the week's focus and rationale (2-3 sentences)",
  "predicted_metrics": {{
    "acwr_estimate": 1.05,
    "divergence_estimate": 0.02,
    "total_weekly_miles": 45
  }},
  "daily_program": [
    {{
      "day": "Monday",
      "date": "{target_week_start.isoformat()}",
      "workout_type": "Easy Run",
      "description": "6 miles easy, conversational pace, flat terrain",
      "duration_estimate": "60-70 minutes",
      "intensity": "Low",
      "key_focus": "Recovery from weekend, maintain aerobic base",
      "terrain_notes": "Flat trails or road"
    }},
    // ... continue for all 7 days (Monday-Sunday)
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
- Ensure all 7 days (Monday-Sunday) are included
- Workout types: Long Run, Easy Run, Tempo Run, Interval/Speed Work, Hill Repeats, Recovery Run, Rest Day, Cross-Training
- Intensity levels: Low, Moderate, High
- Be specific with distances, paces, and rationale
- Ensure the program is realistic for the athlete's current fitness and schedule

Generate the weekly program now:"""
    
    return prompt


def parse_weekly_program_response(response_text: str) -> Dict:
    """
    Parse Claude's response to extract weekly program JSON.
    
    Returns:
        Parsed program dictionary or raises ValueError
    """
    try:
        # Try to parse as JSON directly
        program = json.loads(response_text.strip())
        
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
        target_week_start: Monday of target week (defaults to next Monday)
        force_regenerate: If True, bypass cache and regenerate (used for mid-week adjustments)
    
    Returns:
        Dictionary containing program data and metadata
    """
    # Default to next Monday if not specified
    if target_week_start is None:
        current_date = get_app_current_date()
        days_until_monday = (7 - current_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7  # If today is Monday, target next Monday
        target_week_start = current_date + timedelta(days=days_until_monday)
    
    logger.info(f"Generating weekly program for user {user_id}, week starting {target_week_start}")
    
    # Build prompt
    prompt = build_weekly_program_prompt(user_id, target_week_start)
    
    # Call Claude API
    try:
        response_text = call_anthropic_api(
            prompt,
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=0.7
        )
        
        # Parse response
        program = parse_weekly_program_response(response_text)
        
        # Add metadata
        program['generated_at'] = datetime.now().isoformat()
        program['user_id'] = user_id
        program['raw_response'] = response_text
        
        logger.info(f"Successfully generated weekly program for week starting {target_week_start}")
        return program
        
    except Exception as e:
        logger.error(f"Failed to generate weekly program: {e}", exc_info=True)
        raise


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
        week_start: Monday of the week
        program_data: Program dictionary from generate_weekly_program
        generation_type: 'scheduled' or 'manual'
    
    Returns:
        ID of saved program
    """
    query = """
        INSERT INTO weekly_programs 
        (user_id, week_start_date, program_json, predicted_acwr, predicted_divergence, 
         generated_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        ON CONFLICT (user_id, week_start_date) 
        DO UPDATE SET 
            program_json = EXCLUDED.program_json,
            predicted_acwr = EXCLUDED.predicted_acwr,
            predicted_divergence = EXCLUDED.predicted_divergence,
            updated_at = NOW()
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
    
    program_id = result[0][0] if result else None
    logger.info(f"Saved weekly program {program_id} for user {user_id}, week {week_start}")
    
    return program_id


def get_cached_weekly_program(
    user_id: int,
    week_start: date
) -> Optional[Dict]:
    """
    Get cached weekly program if it exists and is recent.
    
    Args:
        user_id: User ID
        week_start: Monday of target week
    
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
    
    program_json = result[0][0]
    generated_at = result[0][1]
    
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
        week_start: Monday of target week (defaults to next Monday)
        force_regenerate: Force new generation even if cached
    
    Returns:
        Program dictionary with metadata
    """
    # Default to next Monday
    if week_start is None:
        current_date = get_app_current_date()
        days_until_monday = (7 - current_date.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        week_start = current_date + timedelta(days=days_until_monday)
    
    # Check cache first
    if not force_regenerate:
        cached = get_cached_weekly_program(user_id, week_start)
        if cached:
            cached['from_cache'] = True
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

