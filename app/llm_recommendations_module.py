#!/usr/bin/env python3
"""
Enhanced LLM Recommendations Module for Training Monkey™ Dashboard.

This module uses the comprehensive Training Metrics Reference Guide to generate
sophisticated, evidence-based training recommendations through Claude API.
"""

import os
import json
import logging
import requests
from datetime import datetime, date, timedelta
import time
from timezone_utils import get_app_current_date
from unified_metrics_service import UnifiedMetricsService
from prompt_constants import NORMALIZED_DIVERGENCE_FORMULA, format_divergence_for_prompt

# Import database utilities
from db_utils import (
    execute_query,
    save_llm_recommendation,
    get_latest_recommendation,
    recommendation_needs_update,
    recommendation_is_stale,  # Phase 5: explicit date-based staleness check
    cleanup_old_recommendations,  # Updated from deprecated clear_old_recommendations
    get_last_activity_date,
    get_athlete_model,
    upsert_athlete_model,
    get_current_week_context,  # Phase B: Macro→Meso→Micro injection
    append_deviation_log,      # Phase C: Deviation classification
    set_revision_pending,      # Phase C: Deviation classification
    get_answered_alignment_queries,  # Phase D: preference feedback injection
)

# Setup logging - write to stdout for Cloud Logging visibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # NOTE: No filename parameter - logs to stdout/stderr for Cloud Run/Cloud Logging
)
logger = logging.getLogger('llm_recommendations')

# Constants
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-4-6"  # Claude Sonnet 4.6 - current balanced model
DEFAULT_VALID_DAYS = 1
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
ACTIVITY_ANALYSIS_DAYS = 28
RECOMMENDATION_TEMPERATURE = 0.7

# Model constants (Phase 2) — overridden from config.json after load
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_HAIKU = "claude-haiku-4-5-20251001"
MODEL_OPUS = "claude-opus-4-6"

def fix_dates_for_json(data):
    """Quick fix: Convert date objects to strings for JSON serialization"""
    from datetime import date, datetime

    if data is None:
        return data
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            result[key] = fix_dates_for_json(value)
        return result
    elif isinstance(data, list):
        return [fix_dates_for_json(item) for item in data]
    else:
        return data

def safe_date_parse(date_input):
    """
    Safely convert date input to datetime.date object
    Handles both strings and date objects after database DATE standardization

    CRITICAL: After PostgreSQL DATE migration, database returns date objects instead of strings
    This function ensures compatibility with both old string format and new date objects
    """

    if date_input is None:
        return None
    elif isinstance(date_input, str):
        # String format - parse it
        try:
            return datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format if needed
            return datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S').date()
    elif isinstance(date_input, date):
        # Already a date object
        return date_input
    elif hasattr(date_input, 'date') and callable(date_input.date):
        # It's a datetime object - extract date
        return date_input.date()
    else:
        # Last resort - convert to string and parse
        return datetime.strptime(str(date_input), '%Y-%m-%d').date()


def safe_datetime_parse(date_input):
    """Convert date input to datetime object for methods like isocalendar()"""
    from datetime import datetime, date

    if isinstance(date_input, str):
        return datetime.strptime(date_input, '%Y-%m-%d')
    elif isinstance(date_input, datetime):
        return date_input
    elif isinstance(date_input, date):
        return datetime.combine(date_input, datetime.min.time())
    else:
        return datetime.strptime(str(date_input), '%Y-%m-%d')

# Load the training guide content
def load_training_guide():
    """Load the Training Metrics Reference Guide content."""
    guide_path = os.path.join(os.path.dirname(__file__), "Training_Metrics_Reference_Guide.md")

    try:
        with open(guide_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Training guide not found at {guide_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading training guide: {str(e)}")
        return None


def _select_guide_sections(guide_text, assessment_category):
    """Return a filtered subset of the Training Guide relevant to assessment_category.

    Injects all core sections plus 1-2 Response Scenarios matching the situation.
    Always omits Weekly Strategic Analysis Examples — not relevant for daily recommendations.

    assessment_category values (from create_enhanced_prompt_with_tone):
        mandatory_rest, overtraining_risk, high_acwr_risk,
        recovery_needed, undertraining_opportunity, normal_progression
    """
    # Scenario mapping: category → which scenario numbers to inject
    SCENARIO_MAP = {
        'mandatory_rest':            ['Scenario 2', 'Scenario 6'],
        'overtraining_risk':         ['Scenario 2', 'Scenario 6'],
        'high_acwr_risk':            ['Scenario 2', 'Scenario 6'],
        'recovery_needed':           ['Scenario 6', 'Scenario 4'],
        'undertraining_opportunity': ['Scenario 1', 'Scenario 4'],
        'normal_progression':        ['Scenario 3', 'Scenario 5'],
    }
    target_scenarios = SCENARIO_MAP.get(assessment_category, ['Scenario 3', 'Scenario 5'])

    # Core sections — always included regardless of category
    CORE_SECTIONS = [
        'Decision Framework for Daily Training',
        'Advanced Pattern Recognition',
        'Data Quality Indicators',
        'Primary Metrics',
        'Secondary Metrics',
        'Wellness Metrics',
        'Optimal Ranges for Health and Performance',
        'Pattern Recognition',
        'Quick Assessment Protocol',
        'Masters Trail Runner Specifications (50+ years)',
    ]

    # Parse the guide into top-level sections by '## ' headers
    sections = {}
    current_key = None
    current_lines = []
    for line in guide_text.splitlines():
        if line.startswith('## '):
            if current_key is not None:
                sections[current_key] = '\n'.join(current_lines)
            current_key = line[3:].strip()
            current_lines = [line]
        else:
            if current_key is not None:
                current_lines.append(line)
    if current_key is not None:
        sections[current_key] = '\n'.join(current_lines)

    # Assemble core sections
    parts = []
    for name in CORE_SECTIONS:
        if name in sections:
            parts.append(sections[name])

    # Parse and inject only the matching Response Scenarios
    scenarios_section = sections.get('Claude Response Scenarios', '')
    selected_count = 0
    if scenarios_section:
        scenario_parts = {}
        current_skey = None
        current_slines = []
        for line in scenarios_section.splitlines():
            # Handle both '### Scenario N' and '###Scenario N' (guide has both)
            stripped = line.lstrip('#').strip()
            if (line.startswith('### Scenario') or line.startswith('###Scenario')):
                if current_skey:
                    scenario_parts[current_skey] = '\n'.join(current_slines)
                current_skey = stripped.split(':')[0].strip()  # e.g. 'Scenario 1'
                current_slines = [line]
            elif current_skey:
                current_slines.append(line)
        if current_skey:
            scenario_parts[current_skey] = '\n'.join(current_slines)

        selected = [scenario_parts[s] for s in target_scenarios if s in scenario_parts]
        if selected:
            parts.append('## Claude Response Scenarios')
            parts.extend(selected)
            selected_count = len(selected)

    # Weekly Strategic Analysis Examples intentionally omitted — not relevant for daily calls.

    total_chars = sum(len(p) for p in parts)
    logger.info(
        f"_select_guide_sections: category={assessment_category}, "
        f"scenarios={target_scenarios}, "
        f"core_sections={len(CORE_SECTIONS)}, scenario_count={selected_count}, "
        f"approx_chars={total_chars} (was ~28000)"
    )

    return '\n\n'.join(parts)


# Load configuration from config.json
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')
CONFIG = {}
try:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            CONFIG = json.load(f)

        # Get LLM settings
        LLM_SETTINGS = CONFIG.get('llm_settings', {})

        # Override defaults with config file values
        DEFAULT_MODEL = LLM_SETTINGS.get('model', DEFAULT_MODEL)
        RECOMMENDATION_TEMPERATURE = LLM_SETTINGS.get('temperature', RECOMMENDATION_TEMPERATURE)
        DEFAULT_VALID_DAYS = LLM_SETTINGS.get('valid_days', DEFAULT_VALID_DAYS)
        ACTIVITY_ANALYSIS_DAYS = LLM_SETTINGS.get('analysis_days', ACTIVITY_ANALYSIS_DAYS)

        # Override model constants from config
        MODEL_SONNET = LLM_SETTINGS.get('model_sonnet', MODEL_SONNET)
        MODEL_HAIKU = LLM_SETTINGS.get('model_haiku', MODEL_HAIKU)
        MODEL_OPUS = LLM_SETTINGS.get('model_opus', MODEL_OPUS)

        logger.info(f"Loaded configuration from {CONFIG_PATH}")
        logger.info(f"Using model: {DEFAULT_MODEL}, temperature: {RECOMMENDATION_TEMPERATURE}")
except Exception as e:
    logger.warning(f"Error loading config file: {str(e)}")
    logger.warning("Using default settings")


def get_api_key():
    """Get the Anthropic API key from environment variable or config file."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        try:
            if CONFIG and 'anthropic_api_key' in CONFIG:
                api_key = CONFIG['anthropic_api_key']
        except Exception as e:
            logger.error(f"Error loading API key from config file: {str(e)}")

    if not api_key:
        logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or add to config.json.")
        raise ValueError("Anthropic API key not found")

    # Strip whitespace and newlines (common issue when reading from files)
    return api_key.strip()


def _classify_activity_intensity(activity):
    """Classify a single activity row into Easy/Recovery, Moderate, or Hard using HR zone times.
    Returns 'Unknown' when HR data is absent. Used internally by analyze_pattern_flags."""
    z1 = activity.get('time_in_zone1') or 0
    z2 = activity.get('time_in_zone2') or 0
    z3 = activity.get('time_in_zone3') or 0
    z4 = activity.get('time_in_zone4') or 0
    z5 = activity.get('time_in_zone5') or 0
    total = z1 + z2 + z3 + z4 + z5
    if total == 0:
        return 'Unknown'
    p = [z / total * 100 for z in (z1, z2, z3, z4, z5)]
    if p[0] > 50 or p[1] > 50:
        return 'Easy/Recovery'
    if p[2] > 50 or (p[1] + p[2] > 70):
        return 'Moderate'
    if p[3] > 30 or p[4] > 20 or (p[3] + p[4] > 40):
        return 'Hard'
    primary = p.index(max(p))
    return 'Easy/Recovery' if primary <= 1 else ('Moderate' if primary == 2 else 'Hard')


def analyze_pattern_flags(activities, current_metrics, user_id=None, thresholds=None):
    """Analyze training patterns for red flags and positive adaptations with user-specific thresholds."""
    try:
        # Get user-specific thresholds if not provided
        if thresholds is None and user_id is not None:
            recommendation_style = get_user_recommendation_style(user_id)
            thresholds = get_adjusted_thresholds(recommendation_style)
        elif thresholds is None:
            # Default to balanced thresholds
            thresholds = get_adjusted_thresholds('balanced')
        
        flags = {
            'red_flags': [],
            'positive_patterns': [],
            'warnings': []
        }

        # Get recent ACWR and divergence trends
        recent_data = sorted(activities[-14:], key=lambda x: x['date'])  # Last 14 days

        if len(recent_data) < 7:
            return flags

        # Check for chronic ACWR elevation (using adjusted threshold)
        high_acwr_days = 0
        acwr_threshold = thresholds['acwr_high_risk']
        for activity in recent_data[-7:]:  # Last 7 days
            ext_acwr = activity.get('acute_chronic_ratio', 0)
            int_acwr = activity.get('trimp_acute_chronic_ratio', 0)
            if ext_acwr > acwr_threshold or int_acwr > acwr_threshold:
                high_acwr_days += 1

        if high_acwr_days >= 5:
            flags['red_flags'].append(f"Chronic ACWR elevation (>{acwr_threshold}) for 5+ consecutive days")

        # FIXED: Check for consecutive negative divergence days
        divergence_trend = []
        for activity in recent_data[-10:]:  # Look at last 10 days for trend analysis
            div = activity.get('normalized_divergence')
            if div is not None:
                divergence_trend.append(div)

        if len(divergence_trend) >= 5:
            # Count consecutive negative divergence days (from most recent backwards)
            consecutive_negative_days = 0
            for div in reversed(divergence_trend):  # Start from most recent
                if div < -0.05:  # Negative threshold
                    consecutive_negative_days += 1
                else:
                    break  # Stop at first non-negative day

            # Report actual consecutive days instead of hard-coded "5+"
            if consecutive_negative_days >= 5:
                if consecutive_negative_days >= 6:
                    flags['red_flags'].append(
                        f"DIVERGENCE DRIFT: The {consecutive_negative_days}+ day negative divergence trend is a red flag indicating disproportionate internal stress accumulation")
                else:
                    flags['warnings'].append(
                        f"Divergence trending negative for {consecutive_negative_days} consecutive days - monitor closely")

        # ENHANCED: Check for positive adaptation patterns with actual day count
        if len(divergence_trend) >= 5:
            consecutive_positive_days = 0
            for div in reversed(divergence_trend):  # Start from most recent
                if div > 0.05:  # Positive threshold
                    consecutive_positive_days += 1
                else:
                    break

            if consecutive_positive_days >= 3:
                flags['positive_patterns'].append(
                    f"Efficient adaptation - {consecutive_positive_days} consecutive days of positive divergence indicates excellent load tolerance")

        # #5 — Back-to-back hard session detection
        last_7 = sorted({a['date']: a for a in recent_data[-7:]}.values(), key=lambda x: x['date'])
        intensities = [(a['date'], _classify_activity_intensity(a)) for a in last_7]
        known = [(d, i) for d, i in intensities if i != 'Unknown']
        for idx in range(1, len(known)):
            if known[idx][1] == 'Hard' and known[idx - 1][1] == 'Hard':
                flags['warnings'].append(
                    f"Back-to-back hard sessions on {known[idx - 1][0]} and {known[idx][0]} — "
                    f"recovery may be insufficient; consider an easy day between hard efforts")
                break  # Report once per analysis window

        # #6 — Minimum easy day guardrail (≥2 easy/recovery days in last 7)
        easy_days = sum(1 for _, i in intensities if i == 'Easy/Recovery')
        if len(known) >= 5 and easy_days < 2:
            flags['red_flags'].append(
                f"Only {easy_days} easy/recovery day(s) in the last 7 days — "
                f"insufficient aerobic base recovery; trail runners need at least 2 easy days per week")

        # #11 — Activity gap detection (gaps >5 days in training record)
        all_dates = sorted(set(
            a['date'] if isinstance(a['date'], str) else a['date'].strftime('%Y-%m-%d')
            for a in activities if a.get('date')
        ))
        if len(all_dates) >= 2:
            from datetime import date as date_type, timedelta as td
            for i in range(1, len(all_dates)):
                d0 = date_type.fromisoformat(all_dates[i - 1])
                d1 = date_type.fromisoformat(all_dates[i])
                gap = (d1 - d0).days
                if gap > 5:
                    flags['warnings'].append(
                        f"Training gap: {gap} days without activity ({all_dates[i-1]} to {all_dates[i]}) — "
                        f"return-to-load caution applies; limit ACWR to 1.1 this week to avoid re-injury risk")
                    break  # Report the most recent qualifying gap only

        return flags

    except Exception as e:
        logger.error(f"Error analyzing pattern flags: {str(e)}")
        return {
            'red_flags': [],
            'positive_patterns': [],
            'warnings': []
        }


# DEPRECATED FUNCTION REMOVED: create_enhanced_prompt()
# This function was never called and has been superseded by create_enhanced_prompt_with_tone()
# Removed on 2025-11-19 as part of code cleanup and optimization
# All functionality is now handled by create_enhanced_prompt_with_tone() which includes
# coaching tone personalization and autopsy insights integration


def create_recent_activities_summary(activities):
    """Create a detailed summary of recent activities for context."""
    if not activities:
        return "No recent activities found."

    # Get the last 7 days with activities
    activities_by_date = {}
    for activity in activities:
        date = activity['date']
        if date not in activities_by_date:
            activities_by_date[date] = []
        activities_by_date[date].append(activity)

    recent_dates = sorted(activities_by_date.keys(), reverse=True)[:7]

    summary_lines = []
    for date in sorted(recent_dates, reverse=True):
        day_activities = activities_by_date[date]

        for activity in day_activities:
            activity_type = activity.get('type', 'Unknown')
            distance = activity.get('distance_miles', 0)
            elevation = activity.get('elevation_gain_feet', 0)
            trimp = activity.get('trimp', 0)
            acwr_ext = activity.get('acute_chronic_ratio', 0)
            acwr_int = activity.get('trimp_acute_chronic_ratio', 0)
            divergence = activity.get('normalized_divergence')

            if activity_type.lower() == 'rest' or activity.get('activity_id', 0) == 0:
                summary_lines.append(f"{date}: Rest day")
            else:
                div_str = f", Divergence: {divergence:.2f}" if divergence is not None and divergence != 0 else ""
                summary_lines.append(
                    f"{date}: {activity_type} - {distance:.1f}mi, {elevation:.0f}ft, "
                    f"TRIMP: {trimp:.0f}, ACWR: {acwr_ext:.2f}/{acwr_int:.2f}{div_str}"
                )

    return "\n".join(summary_lines)


def get_model_for_task(task):
    """Route to the appropriate Claude model based on task type."""
    task_routing = {
        'daily': MODEL_SONNET,
        'autopsy': MODEL_HAIKU,
        'weekly': MODEL_SONNET,
        'weekly_comprehensive': MODEL_OPUS,
    }
    return task_routing.get(task, MODEL_SONNET)


def extract_structured_output(response_text):
    """Extract and parse the structured JSON block from <structured_output> XML tags.

    Returns parsed dict or None if the block is absent or unparseable.
    """
    import re
    match = re.search(r'<structured_output>\s*(.*?)\s*</structured_output>', response_text, re.DOTALL)
    if not match:
        logger.info("No <structured_output> block found in LLM response")
        return None
    try:
        json_str = match.group(1).strip()
        parsed = json.loads(json_str)
        logger.info("✅ Successfully extracted structured output JSON")
        return parsed
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse structured output JSON: {e}")
        return None


def call_claude(prompt, model=None, temperature=None, max_tokens=2000, timeout=60, task='daily'):
    """Call Claude API using the Anthropic SDK.

    Drop-in replacement for call_anthropic_api() with identical return type (str).
    Uses get_model_for_task() routing when model is not explicitly specified.

    Args:
        prompt: The prompt text
        model: Claude model override (uses task routing if None)
        temperature: Sampling temperature (uses RECOMMENDATION_TEMPERATURE if None)
        max_tokens: Maximum tokens to generate
        timeout: Unused (SDK handles timeouts internally — kept for signature compat)
        task: Task type for model routing ('daily', 'autopsy', 'weekly', 'weekly_comprehensive')
    """
    if model is None:
        model = get_model_for_task(task)
    if temperature is None:
        temperature = RECOMMENDATION_TEMPERATURE

    try:
        import anthropic as anthropic_sdk
        api_key = get_api_key()
        client = anthropic_sdk.Anthropic(api_key=api_key)

        logger.info(f"Calling Claude (SDK) model={model}, max_tokens={max_tokens}, temperature={temperature}, task={task}")

        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        logger.info(
            f"SDK call successful: {message.usage.input_tokens} input, "
            f"{message.usage.output_tokens} output tokens"
        )
        return response_text

    except Exception as e:
        logger.error(f"Error calling Claude API (SDK): {str(e)}", exc_info=True)
        raise


def call_anthropic_api(prompt, model=DEFAULT_MODEL, temperature=RECOMMENDATION_TEMPERATURE, max_tokens=2000, timeout=30):
    """Legacy wrapper — delegates to call_claude(). Kept for backward compatibility.

    All new code should call call_claude() directly with the appropriate task parameter.

    Args:
        prompt: The prompt text
        model: Claude model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        timeout: API timeout in seconds (default 30, use 60-90 for complex generations)
    """
    return call_claude(prompt, model=model, temperature=temperature, max_tokens=max_tokens, timeout=timeout, task='daily')


def format_observations_for_prompt(observations):
    """Format user observations for the AI prompt"""
    if not observations:
        return "No observations recorded"

    formatted = []

    if observations.get('energy_level'):
        energy_labels = {1: "Barely got out of bed", 2: "Low energy", 3: "Normal", 4: "High energy", 5: "Fired up"}
        formatted.append(
            f"Energy Level: {observations['energy_level']}/5 ({energy_labels.get(observations['energy_level'], 'Unknown')}) - How athlete felt going into session")

    if observations.get('rpe_score'):
        formatted.append(f"RPE (Rate of Perceived Exertion): {observations['rpe_score']}/10 - How hard the workout felt")

    if observations.get('pain_percentage') is not None:
        formatted.append(f"Pain %: {observations['pain_percentage']}% - Percentage of time thinking about pain during activity")

    if observations.get('notes'):
        formatted.append(f"Notes: {observations['notes']}")

    return "\n".join(formatted) if formatted else "No specific observations recorded"


def create_autopsy_prompt(date_str, prescribed_action, actual_activities, observations_text, current_metrics,
                          training_guide):
    """Create the specialized prompt for autopsy analysis"""

    prompt = f"""You are an expert endurance sports coach conducting a post-training analysis (autopsy) using established training science principles.

### TRAINING AUTOPSY ANALYSIS
**Date:** {date_str}
**Athlete Metrics Context:**
- External ACWR: {current_metrics.get('external_acwr') or 0:.2f}
- Internal ACWR: {current_metrics.get('internal_acwr') or 0:.2f}
- Normalized Divergence: {format_divergence_for_prompt(current_metrics.get('normalized_divergence'))}
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}

### PRESCRIBED VS ACTUAL COMPARISON

**PRESCRIBED ACTION:**
{prescribed_action}

**ACTUAL ACTIVITY:**
{actual_activities}

**ATHLETE OBSERVATIONS:**
{observations_text}

### TRAINING REFERENCE FRAMEWORK
{training_guide}

### AUTOPSY ANALYSIS INSTRUCTIONS

Using the Training Reference Framework above, provide a structured analysis in exactly three sections:

**ALIGNMENT ASSESSMENT:**
- Compare prescribed vs actual activities
- Evaluate whether the deviation (if any) was appropriate given the circumstances
- Reference specific Decision Framework criteria from the training guide
- Rate alignment on 1-10 scale with justification

**PHYSIOLOGICAL RESPONSE ANALYSIS:**
- Analyze the athlete's energy, RPE, and pain levels in context of the activity
- Compare expected vs actual response based on current metrics
- Identify signs of positive adaptation, fatigue, or overtraining risk
- Reference optimal ranges and pattern recognition from the guide

**LEARNING INSIGHTS & TOMORROW'S IMPLICATIONS:**
- What does this response teach us about the athlete's current adaptation state?
- How should this information influence tomorrow's training decision?
- Specific recommendations for ACWR management and recovery planning
- Flag any concerning patterns that require monitoring

Keep each section focused and evidence-based. Reference specific numbers from the metrics and use the established classification terms from the training guide. Limit response to 200-300 words total for practical journal display."""

    return prompt


def create_fallback_autopsy(prescribed_action, actual_activities, observations):
    """Create a structured fallback autopsy if AI generation fails"""

    # Improved logic: Check for actual rest prescription, not just the word "rest" appearing in context
    prescribed_lower = prescribed_action.lower()
    actual_lower = str(actual_activities).lower()
    
    # Look for explicit rest prescriptions (not just mentions of "rest" in context)
    rest_prescribed = (
        "rest day" in prescribed_lower or
        "take a rest" in prescribed_lower or
        "rest today" in prescribed_lower or
        "rest and recovery" in prescribed_lower or
        prescribed_lower.startswith("rest") or
        "prescribed: rest" in prescribed_lower
    ) and not (
        "days since rest" in prescribed_lower or
        "rest period" in prescribed_lower or
        "rest interval" in prescribed_lower
    )
    
    # Determine basic alignment with improved logic
    if rest_prescribed and ("rest" in actual_lower or "no activity" in actual_lower):
        alignment = "Good - Rest day followed as prescribed"
    elif rest_prescribed and "rest" not in actual_lower:
        alignment = "Poor - Rest was prescribed but activity was performed"
    elif "reduce" in prescribed_lower or "easy" in prescribed_lower or "recovery" in prescribed_lower:
        alignment = "Partial - Intensity guidance may not have been fully followed"
    else:
        alignment = "Unable to assess - AI analysis recommended"

    # Basic response analysis
    response_notes = []
    if observations.get('energy_level'):
        if observations['energy_level'] <= 2:
            response_notes.append("Low energy reported - may indicate fatigue")
        elif observations['energy_level'] >= 4:
            response_notes.append("Good energy levels - positive adaptation sign")

    if observations.get('rpe_score'):
        if observations['rpe_score'] >= 8:
            response_notes.append("High RPE suggests significant effort")
        elif observations['rpe_score'] <= 4:
            response_notes.append("Low RPE indicates easy session")

    if observations.get('pain_percentage', 0) > 0:
        response_notes.append(f"Pain reported ({observations['pain_percentage']}%) - monitor closely")

    fallback = f"""**ALIGNMENT ASSESSMENT:**
{alignment}

**PHYSIOLOGICAL RESPONSE:**
{'; '.join(response_notes) if response_notes else 'Insufficient data for analysis'}

**LEARNING INSIGHTS:**
Basic autopsy generated - full AI analysis recommended for detailed insights.

Prescribed: {prescribed_action[:100]}...
Actual: {actual_activities[:100]}..."""

    return fallback


def generate_recommendations(force=False, user_id=None, target_tomorrow=False, target_date=None):
    """Generate enhanced training recommendations using the training guide with fresh metrics.
    
    Args:
        force: Force generation even if recommendation is recent
        user_id: User ID for multi-user support
        target_tomorrow: Force target date to be tomorrow (for rest days)
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Check if we need to generate a new recommendation
        if not force and not recommendation_needs_update(user_id):
            logger.info(f"No new recommendation needed for user {user_id}")
            return get_latest_recommendation(user_id)

        logger.info(f"Generating new enhanced training recommendations for user {user_id}")

        # CRITICAL FIX: Get current date using USER'S TIMEZONE (not UTC)
        # This ensures Thursday night Pacific generates Thursday/Friday recommendations correctly
        from timezone_utils import get_user_current_date
        current_date = get_user_current_date(user_id)
        current_date_str = current_date.strftime('%Y-%m-%d')
        logger.info(f"Using user current date: {current_date_str}")

        # CRITICAL FIX: Force metrics recalculation before generating recommendations
        # This ensures we use post-workout ACWR values, not pre-workout values
        logger.info("Forcing metrics recalculation to include latest activity data...")

        # Trigger fresh ACWR calculation for the most recent activities
        from strava_training_load import update_moving_averages

        # Update averages for the last few days to ensure fresh calculations
        for days_back in range(3):  # Update last 3 days to be safe
            calc_date = current_date - timedelta(days=days_back)
            date_str = calc_date.strftime('%Y-%m-%d')
            update_moving_averages(date_str, user_id)
            logger.info(f"Updated moving averages for {date_str}")

        # Load the training guide
        training_guide = load_training_guide()
        if not training_guide:
            logger.error("Training guide not available - falling back to basic recommendations")
            return None

        # Determine target_date for this recommendation
        if target_date:
            # Explicit date provided (e.g., Refresh Rec button) — use it directly
            logger.info(f"Using explicitly provided target_date: {target_date}")
        else:
            # Auto-determine: today unless activity+journal complete → tomorrow
            has_activity_today = check_activity_for_date(user_id, current_date_str)
            if target_tomorrow:
                target_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"REST DAY: Explicitly targeting tomorrow: {target_date}")
            elif has_activity_today and check_journal_for_date(user_id, current_date_str):
                target_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"User {user_id} has activity + journal for {current_date_str}, targeting tomorrow: {target_date}")
            else:
                target_date = current_date_str
                logger.info(f"User {user_id} targeting today: {target_date}")

        # Check if recommendation already exists for this target_date.
        # Skip generation to preserve historical record UNLESS this is an explicit
        # force-regeneration (force=True with a specific target_date from Refresh Rec).
        existing_recommendation = execute_query(
            "SELECT id FROM llm_recommendations WHERE user_id = %s AND target_date = %s",
            (user_id, target_date),
            fetch=True
        )

        if existing_recommendation and not (force and target_date):
            logger.info(f"Recommendation already exists for target_date {target_date}, skipping to preserve historical record")
            result = execute_query(
                "SELECT * FROM llm_recommendations WHERE user_id = %s AND target_date = %s ORDER BY generated_at DESC LIMIT 1",
                (user_id, target_date),
                fetch=True
            )
            return dict(result[0]) if result and result[0] else get_latest_recommendation(user_id)
        elif existing_recommendation and force and target_date:
            logger.info(f"Force-regenerating recommendation for target_date {target_date} (Refresh Rec)")

        # For historical record keeping - no expiration for date-specific recommendations
        valid_until = None

        # Get the data needed for the recommendation
        activities = get_recent_activities(days=ACTIVITY_ANALYSIS_DAYS, user_id=user_id)
        if not activities:
            logger.warning(f"No activities found for user {user_id} for generating recommendations")
            return None

        # Get start and end dates from activities
        start_date = activities[0]['date']
        end_date = activities[-1]['date']

        # CRITICAL FIX: Get FRESH metrics after forced recalculation
        current_metrics = get_current_metrics(user_id)
        if not current_metrics:
            logger.warning(f"Failed to get current metrics for user {user_id}")
            return None

        # Log the metrics being used to verify they're fresh
        logger.info(f"Using metrics for recommendation generation:")
        logger.info(f"  External ACWR: {current_metrics.get('external_acwr')}")
        logger.info(f"  Internal ACWR: {current_metrics.get('internal_acwr')}")
        logger.info(f"  Normalized Divergence: {current_metrics.get('normalized_divergence')}")
        logger.info(f"  Latest activity date: {current_metrics.get('latest_activity_date')}")

        pattern_analysis = analyze_training_patterns(activities)
        # spectrum_value = get_user_coaching_spectrum(user_id)
        # tone_instructions = get_coaching_tone_instructions(spectrum_value)

        user_prefs = get_user_preferences(user_id)
        spectrum_value = user_prefs['spectrum_value']
        recommendation_style = user_prefs['recommendation_style']
        logger.info(f"TONE DEBUG: User {user_id} spectrum={spectrum_value}, style={recommendation_style}")

        tone_instructions = get_coaching_tone_instructions(spectrum_value)
        logger.info(f"TONE DEBUG: Instructions preview: {tone_instructions[:100]}...")

        # CRITICAL FIX: Get autopsy insights BEFORE creating prompt so they can be incorporated
        autopsy_insights = get_recent_autopsy_insights(user_id, days=3)
        is_autopsy_informed = bool(autopsy_insights and autopsy_insights.get('count', 0) > 0)

        if is_autopsy_informed:
            logger.info(f"Generating autopsy-informed recommendation with {autopsy_insights['count']} recent autopsies, avg alignment: {autopsy_insights['avg_alignment']}")
        else:
            logger.info("Generating standard recommendation without recent autopsy data")

        prompt = create_enhanced_prompt_with_tone(
            current_metrics, activities, pattern_analysis, training_guide,
            user_id, tone_instructions, autopsy_insights, target_date=target_date,
            recommendation_style=recommendation_style
        )

        # Call the API — use Sonnet for daily recommendations (Phase 2 routing)
        llm_response = call_claude(prompt, task='daily')

        # Parse the response
        sections = parse_llm_response(llm_response)
        
        if is_autopsy_informed:
            logger.info(f"Recommendation is autopsy-informed with {autopsy_insights['count']} recent autopsies, avg alignment: {autopsy_insights['avg_alignment']}")
        else:
            logger.info("Recommendation generated without recent autopsy data")

        # FIXED: Create recommendation object with proper target_date
        recommendation = {
            'generation_date': current_date_str,  # When created (today)
            'target_date': target_date,  # What date it's FOR (today or tomorrow)
            'valid_until': valid_until,  # NULL for permanent records
            'data_start_date': start_date,
            'data_end_date': end_date,
            'metrics_snapshot': current_metrics,
            'daily_recommendation': sections['daily_recommendation'],
            'weekly_recommendation': sections['weekly_recommendation'],
            'pattern_insights': sections['pattern_insights'],
            'raw_response': llm_response,
            'user_id': user_id,
            # NEW: Autopsy tracking fields
            'is_autopsy_informed': is_autopsy_informed,
            'autopsy_count': autopsy_insights['count'] if autopsy_insights else 0,
            'avg_alignment_score': autopsy_insights['avg_alignment'] if autopsy_insights else None,
            # Phase 1: Structured output (None if model didn't emit the block)
            'structured_output': sections.get('structured_output')
        }

        # Save to database
        recommendation = fix_dates_for_json(recommendation)
        recommendation_id = save_llm_recommendation(recommendation)
        logger.info(
            f"Saved enhanced recommendation with ID {recommendation_id} for user {user_id} with target_date {target_date}")

        # Clean up old recommendations (keep last 14 days)
        from db_utils import cleanup_old_recommendations
        cleanup_old_recommendations(user_id, keep_days=14)

        # Add the ID to the recommendation
        recommendation['id'] = recommendation_id

        return recommendation

    except Exception as e:
        logger.error(f"Error generating enhanced recommendations for user {user_id}: {str(e)}")
        return None

def create_enhanced_prompt_with_tone(current_metrics, activities, pattern_analysis, training_guide, user_id, tone_instructions, autopsy_insights=None, target_date=None, recommendation_style=None):
    """Create an enhanced prompt using the training guide framework with coaching tone and optional autopsy learning."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    # Get athlete experience level and age from user profile
    athlete_experience = execute_query(
        "SELECT training_experience, age FROM user_settings WHERE id = %s",
        (user_id,),
        fetch=True
    )
    athlete_profile = athlete_experience[0]['training_experience'].capitalize() if (athlete_experience and athlete_experience[0].get('training_experience')) else "Intermediate"
    athlete_age = athlete_experience[0]['age'] if (athlete_experience and athlete_experience[0].get('age')) else None

    # Use pre-fetched recommendation_style if provided, otherwise query (fallback for other callers)
    if recommendation_style is None:
        recommendation_style = get_user_recommendation_style(user_id)
    thresholds = get_adjusted_thresholds(recommendation_style)
    thresholds = apply_athlete_model_to_thresholds(thresholds, user_id)

    pattern_flags = analyze_pattern_flags(activities, current_metrics, user_id, thresholds)

    # Get date information using USER'S TIMEZONE
    from timezone_utils import get_user_current_date
    current_date = get_user_current_date(user_id).strftime(DEFAULT_DATE_FORMAT)
    start_date = activities[0]['date'] if activities else "unknown"
    end_date = activities[-1]['date'] if activities else "unknown"
    days_analyzed = len(set(activity['date'] for activity in activities))

    # Create recent activities summary
    recent_activities_summary = create_recent_activities_summary(activities)

    # Format the metrics - ensure we're using the unified values
    formatted_metrics = {
        'external_acwr': f"{current_metrics['external_acwr']:.2f}" if current_metrics['external_acwr'] else "N/A",
        'internal_acwr': f"{current_metrics['internal_acwr']:.2f}" if current_metrics['internal_acwr'] else "N/A",
        'normalized_divergence': f"{current_metrics['normalized_divergence']:.3f}" if current_metrics[
                                                                                          'normalized_divergence'] is not None else "N/A",
        'seven_day_avg_load': f"{current_metrics['seven_day_avg_load']:.2f}" if current_metrics[
            'seven_day_avg_load'] else "N/A",
        'seven_day_avg_trimp': f"{current_metrics['seven_day_avg_trimp']:.1f}" if current_metrics[
            'seven_day_avg_trimp'] else "N/A",
        'days_since_rest': str(current_metrics['days_since_rest'])
    }

    # Log what we're sending to the prompt for debugging
    logger.info(f"Prompt will use these metrics for user {user_id}:")
    logger.info(f"  External ACWR: {formatted_metrics['external_acwr']}")
    logger.info(f"  Internal ACWR: {formatted_metrics['internal_acwr']}")
    logger.info(f"  Divergence: {formatted_metrics['normalized_divergence']}")
    logger.info(f"  Days since rest: {formatted_metrics['days_since_rest']}")
    logger.info(f"  Risk tolerance: {recommendation_style} (ACWR threshold: {thresholds['acwr_high_risk']})")

    # Determine primary assessment category based on metrics (using adjusted thresholds)
    days_since_rest = current_metrics.get('days_since_rest', 0)
    external_acwr = current_metrics.get('external_acwr', 0)
    internal_acwr = current_metrics.get('internal_acwr', 0)
    normalized_divergence = current_metrics.get('normalized_divergence', 0)

    assessment_category = "normal_progression"
    if days_since_rest > thresholds['days_since_rest_max']:
        assessment_category = "mandatory_rest"
    elif normalized_divergence < thresholds['divergence_overtraining']:
        assessment_category = "overtraining_risk"
    elif external_acwr > thresholds['acwr_high_risk'] and internal_acwr > thresholds['acwr_high_risk']:
        assessment_category = "high_acwr_risk"
    elif normalized_divergence < thresholds['divergence_moderate_risk'] and days_since_rest > 5:
        assessment_category = "recovery_needed"
    elif external_acwr < thresholds['acwr_undertraining'] and internal_acwr < thresholds['acwr_undertraining']:
        assessment_category = "undertraining_opportunity"

    # Filter the training guide to sections relevant to this assessment category
    filtered_guide = _select_guide_sections(training_guide, assessment_category) if training_guide else training_guide

    # Fetch athlete model once; reused by both the prompt context block and readiness state.
    _cached_athlete_model = get_athlete_model(user_id)

    # Build athlete model context for prompt injection (Phase 3)
    # Only injected when confidence > 0.15 (get_athlete_model_context handles threshold)
    athlete_model_context = get_athlete_model_context(user_id, athlete_model=_cached_athlete_model)

    # Get morning readiness for current date (Phase 6B)
    readiness_data = execute_query(
        """SELECT sleep_quality, morning_soreness, hrv_value, resting_hr,
                  sleep_duration_secs, sleep_score, weight, spo2, respiration_rate
           FROM journal_entries WHERE user_id = %s AND date = %s""",
        (user_id, current_date),
        fetch=True
    )

    # HRV 30-day baseline (require ≥7 readings)
    hrv_baseline_data = execute_query(
        """SELECT AVG(hrv_value) AS hrv_baseline, COUNT(hrv_value) AS hrv_count
           FROM journal_entries
           WHERE user_id = %s
             AND date >= %s::date - INTERVAL '30 days'
             AND date < %s::date
             AND hrv_value IS NOT NULL""",
        (user_id, current_date, current_date),
        fetch=True
    )

    # RHR 7-day baseline (require ≥3 readings)
    rhr_baseline_data = execute_query(
        """SELECT AVG(resting_hr) AS rhr_baseline, COUNT(resting_hr) AS rhr_count
           FROM journal_entries
           WHERE user_id = %s
             AND date >= %s::date - INTERVAL '7 days'
             AND date < %s::date
             AND resting_hr IS NOT NULL""",
        (user_id, current_date, current_date),
        fetch=True
    )

    readiness_context = ""
    if readiness_data and readiness_data[0]:
        row = dict(readiness_data[0])
        sq               = row.get('sleep_quality')
        ms               = row.get('morning_soreness')
        hrv_value        = row.get('hrv_value')
        rhr_value        = row.get('resting_hr')
        sleep_secs       = row.get('sleep_duration_secs')
        sleep_score      = row.get('sleep_score')
        weight           = row.get('weight')
        spo2             = row.get('spo2')
        respiration_rate = row.get('respiration_rate')

        parts = []

        # Sleep — prefer objective duration over subjective quality when available
        if sleep_secs is not None:
            hours = float(sleep_secs) / 3600
            if hours < 6:
                sleep_status = "significant deficit"
            elif hours < 7:
                sleep_status = "suboptimal"
            else:
                sleep_status = "adequate"
            score_str = f", score: {sleep_score}/100" if sleep_score is not None else ""
            parts.append(f"Sleep: {hours:.1f}hrs ({sleep_status}{score_str})")
        elif sq is not None:
            sleep_labels = {1: "very poor", 2: "poor", 3: "fair", 4: "good", 5: "excellent"}
            parts.append(f"Sleep quality: {sq}/5 ({sleep_labels.get(sq, 'unknown')})")

        if ms is not None:
            parts.append(f"Morning soreness: {ms}/100")

        # HRV context
        if hrv_value is not None:
            hrv_baseline = hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data and hrv_baseline_data[0] else None
            hrv_count    = hrv_baseline_data[0]['hrv_count']    if hrv_baseline_data and hrv_baseline_data[0] else 0
            if hrv_baseline and hrv_count >= 7:
                ratio     = float(hrv_value) / float(hrv_baseline)
                pct_diff  = (ratio - 1.0) * 100
                direction = "suppressed" if ratio < 0.85 else ("elevated" if ratio > 1.15 else "normal range")
                parts.append(
                    f"HRV: {hrv_value:.0f}ms "
                    f"(30-day baseline: {hrv_baseline:.0f}ms, "
                    f"{abs(pct_diff):.0f}% {'below' if pct_diff < 0 else 'above'} baseline — {direction})"
                )
            else:
                readings_needed = max(0, 7 - (hrv_count or 0))
                parts.append(f"HRV: {hrv_value:.0f}ms (building baseline — {readings_needed} more readings needed)")

        # Resting HR context
        if rhr_value is not None:
            rhr_baseline = rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data and rhr_baseline_data[0] else None
            rhr_count    = rhr_baseline_data[0]['rhr_count']    if rhr_baseline_data and rhr_baseline_data[0] else 0
            if rhr_baseline and rhr_count >= 3:
                rhr_diff = rhr_value - float(rhr_baseline)
                pct_diff = (rhr_diff / float(rhr_baseline)) * 100
                if pct_diff >= 10:
                    status = "significantly elevated"
                elif pct_diff >= 5:
                    status = "elevated"
                elif pct_diff <= -5:
                    status = "below baseline"
                else:
                    status = "normal range"
                parts.append(
                    f"Resting HR: {rhr_value}bpm "
                    f"(7-day baseline: {rhr_baseline:.0f}bpm, "
                    f"{abs(pct_diff):.0f}% {'above' if rhr_diff > 0 else 'below'} baseline — {status})"
                )
            else:
                parts.append(f"Resting HR: {rhr_value}bpm (building baseline)")

        # Weight — inject only when we have enough history to show context
        if weight is not None:
            weight_baseline_data = execute_query(
                """SELECT AVG(weight) AS weight_avg
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= %s::date - INTERVAL '7 days'
                     AND date < %s::date
                     AND weight IS NOT NULL""",
                (user_id, current_date, current_date),
                fetch=True
            )
            weight_avg = weight_baseline_data[0]['weight_avg'] if weight_baseline_data and weight_baseline_data[0] else None
            if weight_avg:
                delta = float(weight) - float(weight_avg)
                pct   = (delta / float(weight_avg)) * 100
                if pct <= -2:
                    note = " — possible dehydration, monitor"
                elif pct >= 2:
                    note = " — above 7-day avg"
                else:
                    note = ""
                parts.append(f"Weight: {weight:.1f}kg (7-day avg: {float(weight_avg):.1f}kg, {delta:+.1f}kg{note})")
            else:
                parts.append(f"Weight: {weight:.1f}kg")

        # spO2 — only inject when below 95%
        if spo2 is not None and float(spo2) < 95:
            parts.append(f"SpO2: {spo2:.0f}% — low, possible altitude effect or illness")

        # Respiration — only inject when elevated vs 7-day baseline
        if respiration_rate is not None:
            resp_baseline_data = execute_query(
                """SELECT AVG(respiration_rate) AS resp_avg
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= %s::date - INTERVAL '7 days'
                     AND date < %s::date
                     AND respiration_rate IS NOT NULL""",
                (user_id, current_date, current_date),
                fetch=True
            )
            resp_avg = resp_baseline_data[0]['resp_avg'] if resp_baseline_data and resp_baseline_data[0] else None
            if resp_avg and float(respiration_rate) > float(resp_avg) * 1.15:
                parts.append(
                    f"Respiration: {respiration_rate:.0f} breaths/min "
                    f"(7-day avg: {float(resp_avg):.0f} — elevated, possible illness or stress)"
                )

        if parts:
            readiness_context = "\n### MORNING READINESS\n" + "\n".join(f"- {p}" for p in parts) + "\n"

        # Readiness state synthesis (always compute when readiness row exists)
        _rs = compute_readiness_state(
            readiness_row=row,
            hrv_baseline=hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data and hrv_baseline_data[0] else None,
            hrv_baseline_count=hrv_baseline_data[0]['hrv_count'] if hrv_baseline_data and hrv_baseline_data[0] else 0,
            rhr_baseline=rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data and rhr_baseline_data[0] else None,
            rhr_baseline_count=rhr_baseline_data[0]['rhr_count'] if rhr_baseline_data and rhr_baseline_data[0] else 0,
            athlete_model=_cached_athlete_model,
        )
        if readiness_context:
            readiness_context += f"**READINESS STATE: {_rs['state']}** — {_rs['narrative']}\n"
        else:
            readiness_context = f"\n### MORNING READINESS\n**READINESS STATE: {_rs['state']}** — {_rs['narrative']}\n"

    # Build autopsy context section if insights available
    autopsy_context = ""
    if autopsy_insights and autopsy_insights.get('count', 0) > 0:
        alignment_trend = autopsy_insights.get('alignment_trend', [])
        trend_description = "improving" if len(alignment_trend) >= 2 and alignment_trend[-1] > alignment_trend[0] else "mixed"
        
        reason_breakdown = autopsy_insights.get('reason_breakdown', {})
        reason_parts = [f"{v} {k}" for k, v in reason_breakdown.items() if v > 0]
        reason_str = ", ".join(reason_parts) if reason_parts else "none classified"

        autopsy_context = f"""
### RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses)
- Average Alignment Score: {autopsy_insights['avg_alignment']:.1f}/10
- Alignment Trend: {trend_description} ({alignment_trend})
- Deviation Causes: {reason_str}
- Latest Insights: {autopsy_insights.get('latest_insights', 'No specific insights')[:200]}

**COACHING ADAPTATION STRATEGY:**
- If alignment >7: Athlete follows guidance well - build on successful patterns
- If alignment 4-7: Address recurring deviations - simplify recommendations
- If alignment <4: Major strategy adjustment needed - focus on compliance over optimization

**IMPORTANT:** Use this autopsy learning to adapt today's recommendation. If recent alignment is low, recommend more conservative/achievable targets. If alignment is high, maintain current approach.
"""
    else:
        autopsy_context = ""

    # Build weekly context block (Phase B: Macro→Meso→Micro injection)
    weekly_context_block = ""
    try:
        week_ctx = get_current_week_context(user_id)
        summary = week_ctx.get('strategic_summary') if week_ctx else None
        if summary:
            # Determine day of week from target_date (falls back to current_date)
            ref_date_str = target_date if target_date else current_date
            try:
                ref_date_obj = datetime.strptime(ref_date_str, DEFAULT_DATE_FORMAT)
                day_of_week = ref_date_obj.strftime("%A")
            except (ValueError, TypeError):
                day_of_week = "Today"

            week_start = week_ctx.get('week_start_date', '')
            if hasattr(week_start, 'strftime'):
                week_start = week_start.strftime(DEFAULT_DATE_FORMAT)

            training_stage = summary.get('training_stage', 'unknown')
            intensity_target = summary.get('weekly_intensity_target', 'unknown')
            load_low = summary.get('load_target_low', 'N/A')
            load_high = summary.get('load_target_high', 'N/A')
            strategic_notes = summary.get('strategic_notes', '')
            key_sessions = summary.get('key_sessions', [])

            # Format key sessions list
            if key_sessions:
                key_sessions_str = ", ".join(
                    f"{s.get('day', '?')} — {s.get('type', '?')}" for s in key_sessions
                )
            else:
                key_sessions_str = "none specified"

            # Build full daily program summary from program_json
            program_json = week_ctx.get('program_json') or {}
            if isinstance(program_json, str):
                try:
                    program_json = json.loads(program_json)
                except Exception:
                    program_json = {}

            daily_program = program_json.get('daily_program', [])

            # Find today's prescription from the daily program (more detailed than key_sessions)
            today_full = next(
                (d for d in daily_program if d.get('day', '').lower() == day_of_week.lower()),
                None
            )

            # Fall back to key_sessions if daily_program missing today
            if today_full:
                workout_type = today_full.get('workout_type', 'session')
                description = today_full.get('description', '')
                dist = today_full.get('distance_miles')
                elev = today_full.get('elevation_gain_feet')
                intensity = today_full.get('intensity', '')
                key_focus = today_full.get('key_focus', '')
                parts = [workout_type]
                if description:
                    parts.append(description)
                if dist:
                    parts.append(f"{dist:.1f} mi")
                if elev:
                    parts.append(f"+{int(elev)} ft")
                if intensity:
                    parts.append(f"intensity: {intensity}")
                todays_prescribed = " — ".join(parts)
                if key_focus:
                    todays_prescribed += f" | Focus: {key_focus}"
            else:
                today_session = next(
                    (s for s in key_sessions if s.get('day', '').lower() == day_of_week.lower()),
                    None
                )
                if today_session:
                    todays_prescribed = today_session.get('type', 'session')
                    if today_session.get('notes'):
                        todays_prescribed += f" ({today_session['notes']})"
                else:
                    todays_prescribed = "filler/recovery day"

            # Build the full week schedule string
            if daily_program:
                week_schedule_lines = []
                for d in daily_program:
                    day_name = d.get('day', '?')
                    wtype = d.get('workout_type', 'Unknown')
                    d_mi = d.get('distance_miles')
                    d_elev = d.get('elevation_gain_feet')
                    d_int = d.get('intensity', '')
                    marker = " ← TODAY" if day_name.lower() == day_of_week.lower() else ""
                    dist_str = f"{d_mi:.1f} mi" if d_mi else ""
                    elev_str = f"+{int(d_elev)} ft" if d_elev else ""
                    detail = ", ".join(filter(None, [dist_str, elev_str, d_int]))
                    week_schedule_lines.append(f"  {day_name}: {wtype} ({detail}){marker}")
                week_schedule_str = "\n".join(week_schedule_lines)
            else:
                week_schedule_str = f"  Key sessions: {key_sessions_str}"

            weekly_context_block = f"""
### WEEKLY PROGRAM (week of {week_start})
Training stage: {training_stage} | Intensity target: {intensity_target} | Target load: {load_low}–{load_high} ACWR
Strategic notes: {strategic_notes}

Full week schedule:
{week_schedule_str}

**Today ({day_of_week}) prescribed: {todays_prescribed}**

EQUAL WEIGHT RULE: The weekly program prescription and autopsy/readiness data carry equal weight.
- If metrics SUPPORT the prescription: confirm it and execute.
- If metrics CONFLICT with the prescription: you may deviate, but you MUST explicitly state in your DAILY RECOMMENDATION: (1) what the weekly plan prescribes, (2) what you are recommending instead, (3) the specific metric or autopsy finding that justifies the deviation.
Safety constraints (ACWR thresholds, injury flags) still take precedence over both.
"""
            # Append deviation log / revision pending summary when present
            deviation_log = week_ctx.get('deviation_log') or []
            revision_pending = week_ctx.get('revision_pending') or False
            if deviation_log or revision_pending:
                weekly_context_block += f"This week's deviation count: {len(deviation_log)}"
                if revision_pending:
                    weekly_context_block += " | Plan revision pending — a mid-week adjustment has been proposed."
                weekly_context_block += "\n"
        else:
            weekly_context_block = """
### WEEKLY CONTEXT
[No weekly plan active — recommendation generated independently]
"""
    except Exception as e:
        logger.warning(f"Phase B: weekly context injection failed for user {user_id}: {e}. Falling back to race goals.")
        try:
            from coach_recommendations import get_race_goals, format_race_goals_for_prompt
            fallback_goals = get_race_goals(user_id)
            goals_str = format_race_goals_for_prompt(fallback_goals)
            weekly_context_block = f"\n### WEEKLY CONTEXT\n[Weekly plan unavailable — using race goals directly]\n{goals_str}\n"
        except Exception:
            weekly_context_block = "\n### WEEKLY CONTEXT\n[Weekly context unavailable — recommendation generated from current metrics only]\n"

    # Build the enhanced prompt with tone integration and risk tolerance context
    prompt = f"""You are an expert endurance sports coach specializing in data-driven training recommendations.

{tone_instructions}

ATHLETE RISK TOLERANCE: {recommendation_style.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days
- Divergence Overtraining Risk: <{thresholds['divergence_overtraining']}

### ATHLETE PROFILE
Experience Level: {athlete_profile}
Age: {f"{athlete_age} years old" if athlete_age else "Not specified"}
Analysis Period: {start_date} to {end_date} ({days_analyzed} days)
Assessment Category: {assessment_category}

### CURRENT METRICS (as of {current_date})
- External ACWR: {formatted_metrics['external_acwr']} (Optimal: 0.8-1.3)
- Internal ACWR: {formatted_metrics['internal_acwr']} (Optimal: 0.8-1.3)
- Normalized Divergence: {format_divergence_for_prompt(current_metrics.get('normalized_divergence'))}
- 7-day Average Load: {formatted_metrics['seven_day_avg_load']} miles/day
- 7-day Average TRIMP: {formatted_metrics['seven_day_avg_trimp']}/day
- Days Since Rest: {formatted_metrics['days_since_rest']}
{athlete_model_context}
{readiness_context}
{autopsy_context}
{weekly_context_block}
### PATTERN ANALYSIS
Training Trends:
- Weekly volume: {pattern_analysis['weekly_volume_trend']}
- Intensity distribution: {pattern_analysis['intensity_distribution']}
- Workout types: {pattern_analysis['workout_type_frequency']}
- Elevation pattern: {pattern_analysis['elevation_pattern']}

Red Flags: {', '.join(pattern_flags['red_flags']) if pattern_flags['red_flags'] else 'None detected'}
Positive Patterns: {', '.join(pattern_flags['positive_patterns']) if pattern_flags['positive_patterns'] else 'None identified'}
Warnings: {', '.join(pattern_flags['warnings']) if pattern_flags['warnings'] else 'None'}

### RECENT ACTIVITY SUMMARY
{recent_activities_summary}

### TRAINING REFERENCE FRAMEWORK
{filtered_guide}

### RESPONSE INSTRUCTIONS

Using the Training Reference Framework above and applying the specified coaching tone throughout, provide specific, evidence-based recommendations in exactly three sections:

**DAILY RECOMMENDATION:**
- Apply the Decision Framework assessment order (Safety → Overtraining → ACWR → Recovery → Progression)
- Use the athlete's risk tolerance thresholds listed above (NOT the standard guide thresholds)
- Use the specified coaching tone throughout your guidance
- Reference the athlete's specific ACWR threshold ({thresholds['acwr_high_risk']}) and divergence limits
- Include specific volume/intensity targets based on current 7-day averages
- Use the scenario examples as formatting templates

**WEEKLY PLANNING:**
- Apply weekly planning priorities from the guide with your coaching style
- Adjust recommendations to match the athlete's {recommendation_style} risk tolerance
- Address any red flags or leverage positive patterns identified
- Include specific ACWR management strategies based on athlete's thresholds
- Tailor complexity and terminology to athlete's experience level

**PATTERN INSIGHTS:**
- Identify 2-3 specific observations using the pattern recognition framework
- Apply your coaching tone to the delivery of insights
- Interpret metrics relative to this athlete's personalized thresholds
- Include forward-looking trend analysis based on recent patterns

WEEKLY PLAN RULE: The weekly program prescription and the autopsy/readiness data carry EQUAL WEIGHT. Begin your DAILY RECOMMENDATION by stating what the weekly plan prescribes for today. Then either:
- CONFIRM: "The weekly plan calls for [X]. Your metrics support this — [reason]." Then give execution details.
- DEVIATE: "The weekly plan calls for [X]. Based on [specific metric/autopsy finding], I'm recommending [Y] instead." Then explain the deviation clearly.
Never silently ignore the weekly plan. Every recommendation must acknowledge it.

CRITICAL REQUIREMENTS:
- Use the ATHLETE'S PERSONALIZED THRESHOLDS, not the standard guide thresholds
- Apply the specified coaching tone consistently throughout all sections
- Keep each section focused and actionable
- Reference specific numbers from the metrics and use established classification terms (e.g., "Optimal Zone," "High Risk," "Efficient") from the training guide
- Maintain evidence-based analysis while adapting communication style and risk tolerance
- Do NOT add sub-headers like "**TRAINING DECISION: [date]**" or "**ASSESSMENT:**" within your sections. The three section headers (DAILY RECOMMENDATION, WEEKLY PLANNING, PATTERN INSIGHTS) are the only structural elements. Write each section in prose paragraphs.

### STRUCTURED OUTPUT (Phase 1)
After your three prose sections, append a machine-readable JSON block inside XML tags.

DIVERGENCE-FIRST RULE: Evaluate the divergence between External ACWR and Internal ACWR BEFORE assessing raw ACWR values. Divergence is the primary YTM signal. {NORMALIZED_DIVERGENCE_FORMULA}

Set assessment.primary_signal to "divergence" unless another signal clearly dominates.

Fill in ALL fields with actual computed values. Use only the allowed enum values for string fields. Set meta.tokens_used to {{"input": 0, "output": 0}} (post-processed).

<structured_output>
{{
  "target_date": "{target_date or 'YYYY-MM-DD'}",
  "assessment": {{
    "primary_signal": "divergence",
    "category": "normal_progression",
    "confidence": 0.85,
    "primary_driver": "One concise sentence explaining the deciding factor"
  }},
  "divergence": {{
    "value": 0.0,
    "direction": "balanced",
    "severity": "none",
    "interpretation": "balanced"
  }},
  "decision": {{
    "action": "train",
    "intensity_target": "moderate",
    "volume_modifier": 0.0,
    "specific_workout_type": null,
    "duration_minutes_suggested": null
  }},
  "risk": {{
    "injury_risk_level": "low",
    "acwr_external": 0.0,
    "acwr_internal": 0.0,
    "divergence": 0.0,
    "days_since_rest": 0,
    "flags": [],
    "pain_location": null
  }},
  "context": {{
    "autopsy_informed": false,
    "alignment_trend": "insufficient_data",
    "training_stage": null,
    "weeks_to_a_race": null,
    "weekly_plan_prescribed": null,
    "weekly_plan_deviation": false,
    "weekly_plan_deviation_reason": null
  }},
  "meta": {{
    "model_used": "claude-sonnet-4-6",
    "generation_timestamp": "ISO8601",
    "coaching_spectrum": 50,
    "risk_tolerance": "{recommendation_style}",
    "tokens_used": {{"input": 0, "output": 0}},
    "athlete_model_injected": false,
    "div_low_n": 0,
    "threshold_n": 0,
    "divergence_overtraining_threshold": 0.0
  }}
}}
</structured_output>

Allowed enum values:
- assessment.primary_signal: divergence | acwr_external | acwr_internal | days_since_rest | pattern
- assessment.category: normal_progression | mandatory_rest | overtraining_risk | divergence_warning | detraining_signal | recovery_needed | undertraining_opportunity
- divergence.direction: positive | negative | balanced
- divergence.severity: none | mild | moderate | high | critical
- divergence.interpretation: overtraining_risk | detraining | balanced | insufficient_data
- decision.action: train | rest | cross_train | reduce
- decision.intensity_target: easy | moderate | hard | race_effort | none
- risk.injury_risk_level: low | moderate | high | critical
- risk.pain_location: Extract from athlete notes — the specific body part if pain is mentioned (e.g., "left knee", "right achilles", "lower back", "hip flexor"). Set to null if no pain is mentioned in the notes.
- context.alignment_trend: improving | stable | declining | insufficient_data
"""

    return prompt


def check_activity_for_date(user_id, date_str):
    """Check if user has recorded any activity for the specified date."""
    try:
        from db_utils import execute_query

        result = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM activities 
            WHERE user_id = %s AND date = %s
            """,
            (user_id, date_str),
            fetch=True
        )

        if result and result[0]:
            count = dict(result[0])['count']
            return count > 0

        return False

    except Exception as e:
        logger.error(f"Error checking activity for date {date_str}: {str(e)}")
        return False


def check_journal_for_date(user_id, date_str):
    """Check if user has saved journal observations (energy or RPE) for the specified date."""
    try:
        from db_utils import execute_query
        result = execute_query(
            """
            SELECT COUNT(*) as count
            FROM journal_entries
            WHERE user_id = %s AND date = %s
              AND (energy_level IS NOT NULL OR rpe_score IS NOT NULL)
            """,
            (user_id, date_str),
            fetch=True
        )
        if result and result[0]:
            return dict(result[0])['count'] > 0
        return False
    except Exception as e:
        logger.error(f"Error checking journal for date {date_str}: {str(e)}")
        return False


def get_recent_activities(days=ACTIVITY_ANALYSIS_DAYS, user_id=None):
    """Get recent activities using unified service for consistency."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Use the unified service instead of custom logic
        activities = UnifiedMetricsService.get_recent_activities_for_analysis(days, user_id)

        logger.info(f"LLM retrieved {len(activities)} activities from unified service for user {user_id}")

        return activities

    except Exception as e:
        logger.error(f"Error getting recent activities for LLM user {user_id}: {str(e)}")
        return []


def get_current_metrics(user_id=None):
    """Get current training metrics using unified service for consistency."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Use the unified metrics service instead of custom logic
        unified_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)

        if not unified_metrics:
            logger.warning(f"No unified metrics available for LLM recommendation for user {user_id}")
            return None

        # Log the exact values being used
        logger.info(f"LLM using unified metrics for user {user_id}:")
        logger.info(f"  External ACWR: {unified_metrics['external_acwr']}")
        logger.info(f"  Internal ACWR: {unified_metrics['internal_acwr']}")
        logger.info(f"  Normalized Divergence: {unified_metrics['normalized_divergence']}")
        logger.info(f"  Days since rest: {unified_metrics['days_since_rest']}")
        logger.info(f"  Latest activity date: {unified_metrics['latest_activity_date']}")

        return unified_metrics

    except Exception as e:
        logger.error(f"Error getting current metrics for LLM user {user_id}: {str(e)}")
        return None


def analyze_training_patterns(activities):
    """Analyze training patterns from activities."""
    if not activities:
        return {
            'weekly_volume_trend': 'insufficient data',
            'intensity_distribution': 'insufficient data',
            'workout_type_frequency': 'insufficient data',
            'elevation_pattern': 'insufficient data'
        }

    # Group activities by week
    weeks = {}
    for activity in activities:
        date = activity['date']
        date_obj = safe_datetime_parse(date)
        week_num = date_obj.isocalendar()[1]

        if week_num not in weeks:
            weeks[week_num] = []

        weeks[week_num].append(activity)

    # Calculate weekly volumes
    weekly_volumes = []
    for week_num, week_activities in sorted(weeks.items()):
        total_distance = sum(act.get('distance_miles', 0) for act in week_activities)
        weekly_volumes.append((week_num, total_distance))

    # Determine volume trend
    volume_trend = 'stable'
    if len(weekly_volumes) >= 2:
        last_week = weekly_volumes[-1][1]
        prev_week = weekly_volumes[-2][1]

        if last_week > prev_week * 1.15:
            volume_trend = 'increasing'
        elif last_week < prev_week * 0.85:
            volume_trend = 'decreasing'

    # Analyze workout types
    workout_types = {}
    for activity in activities:
        activity_type = activity.get('type', 'unknown')
        if activity_type:
            workout_types[activity_type] = workout_types.get(activity_type, 0) + 1

    workout_type_freq = ', '.join([f"{type}: {count}" for type, count in
                                   sorted(workout_types.items(), key=lambda x: x[1], reverse=True)[:3]])

    # Count workouts in intensity zones based on TRIMP
    intensity_zones = {'easy': 0, 'moderate': 0, 'hard': 0}

    for activity in activities:
        # Use HR zones instead of TRIMP for more accurate intensity classification
        zone1_time = activity.get('time_in_zone1', 0)
        zone2_time = activity.get('time_in_zone2', 0)
        zone3_time = activity.get('time_in_zone3', 0)
        zone4_time = activity.get('time_in_zone4', 0)
        zone5_time = activity.get('time_in_zone5', 0)
        
        total_zone_time = zone1_time + zone2_time + zone3_time + zone4_time + zone5_time
        
        if total_zone_time == 0:
            # Fallback to TRIMP if no HR zone data
            trimp = activity.get('trimp', 0)
            if trimp <= 30:
                intensity_zones['easy'] += 1
            elif trimp <= 70:
                intensity_zones['moderate'] += 1
            else:
                intensity_zones['hard'] += 1
        else:
            # Classify based on HR zone distribution
            zone1_pct = zone1_time / total_zone_time * 100
            zone2_pct = zone2_time / total_zone_time * 100
            zone3_pct = zone3_time / total_zone_time * 100
            zone4_pct = zone4_time / total_zone_time * 100
            zone5_pct = zone5_time / total_zone_time * 100
            
            if zone1_pct > 50 or (zone1_pct + zone2_pct) > 70:
                intensity_zones['easy'] += 1
            elif zone4_pct > 30 or zone5_pct > 20 or (zone4_pct + zone5_pct) > 40:
                intensity_zones['hard'] += 1
            else:
                intensity_zones['moderate'] += 1

    total_workouts = sum(intensity_zones.values())
    intensity_distribution = "unknown"
    if total_workouts > 0:
        intensity_distribution = (
            f"Easy: {intensity_zones['easy'] / total_workouts * 100:.0f}%, "
            f"Moderate: {intensity_zones['moderate'] / total_workouts * 100:.0f}%, "
            f"Hard: {intensity_zones['hard'] / total_workouts * 100:.0f}%"
        )

    # Analyze elevation patterns
    elevation_gains = [activity.get('elevation_gain_feet', 0) for activity in activities]
    avg_elevation = sum(elevation_gains) / len(elevation_gains) if elevation_gains else 0

    elevation_pattern = 'flat'
    if avg_elevation > 500:
        elevation_pattern = 'hilly'
    elif avg_elevation > 200:
        elevation_pattern = 'rolling'

    return {
        'weekly_volume_trend': volume_trend,
        'intensity_distribution': intensity_distribution,
        'workout_type_frequency': workout_type_freq,
        'elevation_pattern': elevation_pattern
    }


def parse_llm_response(response_text):
    """Extract daily_recommendation and structured_output from a single-section LLM response.

    Expects:
        DAILY RECOMMENDATION
        [200-230 word prose]

        <structured_output>{ ... }</structured_output>

    weekly_recommendation and pattern_insights are always returned as empty strings —
    those concerns are owned by dedicated systems (Coach page weekly program, autopsy)
    and are no longer generated in the daily call.
    """
    import re

    sections = {
        'daily_recommendation': '',
        'weekly_recommendation': '',
        'pattern_insights': '',
        'structured_output': None
    }

    if not response_text or not response_text.strip():
        logger.error("Empty response text received")
        return sections

    # Extract structured JSON block first (before any text manipulation)
    sections['structured_output'] = extract_structured_output(response_text)

    # Strip <structured_output> block — already captured above; remove it so it doesn't
    # appear inside the prose capture
    cleaned_response = re.sub(
        r'<structured_output>.*?</structured_output>', '', response_text.strip(), flags=re.DOTALL
    ).strip()

    logger.info(f"Parsing response of length {len(cleaned_response)}")
    logger.info(f"Response preview: {cleaned_response[:200]}...")

    # Extract DAILY RECOMMENDATION section.
    # Handles plain text, bold (**DAILY...**), and markdown header (#/##) variants.
    # Captures everything after the header to end-of-string.
    daily_match = re.search(
        r'(?:\*{0,2}#{0,2}\s*)?DAILY\s+RECOMMENDATION:?\*{0,2}\s+(.*)',
        cleaned_response, re.DOTALL | re.IGNORECASE
    )

    if daily_match:
        raw_section = daily_match.group(1).strip()
        logger.info(f"✅ Extracted daily recommendation: {len(raw_section)} chars")
    else:
        raw_section = cleaned_response
        logger.warning("No DAILY RECOMMENDATION header found — using full response as daily recommendation")

    # Clean markdown formatting and collapse excess blank lines
    sections['daily_recommendation'] = process_markdown(raw_section)
    sections['daily_recommendation'] = re.sub(r'\n{2,}', '\n', sections['daily_recommendation']).strip()

    # Final validation
    logger.info("FINAL PARSED SECTIONS:")
    if sections['daily_recommendation'] and len(sections['daily_recommendation']) > 10:
        logger.info(f"✅ daily_recommendation: {len(sections['daily_recommendation'])} characters")
    else:
        logger.warning("❌ daily_recommendation: EMPTY or too short")

    return sections


def generate_activity_autopsy_enhanced(user_id, date_str, prescribed_action, actual_activities, observations):
    """
    Generate AI autopsy comparing prescribed vs actual training using Training Reference Guide.
    Enhanced version that includes alignment scoring and structured learning insights.
    
    This is the primary autopsy generation function. Use this instead of the deprecated
    generate_activity_autopsy() function.
    
    Args:
        user_id (int): User ID for multi-user support
        date_str (str): Date in YYYY-MM-DD format
        prescribed_action (str): The "Today" section from AI recommendation
        actual_activities (str): Summary of what user actually did
        observations (dict): User's energy, RPE, pain, notes
        
    Returns:
        dict: Contains 'analysis' (str) and 'alignment_score' (int 1-10)
    """
    try:
        logger.info(f"Generating enhanced autopsy for user {user_id}, date {date_str}")

        # Get user's coaching style preference
        spectrum_value = get_user_coaching_spectrum(user_id)
        tone_instructions = get_coaching_tone_instructions(spectrum_value)

        # Create autopsy prompt - focuses on comparing prescribed vs actual, no metrics needed
        prompt = create_enhanced_autopsy_prompt_with_scoring(
            date_str,
            prescribed_action,
            actual_activities,
            observations,
            tone_instructions
        )

        # Get specialized settings for autopsy analysis from config
        autopsy_settings = CONFIG.get('specialized_prompts', {}).get('autopsy_analysis', {})
        autopsy_temperature = autopsy_settings.get('temperature', 0.25)
        autopsy_max_tokens = autopsy_settings.get('max_tokens', 3000)
        
        logger.info(f"Calling API for autopsy with temperature={autopsy_temperature}, max_tokens={autopsy_max_tokens}")

        # Call Claude — use Haiku for autopsy scoring (Phase 2 routing)
        response = call_claude(prompt, temperature=autopsy_temperature, max_tokens=autopsy_max_tokens, task='autopsy')

        if not response:
            logger.error("No response from Anthropic API for enhanced autopsy generation")
            return generate_basic_autopsy_fallback_enhanced(prescribed_action, actual_activities, observations)

        # Parse autopsy response to extract analysis and alignment score
        autopsy_data = parse_enhanced_autopsy_response(response)

        # NOTE: update_athlete_model() is called in save_journal_entry() AFTER Phase C
        # (classify_deviation) so that deviation_reason is available for threshold calibration.
        return autopsy_data

    except Exception as e:
        logger.error(f"Error generating enhanced autopsy: {str(e)}", exc_info=True)
        logger.error(f"Falling back to basic autopsy due to error")
        return generate_basic_autopsy_fallback_enhanced(prescribed_action, actual_activities, observations)


def get_user_coaching_spectrum(user_id):
    """Get user's coaching spectrum preference with fallback"""
    try:
        result = execute_query("""
            SELECT coaching_style_spectrum, coaching_tone 
            FROM user_settings 
            WHERE id = %s
        """, (user_id,), fetch=True)

        if result and len(result) > 0:
            user_data = result[0]
            spectrum_value = user_data.get('coaching_style_spectrum')

            # Fallback to coaching_tone if spectrum not set
            if spectrum_value is None:
                coaching_tone = user_data.get('coaching_tone', 'supportive')
                spectrum_value = map_coaching_tone_to_spectrum(coaching_tone)

            return spectrum_value
        else:
            return 50  # Default to supportive

    except Exception as e:
        logger.error(f"Error fetching coaching spectrum for user {user_id}: {str(e)}")
        return 50


def map_coaching_tone_to_spectrum(coaching_tone):
    """Map existing coaching_tone to spectrum value"""
    tone_map = {
        'casual': 12,
        'supportive': 37,
        'motivational': 62,
        'analytical': 87
    }
    return tone_map.get(coaching_tone, 50)


def get_coaching_tone_instructions(spectrum_value):
    """Generate tone instructions based on spectrum position"""
    if spectrum_value <= 25:
        return """
TONE & APPROACH for CASUAL COACHING:
- Use friendly, conversational language ("Nice work!", "How did that feel?")
- Focus on the joy and health benefits of training
- Minimize technical jargon and complex metrics
- Frame any adjustments as suggestions, not requirements
- Celebrate consistency over performance metrics
- Emphasize sustainable, enjoyable training
        """
    elif spectrum_value <= 50:
        return """
TONE & APPROACH for SUPPORTIVE COACHING:
- Lead with positive affirmation and accomplishment recognition
- Frame deviations as learning opportunities, not mistakes
- Use encouraging language ("Great progress!", "You're building strength!")
- Acknowledge effort and commitment consistently
- Provide gentle guidance with rationale
- Focus on building confidence through small wins
        """
    elif spectrum_value <= 75:
        return """
TONE & APPROACH for MOTIVATIONAL COACHING:
- Balance encouragement with performance challenges
- Set clear, achievable targets for improvement
- Use action-oriented language ("Let's push for...", "Time to level up...")
- Provide constructive feedback with growth focus
- Highlight potential and progress toward goals
- Challenge athlete while maintaining support
        """
    else:
        return """
TONE & APPROACH for ANALYTICAL COACHING:
- Provide detailed, technical analysis of performance data
- Use precise metrics and evidence-based recommendations
- Direct feedback on training execution and physiological response
- Focus on optimization and performance enhancement
- Reference specific training science principles
- Give clear, actionable technical adjustments
        """


def get_user_preferences(user_id):
    """Fetch coaching spectrum and recommendation style in a single user_settings query.

    Returns dict: {spectrum_value: int, recommendation_style: str}.
    Replaces separate get_user_coaching_spectrum() + get_user_recommendation_style() calls
    in the recommendation generation path.
    """
    try:
        result = execute_query("""
            SELECT coaching_style_spectrum, coaching_tone, recommendation_style
            FROM user_settings
            WHERE id = %s
        """, (user_id,), fetch=True)

        if result and len(result) > 0:
            row = result[0]
            spectrum_value = row.get('coaching_style_spectrum')
            if spectrum_value is None:
                spectrum_value = map_coaching_tone_to_spectrum(row.get('coaching_tone', 'supportive'))
            recommendation_style = row.get('recommendation_style') or 'balanced'
            logger.info(f"User {user_id} preferences: spectrum={spectrum_value}, style={recommendation_style}")
            return {'spectrum_value': spectrum_value, 'recommendation_style': recommendation_style}
        else:
            return {'spectrum_value': 50, 'recommendation_style': 'balanced'}

    except Exception as e:
        logger.error(f"Error fetching preferences for user {user_id}: {str(e)}")
        return {'spectrum_value': 50, 'recommendation_style': 'balanced'}


def get_user_recommendation_style(user_id):
    """Get user's recommendation style preference (conservative/balanced/adaptive/aggressive)"""
    try:
        result = execute_query("""
            SELECT recommendation_style
            FROM user_settings
            WHERE id = %s
        """, (user_id,), fetch=True)

        if result and len(result) > 0:
            style = result[0].get('recommendation_style', 'balanced')
            logger.info(f"User {user_id} recommendation_style: {style}")
            return style
        else:
            logger.info(f"No recommendation_style found for user {user_id}, defaulting to 'balanced'")
            return 'balanced'

    except Exception as e:
        logger.error(f"Error fetching recommendation_style for user {user_id}: {str(e)}")
        return 'balanced'


def get_adjusted_thresholds(recommendation_style):
    """
    Get risk thresholds adjusted based on user's training philosophy.
    
    Returns a dict with adjusted thresholds for:
    - ACWR high risk level
    - Days since rest mandatory
    - Divergence overtraining threshold
    - Divergence moderate risk threshold
    """
    thresholds = {
        'conservative': {
            'acwr_high_risk': 1.2,          # Trigger warnings earlier
            'days_since_rest_max': 6,        # Enforce rest after 6 days
            'divergence_overtraining': -0.10,  # More sensitive to fatigue
            'divergence_moderate_risk': -0.03, # Earlier recovery warnings
            'acwr_undertraining': 0.85,      # Less aggressive push for more load
            'description': 'Lower risk tolerance, earlier warnings, more recovery emphasis'
        },
        'balanced': {
            'acwr_high_risk': 1.3,          # Standard evidence-based threshold
            'days_since_rest_max': 7,        # Standard rest enforcement
            'divergence_overtraining': -0.15,  # Standard threshold
            'divergence_moderate_risk': -0.05, # Standard recovery threshold
            'acwr_undertraining': 0.8,       # Standard progression opportunity
            'description': 'Evidence-based thresholds, balanced risk approach'
        },
        'adaptive': {
            'acwr_high_risk': 1.35,         # Slightly more flexible
            'days_since_rest_max': 7,        # Same as balanced but recommendations adapt
            'divergence_overtraining': -0.15,  # Same as balanced
            'divergence_moderate_risk': -0.05, # Same as balanced
            'acwr_undertraining': 0.8,       # Same as balanced
            'description': 'Adjusts based on individual response patterns and recovery'
        },
        'aggressive': {
            'acwr_high_risk': 1.5,          # Higher risk tolerance
            'days_since_rest_max': 8,        # Allow more consecutive training days
            'divergence_overtraining': -0.20,  # Higher fatigue tolerance
            'divergence_moderate_risk': -0.08, # Less conservative recovery warnings
            'acwr_undertraining': 0.75,      # More aggressive progression push
            'description': 'Higher risk tolerance, aggressive progression, performance-focused'
        }
    }
    
    selected_thresholds = thresholds.get(recommendation_style, thresholds['balanced'])
    logger.info(f"Using {recommendation_style} thresholds: {selected_thresholds['description']}")
    
    return selected_thresholds


def apply_athlete_model_to_thresholds(thresholds, user_id):
    """Override style-based divergence thresholds with the athlete's personal values when
    the model has been calibrated from real autopsy data.

    Returns a new dict — never mutates the input.
    The injury signal framework is divergence-based; ACWR thresholds are not overridden
    here (the acwr_sweet_spot_low/high fields are retired — see Phase 3-A of QC plan).
    """
    try:
        model = get_athlete_model(user_id)
        if not model:
            return thresholds

        calibrated = dict(thresholds)
        changes = []

        # Override divergence_overtraining from personalized breakdown threshold.
        # Stored as positive absolute value; applied as negative.
        # Defaults (0.15 → -0.15) match the balanced style baseline — no-op until calibrated.
        div_threshold = model.get('divergence_injury_threshold') or 0.15
        calibrated['divergence_overtraining'] = -float(div_threshold)
        changes.append(f"divergence_overtraining→{-div_threshold:.3f}")

        # Override divergence_moderate_risk from personalized productive window edge.
        # Marks the boundary between productive training and elevated stress for this athlete.
        # Default (-0.05) matches the balanced style baseline — no-op until calibrated.
        div_low = model.get('typical_divergence_low') or -0.05
        calibrated['divergence_moderate_risk'] = float(div_low)
        changes.append(f"divergence_moderate_risk→{div_low:.3f}")

        if changes:
            logger.info(
                f"Thresholds calibrated for user {user_id}: {', '.join(changes)}"
            )
        return calibrated

    except Exception as e:
        logger.warning(f"Could not apply athlete model to thresholds for user {user_id}: {e}")
    return thresholds


def get_coaching_style_from_spectrum(spectrum_value):
    """Convert spectrum value to coaching style configuration (for API endpoints)"""
    if spectrum_value <= 25:
        return {
            'style': 'casual',
            'label': 'Casual',
            'description': 'Relaxed, friendly guidance'
        }
    elif spectrum_value <= 50:
        return {
            'style': 'supportive',
            'label': 'Supportive',
            'description': 'Encouraging with gentle guidance'
        }
    elif spectrum_value <= 75:
        return {
            'style': 'motivational',
            'label': 'Motivational',
            'description': 'Goal-oriented with push for improvement'
        }
    else:
        return {
            'style': 'analytical',
            'label': 'Analytical',
            'description': 'Technical, data-driven coaching'
        }

def create_enhanced_autopsy_prompt_with_scoring(date_str, prescribed_action, actual_activities, observations,
                                                tone_instructions=None):
    """Create autopsy prompt that compares prescribed vs actual without metrics confusion."""
    try:
        # Format user observations
        energy_level = observations.get('energy_level', 'Not recorded')
        rpe_score = observations.get('rpe_score', 'Not recorded')
        pain_percentage = observations.get('pain_percentage', 'Not recorded')
        notes = observations.get('notes', 'None')

        # Format activity data (handle both dict and string formats)
        if isinstance(actual_activities, dict):
            activity_type = actual_activities.get('type', 'unknown')
            distance = actual_activities.get('distance', 0)
            elevation = actual_activities.get('elevation', 0)
            trimp = actual_activities.get('total_trimp', 0)
            classification = actual_activities.get('workout_classification', 'unknown')
            activity_summary = f"{activity_type} - {distance} miles, {elevation}ft elevation, {trimp} TRIMP, {classification} intensity"
        else:
            activity_summary = str(actual_activities)

        # Add tone instructions if provided
        tone_section = ""
        if tone_instructions:
            tone_section = f"{tone_instructions}\n\n"

        training_guide = load_training_guide()

        prompt = f"""You are an expert endurance coach conducting a training autopsy analysis.

{tone_section}ANALYSIS DATE: {date_str}

PRESCRIBED TRAINING DECISION:
{prescribed_action}

ACTUAL TRAINING COMPLETED:
{activity_summary}

USER OBSERVATIONS:
- Energy Level: {energy_level}/5 (How did the athlete feel going into the session? 5=Fired up, 1=Barely got out of bed)
- RPE (Rate of Perceived Exertion): {rpe_score}/10 (How hard did the workout feel? 10=Maximum effort, 1=Very easy)
- Pain %: {pain_percentage}% (Percentage of time during the activity that the athlete was thinking about pain)
- Additional Notes: {notes}

DIVERGENCE SIGN CONVENTION: {NORMALIZED_DIVERGENCE_FORMULA}
  If the prescribed recommendation flagged a positive divergence as a concern, that was an error — do NOT echo it.

### TRAINING REFERENCE FRAMEWORK
{training_guide if training_guide else "Apply evidence-based training principles."}

AUTOPSY ANALYSIS INSTRUCTIONS:

You must provide analysis in EXACTLY this format for parsing{', applying the specified coaching tone throughout' if tone_instructions else ''}:

ALIGNMENT_SCORE: [X/10]

ALIGNMENT ASSESSMENT:
[{('Apply the specified coaching tone. ' if tone_instructions else '')}Compare prescribed vs actual training. Score 10=perfect compliance, 8-9=minor deviations, 5-7=moderate changes, 1-4=major deviations. Consider volume, intensity, workout type, and execution quality. If athlete deviated, check notes for reasons (injury, time constraints, etc.).]

PHYSIOLOGICAL RESPONSE ANALYSIS:
[{('Use the specified coaching style. ' if tone_instructions else '')}Evaluate energy/RPE/pain levels relative to the workout completed. Was the response appropriate for the effort? Signs of positive adaptation, fatigue, or concerns? How did pre-session energy affect execution?]

LEARNING INSIGHTS & COACHING TAKEAWAYS:
[{('Apply the coaching tone throughout. ' if tone_instructions else '')}Key takeaways from today's session. Why did athlete deviate (if applicable)? What does response reveal about adaptation and adherence patterns? Any coaching adjustments needed based on alignment and physiological response?]

CRITICAL REQUIREMENTS:
- Start with "ALIGNMENT_SCORE: X/10" where X is a number 1-10
- Keep total response under 300 words for Journal display
- Focus on actionable insights about compliance and response
- Check user notes for context on deviations{(' - Apply the specified coaching tone consistently throughout all sections' if tone_instructions else '')}
"""

        return prompt

    except Exception as e:
        logger.error(f"Error creating enhanced autopsy prompt: {str(e)}")
        # Fallback to basic prompt without metrics
        return f"""Analyze this workout:
Prescribed: {prescribed_action}
Actual: {actual_activities}
Observations: {observations}
Provide alignment score and brief analysis."""


def parse_enhanced_autopsy_response(response):
    """Parse enhanced autopsy response to extract alignment score and analysis."""
    try:
        import re

        # Extract alignment score — handle two LLM output patterns:
        #   1. Labeled:  "ALIGNMENT_SCORE: 9/10"  (required format)
        #   2. Unlabeled: "9.5/10" as first line  (LLM sometimes skips the label)
        # Both patterns accept decimals (e.g. 9.5) and convert to nearest integer.
        score_match = re.search(r'ALIGNMENT_SCORE:\s*([\d.]+)/10', response, re.IGNORECASE)
        if not score_match:
            score_match = re.search(r'^\s*([\d.]+)/10', response, re.MULTILINE)
        alignment_score = round(float(score_match.group(1))) if score_match else 5

        # Ensure score is in valid range
        alignment_score = max(1, min(10, alignment_score))

        # Remove the score prefix from the stored analysis text so the banner
        # is the single source of truth and the text doesn't repeat it.
        cleaned_analysis = re.sub(r'ALIGNMENT_SCORE:\s*[\d.]+/10\s*', '', response, flags=re.IGNORECASE).strip()
        cleaned_analysis = re.sub(r'^[\d.]+/10\s*', '', cleaned_analysis).strip()
        cleaned_analysis = process_markdown(cleaned_analysis)

        return {
            'analysis': cleaned_analysis,
            'alignment_score': alignment_score
        }

    except Exception as e:
        logger.error(f"Error parsing enhanced autopsy response: {str(e)}")
        return {
            'analysis': response[:1000] if response else "Error parsing autopsy analysis",
            'alignment_score': 5
        }


def generate_basic_autopsy_fallback_enhanced(prescribed_action, actual_activities, observations):
    """Enhanced fallback with alignment scoring."""
    try:
        # Simple alignment assessment
        alignment_score = 6  # Default moderate alignment

        # Try to determine basic alignment
        if isinstance(actual_activities, dict):
            distance = actual_activities.get('distance', 0)
            trimp = actual_activities.get('total_trimp', 0)
            activity_summary = f"{distance} miles, {trimp} TRIMP"
        else:
            activity_summary = str(actual_activities)

        energy = observations.get('energy_level', 'Not recorded')
        rpe = observations.get('rpe_score', 'Not recorded')
        pain = observations.get('pain_percentage', 'Not recorded')

        analysis = f"""ALIGNMENT ASSESSMENT:
Training completed with basic alignment assessment. Detailed comparison requires enhanced AI analysis.

PHYSIOLOGICAL RESPONSE ANALYSIS:
User reported energy level of {energy}/5, RPE of {rpe}/10, and pain level of {pain}%. These metrics provide baseline insight into training tolerance and recovery status.

LEARNING INSIGHTS & TOMORROW'S IMPLICATIONS:
Fallback autopsy generated due to system limitations. For detailed learning insights, ensure Training Reference Guide is available and AI service is operational. Future training should consider reported energy and pain levels.

Activity Summary: {activity_summary}
Generated: {get_app_current_date().strftime('%Y-%m-%d %H:%M:%S')}"""

        return {
            'analysis': analysis,
            'alignment_score': alignment_score,
            'is_fallback': True,
        }

    except Exception as e:
        logger.error(f"Error generating enhanced fallback autopsy: {str(e)}")
        return {
            'analysis': f"Enhanced autopsy generation failed: {str(e)}",
            'alignment_score': 5,
            'is_fallback': True,
        }


def compute_readiness_state(readiness_row, hrv_baseline, hrv_baseline_count,
                            rhr_baseline, rhr_baseline_count, athlete_model):
    """Synthesize wellness signals into a readiness state: GREEN, AMBER, or RED.

    Args:
        readiness_row: dict with wellness fields from journal_entries (or None).
        hrv_baseline: float — 30-day HRV average (or None if insufficient data).
        hrv_baseline_count: int — number of readings in the baseline.
        rhr_baseline: float — 7-day RHR average (or None).
        rhr_baseline_count: int — number of readings in the baseline.
        athlete_model: dict from get_athlete_model() for personalised thresholds (or None).

    Returns:
        dict: {state, component_flags, confidence, narrative}
    """
    model = athlete_model or {}
    hrv_suppression_threshold = float(model.get('hrv_suppression_threshold') or 0.85)
    rhr_elevation_threshold   = float(model.get('rhr_elevation_threshold') or 1.08)

    row          = readiness_row or {}
    hrv_value    = row.get('hrv_value')
    rhr_value    = row.get('resting_hr')
    sleep_secs   = row.get('sleep_duration_secs')
    sleep_score  = row.get('sleep_score')
    # morning_soreness (morning entry) or pain_percentage (post-workout)
    soreness     = row.get('morning_soreness') if row.get('morning_soreness') is not None else row.get('pain_percentage')

    hrv_suppressed   = False
    rhr_elevated     = False
    sleep_deficit    = False
    sleep_poor_score = False
    high_soreness    = False
    signals_with_data = 0.0

    # HRV suppression (requires ≥5 baseline days for full credit)
    if hrv_value is not None:
        if hrv_baseline and hrv_baseline_count >= 5:
            signals_with_data += 1
            if float(hrv_value) < float(hrv_baseline) * hrv_suppression_threshold:
                hrv_suppressed = True
        else:
            signals_with_data += 0.5  # value present but no reliable baseline yet

    # RHR elevation (requires ≥3 baseline days)
    if rhr_value is not None:
        if rhr_baseline and rhr_baseline_count >= 3:
            signals_with_data += 1
            if float(rhr_value) > float(rhr_baseline) * rhr_elevation_threshold:
                rhr_elevated = True
        else:
            signals_with_data += 0.5

    if sleep_secs is not None:
        signals_with_data += 1
        if float(sleep_secs) < 21600:  # < 6 hrs
            sleep_deficit = True

    if sleep_score is not None:
        signals_with_data += 1
        if int(sleep_score) < 60:
            sleep_poor_score = True

    if soreness is not None:
        signals_with_data += 1
        if float(soreness) >= 70:
            high_soreness = True

    # Max theoretical confidence is 1.0 (all 5 signals present with reliable baselines).
    # Signals without baselines contribute 0.5 each, so confidence may cap below 1.0
    # until enough baseline readings accumulate (≥5 for HRV, ≥3 for RHR).
    confidence = round(signals_with_data / 5.0, 2)

    # Determine state
    red_conditions = (
        (hrv_suppressed and rhr_elevated) or
        (hrv_suppressed and sleep_deficit) or
        (high_soreness and (hrv_suppressed or rhr_elevated)) or
        (sleep_score is not None and int(sleep_score) < 40) or
        (soreness is not None and float(soreness) >= 85)
    )
    flag_count = sum([hrv_suppressed, rhr_elevated, sleep_deficit, sleep_poor_score, high_soreness])

    if red_conditions:
        state = "RED"
    elif flag_count >= 1:
        state = "AMBER"
    else:
        state = "GREEN"

    # Confidence downgrade: < 0.4 data coverage → pull back one level
    if confidence < 0.4:
        if state == "RED":
            state = "AMBER"
        elif state == "AMBER":
            state = "GREEN"

    # Build narrative
    if state == "GREEN":
        narrative = "Wellness signals normal — cleared for planned training load."
    elif state == "AMBER":
        active = []
        if hrv_suppressed:   active.append("HRV suppressed")
        if rhr_elevated:     active.append("RHR elevated")
        if sleep_deficit:    active.append("sleep deficit")
        if sleep_poor_score: active.append("poor sleep score")
        if high_soreness:    active.append("high soreness")
        flags_str = ", ".join(active) if active else "one or more signals elevated"
        narrative = f"Caution: {flags_str} — monitor effort, reduce intensity if needed."
    else:
        narrative = "Multiple recovery signals active — strongly consider rest or easy recovery session."

    return {
        "state": state,
        "component_flags": {
            "hrv_suppressed":   hrv_suppressed,
            "rhr_elevated":     rhr_elevated,
            "sleep_deficit":    sleep_deficit,
            "sleep_poor_score": sleep_poor_score,
            "high_soreness":    high_soreness,
        },
        "confidence": confidence,
        "narrative": narrative,
    }


def get_athlete_model_context(user_id, athlete_model=None):
    """Return a formatted string for prompt injection based on the athlete's persistent model.

    Phase 3 — Persistent Athlete Model.

    Args:
        user_id: User ID.
        athlete_model: Optional pre-fetched model dict. If None, fetches from DB.

    Returns:
        str: Multi-line context block ready to embed in a prompt, OR
             an empty string if no model exists or the model has fewer than 3 autopsies.
    """
    MIN_AUTOPSIES = 3

    try:
        model = athlete_model if athlete_model is not None else get_athlete_model(user_id)
        if not model:
            return ""

        total_autopsies = model.get('total_autopsies', 0) or 0

        if total_autopsies < MIN_AUTOPSIES:
            # Still in learning mode — return a brief note so the LLM is aware
            return "ATHLETE MODEL: LEARNING (building athlete model — insufficient data yet)"

        # Sufficient data — build a full context block
        avg_alignment = model.get('avg_lifetime_alignment', 5.0) or 5.0
        trend = model.get('recent_alignment_trend', 'insufficient_data') or 'insufficient_data'
        div_low = model.get('typical_divergence_low', -0.05) or -0.05
        div_injury = model.get('divergence_injury_threshold', 0.15) or 0.15
        last_date = model.get('last_autopsy_date', 'unknown')
        div_low_n = model.get('div_low_n', 0) or 0
        threshold_n = model.get('threshold_n', 0) or 0

        div_low_calibration = (
            f"calibrated from {div_low_n} healthy days" if div_low_n >= 5
            else "population default — calibrating"
        )
        threshold_calibration = (
            f"calibrated from {threshold_n} distress events" if threshold_n >= 3
            else "population default — calibrating"
        )

        context = f"""### ATHLETE MODEL (learned from {total_autopsies} autopsies)
- Productive window edge: {div_low:.3f} ({div_low_calibration})
- Breakdown threshold: {-div_injury:.3f} ({threshold_calibration})
- Avg Lifetime Alignment Score: {avg_alignment:.1f}/10
- Recent Alignment Trend: {trend}
- Last Autopsy Date: {last_date}

COACHING NOTE: Use the athlete's personalized divergence window above instead of population defaults. Affirm training in the productive window. Flag risk only when divergence exceeds the breakdown threshold."""

        return context

    except Exception as e:
        logger.error(f"Error building athlete model context for user {user_id}: {e}")
        return "ATHLETE MODEL: UNAVAILABLE (fetch error — using population defaults)"


def update_athlete_model(user_id, autopsy_data):
    """Update the athlete's persistent model after a successful autopsy.

    Uses a weighted moving average (30% new, 70% historical) for alignment.
    Increments total_autopsies, updates last_autopsy_date, computes recent trend,
    and increments acwr_sweet_spot_confidence (capped at 1.0).

    Also checks the last 10 autopsies to update divergence_injury_threshold:
    if alignment drops below 5 on days where normalised divergence exceeded a
    threshold, that threshold is updated in the model.

    Computes typical_divergence_low/high from healthy training days (alignment >= 7,
    no pain, adequate energy) to establish the athlete's personal safe range.
    Requires N>=5 qualifying days; otherwise leaves the existing value untouched.

    Phase 3 — Persistent Athlete Model.

    Args:
        user_id (int): User ID.
        autopsy_data (dict): Must contain 'alignment_score' (int/float) and 'date' (str YYYY-MM-DD).
    """
    try:
        alignment_score = float(autopsy_data.get('alignment_score', 5))
        date_str = autopsy_data.get('date')

        # Fetch existing model (or create default values if not yet present)
        existing = get_athlete_model(user_id)
        if existing is None:
            # Bootstrap an empty row so the upsert has something to merge into
            upsert_athlete_model(user_id, {})
            existing = {
                'total_autopsies': 0,
                'avg_lifetime_alignment': 5.0,
                'acwr_sweet_spot_confidence': 0.0,
            }

        prev_total = existing.get('total_autopsies', 0) or 0
        prev_avg = existing.get('avg_lifetime_alignment', 5.0) or 5.0
        prev_confidence = existing.get('acwr_sweet_spot_confidence', 0.0) or 0.0

        # Weighted moving average: 30% new, 70% historical
        new_avg = (0.7 * prev_avg) + (0.3 * alignment_score)
        new_total = prev_total + 1

        # Confidence increases 0.05 per autopsy, capped at 1.0
        new_confidence = min(1.0, prev_confidence + 0.05)

        # Compute recent_alignment_trend from last 5 autopsies (most recent first)
        recent_scores_rows = execute_query(
            """
            SELECT alignment_score FROM ai_autopsies
            WHERE user_id = %s AND alignment_score IS NOT NULL
            ORDER BY date DESC
            LIMIT 5
            """,
            (user_id,),
            fetch=True
        )
        recent_scores = [r['alignment_score'] for r in (recent_scores_rows or [])]

        if len(recent_scores) >= 3:
            # Scores are in DESC order (most recent first).
            # Use endpoint comparison (most recent vs. oldest) to detect directional
            # movement — strict monotonicity nearly always produced 'stable'.
            if recent_scores[0] > recent_scores[-1]:
                trend = 'improving'
            elif recent_scores[0] < recent_scores[-1]:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'

        # Update divergence_injury_threshold:
        # Collect all physical-cause distress events where divergence is beyond the
        # athlete's productive training window edge (typical_divergence_low).
        # Requires N>=3 qualifying events; uses median for robustness.
        new_div_threshold = None
        new_threshold_n = None
        try:
            current_div_low = (existing or {}).get('typical_divergence_low') or -0.05
            distress_rows = execute_query(
                """
                SELECT act.normalized_divergence
                FROM ai_autopsies a
                JOIN activities act ON act.user_id = a.user_id AND act.date = a.date
                WHERE a.user_id = %s
                  AND a.deviation_reason = 'physical'
                  AND act.normalized_divergence IS NOT NULL
                  AND act.normalized_divergence < %s
                ORDER BY a.date DESC
                """,
                (user_id, current_div_low),
                fetch=True
            )
            if distress_rows and len(distress_rows) >= 3:
                distress_vals = sorted([r['normalized_divergence'] for r in distress_rows])
                mid = len(distress_vals) // 2
                median_div = distress_vals[mid]
                new_div_threshold = round(abs(median_div), 3)
                new_threshold_n = len(distress_vals)
                logger.info(
                    f"Computed breakdown threshold for user {user_id}: "
                    f"{-new_div_threshold:.3f} (median of {new_threshold_n} distress events, "
                    f"anchored to div_low={current_div_low:.3f})"
                )
        except Exception as div_err:
            logger.warning(f"Could not compute divergence_injury_threshold for user {user_id}: {div_err}")

        # Compute typical_divergence_low from healthy training days.
        # Healthy day = high alignment, no pain reported, adequate energy, real activity.
        # P20 of the distribution gives the lower edge of the productive training window.
        # Zero is the natural upper boundary (positive divergence = recovery by definition).
        # typical_divergence_high is not computed — positive divergence needs no personal calibration.
        new_div_low = None
        new_div_low_n = None
        try:
            healthy_rows = execute_query(
                """
                SELECT act.normalized_divergence
                FROM activities act
                JOIN ai_autopsies a ON a.user_id = act.user_id AND a.date = act.date
                LEFT JOIN journal_entries j ON j.user_id = act.user_id AND j.date = act.date
                WHERE act.user_id = %s
                  AND act.normalized_divergence IS NOT NULL
                  AND act.activity_id > 0
                  AND act.type != 'rest'
                  AND a.alignment_score >= 7
                  AND (j.pain_percentage IS NULL OR j.pain_percentage = 0)
                  AND (j.energy_level IS NULL OR j.energy_level >= 3)
                ORDER BY act.date DESC
                LIMIT 60
                """,
                (user_id,),
                fetch=True
            )
            if healthy_rows and len(healthy_rows) >= 5:
                div_values = sorted([r['normalized_divergence'] for r in healthy_rows])
                n = len(div_values)
                p20_idx = max(0, int(n * 0.20) - 1)
                new_div_low = round(div_values[p20_idx], 3)
                new_div_low_n = n
                logger.info(
                    f"Computed productive training window edge for user {user_id}: "
                    f"div_low={new_div_low} (n={n} healthy days)"
                )
        except Exception as div_range_err:
            logger.warning(f"Could not compute typical_divergence_low for user {user_id}: {div_range_err}")

        # Cache current HRV/RHR baselines and tighten HRV suppression threshold when
        # athlete underperformed on a day where HRV appeared normal (false negative).
        new_hrv_baseline_30d = None
        new_rhr_baseline_7d = None
        new_hrv_suppression_threshold = None
        try:
            hrv_b_row = execute_query(
                """SELECT AVG(hrv_value) AS hrv_avg
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= CURRENT_DATE - INTERVAL '30 days'
                     AND hrv_value IS NOT NULL""",
                (user_id,), fetch=True
            )
            if hrv_b_row and hrv_b_row[0] and hrv_b_row[0]['hrv_avg']:
                new_hrv_baseline_30d = round(float(hrv_b_row[0]['hrv_avg']), 1)

            rhr_b_row = execute_query(
                """SELECT AVG(resting_hr) AS rhr_avg
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= CURRENT_DATE - INTERVAL '7 days'
                     AND resting_hr IS NOT NULL""",
                (user_id,), fetch=True
            )
            if rhr_b_row and rhr_b_row[0] and rhr_b_row[0]['rhr_avg']:
                new_rhr_baseline_7d = int(round(float(rhr_b_row[0]['rhr_avg'])))

            # Tighten HRV suppression threshold if athlete underperformed (alignment < 5)
            # Adjust HRV suppression threshold based on alignment outcome:
            # - Tighten (+0.02) when athlete underperformed (alignment < 5) but HRV looked
            #   normal — threshold was too lenient, missing a real suppression signal.
            # - Loosen (-0.01) when athlete performed well (alignment >= 7) and HRV was
            #   above the threshold — threshold may be too aggressive, causing false positives.
            # Bounds: [0.75, 0.95]
            if new_hrv_baseline_30d and date_str:
                hrv_day_row = execute_query(
                    "SELECT hrv_value FROM journal_entries WHERE user_id = %s AND date = %s",
                    (user_id, date_str), fetch=True
                )
                hrv_today = hrv_day_row[0]['hrv_value'] if hrv_day_row and hrv_day_row[0] else None
                if hrv_today is not None:
                    current_threshold = float((existing or {}).get('hrv_suppression_threshold') or 0.85)
                    hrv_ratio = float(hrv_today) / new_hrv_baseline_30d
                    if alignment_score < 5 and hrv_ratio >= current_threshold:
                        # HRV appeared normal but athlete underperformed — tighten
                        new_hrv_suppression_threshold = min(round(current_threshold + 0.02, 2), 0.95)
                        logger.info(
                            f"Tightening HRV suppression threshold for user {user_id}: "
                            f"{current_threshold:.2f} → {new_hrv_suppression_threshold:.2f} "
                            f"(hrv_ratio={hrv_ratio:.2f}, alignment={alignment_score})"
                        )
                    elif alignment_score >= 7 and hrv_ratio >= current_threshold:
                        # HRV above threshold and athlete performed well — loosen slightly
                        new_hrv_suppression_threshold = max(round(current_threshold - 0.01, 2), 0.75)
                        logger.info(
                            f"Loosening HRV suppression threshold for user {user_id}: "
                            f"{current_threshold:.2f} → {new_hrv_suppression_threshold:.2f} "
                            f"(hrv_ratio={hrv_ratio:.2f}, alignment={alignment_score})"
                        )
        except Exception as hrv_learn_err:
            logger.warning(f"Could not update wellness thresholds for user {user_id}: {hrv_learn_err}")

        # Check for sustained physical distress pattern: 2 of last 5 autopsies physical.
        # Auto-sets or auto-clears early_warning_active based on current pattern.
        early_warning_active = False
        early_warning_message = None
        try:
            recent_rows = execute_query(
                """
                SELECT deviation_reason
                FROM ai_autopsies
                WHERE user_id = %s
                  AND deviation_reason IS NOT NULL
                ORDER BY date DESC
                LIMIT 5
                """,
                (user_id,),
                fetch=True
            )
            if recent_rows:
                physical_count = sum(1 for r in recent_rows if r['deviation_reason'] == 'physical')
                total_classified = len(recent_rows)
                if physical_count >= 2:
                    early_warning_active = True
                    early_warning_message = (
                        f"Physical distress signals on {physical_count} of your last "
                        f"{total_classified} workouts. Your coach is monitoring this pattern — "
                        f"consider reducing load until symptoms resolve."
                    )
                    logger.info(
                        f"Early warning SET for user {user_id}: "
                        f"{physical_count}/{total_classified} recent workouts physical distress"
                    )
        except Exception as ew_err:
            logger.warning(f"Could not compute early warning for user {user_id}: {ew_err}")

        updates = {
            'total_autopsies': new_total,
            'avg_lifetime_alignment': round(new_avg, 3),
            'acwr_sweet_spot_confidence': round(new_confidence, 4),
            'recent_alignment_trend': trend,
            'early_warning_active': early_warning_active,
            'early_warning_message': early_warning_message,
        }
        if date_str:
            updates['last_autopsy_date'] = date_str
        if new_div_threshold is not None:
            updates['divergence_injury_threshold'] = new_div_threshold
        if new_threshold_n is not None:
            updates['threshold_n'] = new_threshold_n
        if new_div_low is not None:
            updates['typical_divergence_low'] = new_div_low
        if new_div_low_n is not None:
            updates['div_low_n'] = new_div_low_n
        if new_hrv_baseline_30d is not None:
            updates['hrv_baseline_30d'] = new_hrv_baseline_30d
        if new_rhr_baseline_7d is not None:
            updates['rhr_baseline_7d'] = new_rhr_baseline_7d
        if new_hrv_suppression_threshold is not None:
            updates['hrv_suppression_threshold'] = new_hrv_suppression_threshold

        upsert_athlete_model(user_id, updates)
        logger.info(
            f"Updated athlete model for user {user_id}: total_autopsies={new_total}, "
            f"avg_alignment={new_avg:.2f}, confidence={new_confidence:.2f}, trend={trend}"
        )

    except Exception as e:
        logger.error(f"Error updating athlete model for user {user_id}: {e}")
        # Do not re-raise — athlete model update failure must never break autopsy flow


def get_recent_autopsy_insights(user_id, days=3):
    """
    Get recent autopsy insights to inform future training decisions.
    This is the key function that creates the learning loop.
    """
    try:
        cutoff_date = (get_app_current_date() - timedelta(days=days)).strftime('%Y-%m-%d')

        recent_autopsies = execute_query(
            """
            SELECT date, autopsy_analysis, alignment_score, deviation_reason, generated_at
            FROM ai_autopsies
            WHERE user_id = %s AND date >= %s
            ORDER BY date DESC
            LIMIT 5
            """,
            (user_id, cutoff_date),
            fetch=True
        )

        if not recent_autopsies:
            return None

        # Calculate average alignment and collect full autopsy texts
        alignment_scores = []
        latest_full_analysis = None

        for row in recent_autopsies:
            autopsy = dict(row)
            if autopsy['alignment_score']:
                alignment_scores.append(autopsy['alignment_score'])
            # Keep the most recent full autopsy text (rows are ordered DESC)
            if latest_full_analysis is None and autopsy.get('autopsy_analysis'):
                latest_full_analysis = autopsy['autopsy_analysis']

        avg_alignment = sum(alignment_scores) / len(alignment_scores) if alignment_scores else 5

        reason_breakdown = {
            'physical': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'physical'),
            'external': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'external'),
            'prescription_mismatch': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'prescription_mismatch'),
            'unknown': sum(1 for r in recent_autopsies if dict(r).get('deviation_reason') == 'unknown'),
        }

        return {
            'count': len(recent_autopsies),
            'avg_alignment': round(avg_alignment, 1),
            'latest_insights': latest_full_analysis,
            'alignment_trend': alignment_scores[-3:] if len(alignment_scores) >= 3 else alignment_scores,
            'reason_breakdown': reason_breakdown,
        }

    except Exception as e:
        logger.error(f"Error getting recent autopsy insights: {str(e)}")
        return None


def get_recent_journal_notes(user_id, days=3):
    """
    Get recent journal notes to provide context for recommendation generation.
    Notes may contain critical information about injury status, medical constraints,
    or reasons for deviating from prescriptions.
    """
    try:
        cutoff_date = (get_app_current_date() - timedelta(days=days)).strftime('%Y-%m-%d')

        recent_notes = execute_query(
            """
            SELECT date, notes, energy_level, rpe_score, pain_percentage
            FROM journal_entries
            WHERE user_id = %s AND date >= %s AND notes IS NOT NULL AND notes != ''
            ORDER BY date DESC
            LIMIT 5
            """,
            (user_id, cutoff_date),
            fetch=True
        )

        if not recent_notes:
            return None

        # Format notes for prompt inclusion
        formatted_notes = []
        for row in recent_notes:
            note_data = dict(row)
            date_str = note_data['date'].strftime('%Y-%m-%d') if hasattr(note_data['date'], 'strftime') else str(note_data['date'])
            notes_text = note_data['notes']
            energy = note_data.get('energy_level', '-')
            rpe = note_data.get('rpe_score', '-')
            pain = note_data.get('pain_percentage', '-')

            formatted_notes.append(f"  {date_str}: Energy {energy}/5, RPE {rpe}/10, Pain {pain}%\n  Notes: {notes_text}")

        return "\n\n".join(formatted_notes)

    except Exception as e:
        logger.error(f"Error getting recent journal notes: {str(e)}")
        return None


def generate_autopsy_informed_daily_decision(user_id, target_date=None, autopsy_insights=None):
    """
    Generate daily training decision that incorporates recent autopsy learning.
    This is the CORE INNOVATION - autopsy influences next decision.

    Args:
        user_id: The user ID
        target_date: Target date for recommendation (defaults to tomorrow)
        autopsy_insights: Optional pre-computed autopsy insights dict. If not provided,
                         will fetch recent autopsy insights automatically.

    Returns:
        dict with parsed sections: {
            'daily_recommendation': str,
            'weekly_recommendation': str,
            'pattern_insights': str,
            'raw_response': str
        }
        or None if generation fails
    """
    import re
    try:
        if target_date is None:
            # Use USER'S TIMEZONE for date calculation
            from timezone_utils import get_user_current_date
            target_date = get_user_current_date(user_id) + timedelta(days=1)  # Tomorrow
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        target_date_str = target_date.strftime('%Y-%m-%d')

        logger.info(f"Generating autopsy-informed decision for user {user_id}, target {target_date_str}")

        # Get current metrics
        current_metrics = get_current_metrics(user_id)
        if not current_metrics:
            logger.warning(f"No current metrics for autopsy-informed decision user {user_id}")
            return None

        # Use provided autopsy insights or fetch recent ones
        if autopsy_insights is None:
            autopsy_insights = get_recent_autopsy_insights(user_id, days=3)

        # Create enhanced prompt that includes autopsy learning
        prompt = create_autopsy_informed_decision_prompt(
            user_id,
            target_date_str,
            current_metrics,
            autopsy_insights
        )

        # Call LLM API
        response = call_anthropic_api(prompt)

        if response and response.strip():
            logger.info(f"Generated autopsy-informed decision for user {user_id}")

            # parse_llm_response handles process_markdown and structured_output extraction
            sections = parse_llm_response(response.strip())

            daily_rec = sections.get('daily_recommendation', '')

            # Fallback: if parser returned empty, use the raw response stripped of XML block
            if not daily_rec:
                daily_rec = re.sub(
                    r'<structured_output>.*?</structured_output>', '', response.strip(), flags=re.DOTALL
                ).strip()
                logger.warning("Parser returned empty daily_recommendation, using stripped raw response")

            logger.info(f"✅ Daily recommendation: {len(daily_rec)} chars")

            return {
                'daily_recommendation': daily_rec,
                'weekly_recommendation': '',
                'pattern_insights': '',
                'raw_response': response.strip(),
                'structured_output': sections.get('structured_output')
            }
        else:
            logger.warning("No response from autopsy-informed decision generation")
            return None

    except Exception as e:
        logger.error(f"Error generating autopsy-informed decision: {str(e)}")
        return None


def create_autopsy_prompt_with_coaching_style(date_str, prescribed_action, actual_activities,
                                              observations_text, current_metrics, training_guide, tone_instructions):
    """NEW FUNCTION: Create autopsy prompt with coaching style tone"""

    # Format activity data correctly (based on existing code patterns)
    if isinstance(actual_activities, dict):
        activity_type = actual_activities.get('type', 'unknown')
        distance = actual_activities.get('distance', 0)
        elevation = actual_activities.get('elevation', 0)
        trimp = actual_activities.get('total_trimp', 0)
        classification = actual_activities.get('workout_classification', 'unknown')
        activity_summary = f"{activity_type} - {distance} miles, {elevation}ft elevation, {trimp} TRIMP, {classification} intensity"
    else:
        activity_summary = str(actual_activities)

    prompt = f"""You are an expert endurance sports coach conducting a post-training analysis.

{tone_instructions}

DATE: {date_str}
PRESCRIBED: {prescribed_action}
ACTUAL: {activity_summary}
USER OBSERVATIONS: {observations_text}

CURRENT TRAINING METRICS:
- External ACWR: {current_metrics.get('external_acwr') or 0:.2f}
- Internal ACWR: {current_metrics.get('internal_acwr') or 0:.2f}
- Normalized Divergence: {format_divergence_for_prompt(current_metrics.get('normalized_divergence'))}
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}

### TRAINING REFERENCE FRAMEWORK
{training_guide}

DIVERGENCE SIGN CONVENTION: {NORMALIZED_DIVERGENCE_FORMULA}

### AUTOPSY ANALYSIS INSTRUCTIONS
Using the Training Reference Framework above and the specified tone approach, provide analysis in exactly three sections:

**ALIGNMENT ASSESSMENT:**
- Compare prescribed vs actual activities using the specified tone
- Reference specific Decision Framework criteria from the training guide
- Rate alignment on 1-10 scale with justification

**PHYSIOLOGICAL RESPONSE ANALYSIS:**
- Analyze energy/RPE/pain levels using the coaching style tone
- Compare expected vs actual response based on current metrics
- Reference optimal ranges and pattern recognition from the guide

**LEARNING INSIGHTS & TOMORROW'S IMPLICATIONS:**
- Provide insights using the specified coaching approach
- How should this influence tomorrow's training decision?
- Specific recommendations for ACWR management and recovery planning

CRITICAL REQUIREMENTS:
- Start with "ALIGNMENT_SCORE: X/10" where X is a number 1-10
- Keep total response under 300 words for Journal display
- Apply the specified coaching tone throughout the analysis
- Use evidence-based analysis referencing Training Reference Guide principles
"""

    return prompt


def create_autopsy_informed_decision_prompt(user_id, target_date_str, current_metrics, autopsy_insights):
    """Create daily decision prompt that learns from recent autopsy analyses.
    
    Enhanced version includes Training Reference Framework and Risk Tolerance personalization
    for evidence-based, consistent recommendations aligned with the comprehensive prompt.
    Also includes reference to Coach page weekly plan for consistency.
    """

    # Get user's risk tolerance and personalized thresholds
    recommendation_style = get_user_recommendation_style(user_id)
    thresholds = get_adjusted_thresholds(recommendation_style)
    
    # Load training guide for evidence-based recommendations
    training_guide = load_training_guide()
    if not training_guide:
        logger.warning("Training guide not available for autopsy-informed prompt")
        training_guide = "Apply evidence-based training principles focusing on ACWR management and recovery."

    # Get weekly program context from Coach page
    weekly_program_context = ""
    try:
        from llm_context_tools import get_weekly_program_day
        from datetime import datetime

        daily_plan = get_weekly_program_day(user_id, target_date_str)

        if daily_plan:
            target_date_obj = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            day_name = target_date_obj.strftime('%A')
            weekly_program_context = f"""
YOUR MONKEY'S WEEK PLAN FOR {target_date_str} ({day_name}):
- Planned Workout: {daily_plan.get('workout_type', 'N/A')}
- Description: {daily_plan.get('description', 'N/A')}
- Duration: {daily_plan.get('duration_estimate', 'N/A')}
- Intensity: {daily_plan.get('intensity', 'N/A')}
- Key Focus: {daily_plan.get('key_focus', 'N/A')}

CRITICAL: Your Daily Recommendation must be CONSISTENT with the week plan above.
When referencing the plan, choose naturally from: "your coach recommends", "your workplan for the week calls for", "your coach has mapped out", or "your weekly training plan calls for".
If current metrics suggest adjusting the plan (e.g., rest day due to high ACWR), explain the deviation clearly.
Otherwise, provide tactical execution guidance for the planned workout."""
        else:
            weekly_program_context = "\nNOTE: No weekly program available from Coach page. Provide standalone recommendation."

    except Exception as e:
        logger.warning(f"Could not fetch weekly program context: {str(e)}")
        weekly_program_context = "\nNOTE: Weekly program not accessible. Provide standalone recommendation."

    # Get recent journal notes for additional context (may contain injury/medical info)
    recent_notes = get_recent_journal_notes(user_id, days=3)
    notes_context = ""
    if recent_notes:
        notes_context = f"""
RECENT JOURNAL NOTES (Last 3 Days):
{recent_notes}

CRITICAL: If notes mention injury, pain, rehabilitation, medical issues, or reasons for
deviating from prescription, these override normal training progression logic.
"""

    # Athlete preference feedback from alignment query responses (last 30 days)
    preference_context = ""
    try:
        answered_queries = get_answered_alignment_queries(user_id, days=30)
        if answered_queries:
            lines = []
            for q in answered_queries:
                date_val = q.get('activity_date', '')
                date_str = date_val.strftime('%Y-%m-%d') if hasattr(date_val, 'strftime') else str(date_val)
                lines.append(f"  {date_str} (alignment {q.get('alignment_score', '?')}/10): {q['response']}")
            preference_context = f"""
ATHLETE PREFERENCE FEEDBACK (responses to off-plan queries):
{chr(10).join(lines)}

CRITICAL: These are the athlete's own words explaining why the prescription didn't fit
their reality. Treat repeated themes (terrain, environment, schedule constraints) as
HARD CONSTRAINTS — adjust future prescriptions to work within them, not against them.
"""
    except Exception as pref_err:
        logger.warning(f"Could not load preference feedback for user {user_id}: {pref_err}")

    autopsy_context = ""
    if autopsy_insights:
        alignment_trend = autopsy_insights.get('alignment_trend', [])
        trend_description = "improving" if len(alignment_trend) >= 2 and alignment_trend[-1] > alignment_trend[
            0] else "mixed"

        autopsy_context = f"""
RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses):
- Average Alignment Score: {autopsy_insights['avg_alignment']}/10
- Alignment Trend: {trend_description} ({alignment_trend})
- Key Learning: {autopsy_insights['latest_insights'] if autopsy_insights['latest_insights'] else 'No specific insights'}

AUTOPSY-INFORMED ADAPTATION (CRITICAL):
- The autopsy analysis above identifies the ROOT CAUSE of alignment mismatches
- If alignment <4: The autopsy contains SPECIFIC STRATEGY CHANGES needed - READ IT CAREFULLY
- Common root causes and correct coaching responses:
  * INJURY/PAIN mentioned in autopsy or notes → OVERRIDE ACWR logic, prescribe rehabilitation protocol
  * User notes indicate medical constraints → HONOR those constraints, do not push volume
  * Non-compliance pattern → Simplify guidance for better adherence
  * External constraints (time, access) → Adjust for athlete's reality
- DO NOT assume low alignment = simplification needed
- APPLY THE AUTOPSY'S SPECIFIC RECOMMENDATIONS, not generic defaults
- When injury/medical issues present: Current metrics (ACWR, divergence) are SECONDARY to safe recovery
"""
    else:
        autopsy_context = """
RECENT AUTOPSY LEARNING: No recent autopsy data available
COACHING STRATEGY: Standard evidence-based recommendation without learning context
"""
    # Extract day name safely before f-string
    target_date_obj = safe_datetime_parse(target_date_str)
    day_name = target_date_obj.strftime('%A')

    # Athlete model context (personalized thresholds + confidence)
    athlete_model_context = get_athlete_model_context(user_id)

    # Training stage from existing Coach page logic (DB call, not recomputed)
    training_stage_context = ""
    try:
        from coach_recommendations import get_current_training_stage
        stage_info = get_current_training_stage(user_id)
        training_stage_context = (
            f"TRAINING STAGE: {stage_info.get('stage', 'Unknown')}"
            + (f" | Weeks to {stage_info.get('race_name', 'race')}: {stage_info.get('weeks_to_race', 'N/A')}" if stage_info.get('race_name') else "")
            + (f" | {stage_info.get('details', '')}" if stage_info.get('details') else "")
        )
    except Exception as _e:
        logger.warning(f"Could not fetch training stage: {_e}")

    # Alignment K of N (raw counts — LLM interprets)
    alignment_kn_context = ""
    if autopsy_insights and autopsy_insights.get('alignment_trend'):
        scores = [s for s in autopsy_insights['alignment_trend'] if isinstance(s, (int, float))]
        if len(scores) >= 2:
            n = len(scores)
            k = sum(1 for s in scores if s >= 7)
            alignment_kn_context = f"ALIGNMENT: {k} of last {n} workouts scored ≥7 | avg {autopsy_insights.get('avg_alignment', 0):.1f}/10"

    prompt = f"""You are an expert endurance coach providing tomorrow's training decision with learning from recent autopsy analyses.

TARGET DATE: {target_date_str} ({day_name})

ATHLETE RISK TOLERANCE: {recommendation_style.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days
- Divergence Overtraining Risk: <{thresholds['divergence_overtraining']}

DIVERGENCE SIGN CONVENTION: {NORMALIZED_DIVERGENCE_FORMULA}

CURRENT METRICS:
- External ACWR: {current_metrics.get('external_acwr') or 0:.2f} (Optimal: 0.8-1.3)
- Internal ACWR: {current_metrics.get('internal_acwr') or 0:.2f} (Optimal: 0.8-1.3)
- Normalized Divergence: {format_divergence_for_prompt(current_metrics.get('normalized_divergence'))}
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}
- 7-day Avg Load: {current_metrics.get('seven_day_avg_load') or 0:.2f} miles/day

{training_stage_context}

{alignment_kn_context}

{athlete_model_context}

{weekly_program_context}

{notes_context}

{preference_context}

{autopsy_context}

### TRAINING REFERENCE FRAMEWORK
{training_guide}

INSTRUCTIONS:
Using the Training Reference Framework above, provide a complete training analysis with three sections that demonstrates learning from recent autopsy patterns.
Adapt your coaching approach based on the athlete's demonstrated preferences, adherence patterns, and risk tolerance.

CRITICAL DECISION HIERARCHY (APPLY IN THIS ORDER):
1. INJURY/MEDICAL STATUS (from autopsy or notes) - HIGHEST PRIORITY
   - If injury/pain/rehabilitation mentioned → Conservative protocol overrides all other metrics
   - Ignore ACWR optimization when injury present
2. ATHLETE PREFERENCE FEEDBACK (from off-plan query responses above)
   - If the athlete has explicitly stated a prescription element is incompatible with their
     environment or life, treat it as a HARD CONSTRAINT — same weight as a medical constraint
   - Examples: "I live in the mountains" → vert restrictions are not viable; prescribe for
     mountain terrain. "I can't avoid hills" → stop prescribing flat routes.
   - Repeated themes across multiple responses = persistent constraint, not a one-off.
3. AUTOPSY-SPECIFIC GUIDANCE (from Key Learning above)
   - Apply the exact strategy changes recommended in autopsy analysis
   - Don't assume low alignment = simplify; read what autopsy actually says
4. WEEKLY PLAN ADHERENCE — DEFAULT IS TO PROCEED AS PLANNED
   - The weekly plan is the default prescription. Positive divergence means more available capacity, not less — it is never a reason to reduce load. Deviate only when metrics breach a threshold, an injury is present, or the autopsy identifies a specific adaptation or scheduling adjustment.
5. CURRENT METRICS (ACWR, divergence, days since rest)
   - Only apply normal training progression if no injury/medical issues present
6. ATHLETE RISK TOLERANCE
   - Respect personalized thresholds, but medical safety always trumps risk tolerance

REQUIRED OUTPUT FORMAT:

IMPORTANT: Output ONLY two things — the DAILY RECOMMENDATION prose and the structured_output block. Do NOT include "WEEKLY PLANNING", "PATTERN INSIGHTS", or any other section headers. Responses that include those sections will have content truncated by the parser.

Begin your response with this header on its own line, then write the prescription immediately after:

DAILY RECOMMENDATION

Your prescription must be flowing prose (no bullets, no sub-headers, no numbered lines) and must be 200-230 words. You are not done until you have addressed all eight elements below. Do not stop after the workout description — the metrics, decision, and execution cues are mandatory.

Element 1 — PLAN (~30 words): State the planned workout (type, distance, terrain, vert). Use one of: "your coach recommends", "your workplan for the week calls for", "your coach has mapped out", "your weekly training plan calls for". If no plan exists, prescribe from metrics.
Element 2 — STAGE (~20 words): Name the training stage and what it means for today's effort quality.
Element 3 — ALIGNMENT (~20 words): Cite the K-of-N figure from ALIGNMENT data and what it says about recent execution.
Element 4 — METRICS (~45 words): Cite External ACWR, Internal ACWR, and Divergence values by number. Interpret each against the athlete's personal thresholds from ATHLETE MODEL — state where they sit in their productive training window.
Element 5 — CONFIDENCE (~20 words): State the model confidence % and autopsy count. Say what that means for trusting this prescription.
Element 6 — DECISION (~20 words): Write "Proceed as planned." or "Adjust: [specific change] because [one reason]."
Element 7 — EXECUTION (~45 words): Give 2-3 specific execution cues covering effort zone, pacing or HR target, terrain guidance, and duration.
Element 8 — INJURY (≤15 words, only if signals are present): One sentence on managing the injury this workout.

Plain text only — no markdown, no bold, no headers within the prose.

### STRUCTURED OUTPUT (required)
After the DAILY RECOMMENDATION section, append a machine-readable JSON block inside XML tags.

SIGN CONVENTION: {NORMALIZED_DIVERGENCE_FORMULA}

<structured_output>
{{
  "target_date": "{target_date_str}",
  "assessment": {{
    "primary_signal": "divergence",
    "category": "normal_progression",
    "confidence": 0.85,
    "primary_driver": "One concise sentence explaining the deciding factor"
  }},
  "divergence": {{
    "value": 0.0,
    "direction": "balanced",
    "severity": "none",
    "interpretation": "balanced"
  }},
  "decision": {{
    "action": "train",
    "intensity_target": "moderate",
    "volume_modifier": 0.0,
    "specific_workout_type": null,
    "duration_minutes_suggested": null
  }},
  "risk": {{
    "injury_risk_level": "low",
    "acwr_external": 0.0,
    "acwr_internal": 0.0,
    "divergence": 0.0,
    "days_since_rest": 0,
    "flags": [],
    "pain_location": null
  }},
  "context": {{
    "autopsy_informed": true,
    "alignment_trend": "insufficient_data",
    "training_stage": null,
    "weeks_to_a_race": null
  }},
  "meta": {{
    "model_used": "claude-haiku-4-5-20251001",
    "generation_timestamp": "ISO8601",
    "coaching_spectrum": 50,
    "risk_tolerance": "{recommendation_style}",
    "tokens_used": {{"input": 0, "output": 0}}
  }}
}}
</structured_output>

Allowed values — assessment.category: normal_progression | mandatory_rest | overtraining_risk | divergence_warning | detraining_signal | recovery_needed | undertraining_opportunity. divergence.direction: positive | negative | balanced. divergence.severity: none | mild | moderate | high | critical. divergence.interpretation: overtraining_risk | detraining | balanced | insufficient_data. decision.action: train | rest | cross_train | reduce. risk.injury_risk_level: low | moderate | high | critical. risk.pain_location: specific body part extracted from athlete notes (e.g., "left knee", "right achilles") or null if no pain mentioned.
"""

    return prompt


def update_recommendations_with_autopsy_learning(user_id, journal_date):
    """
    Complete workflow function that coordinates autopsy generation and decision updates.
    This function should be called from strava_app.py after journal save.
    """
    try:
        app_current_date = get_app_current_date()
        journal_date_obj = safe_date_parse(journal_date)

        logger.info(f"Starting autopsy learning workflow for user {user_id}, date {journal_date}")

        # STEP 1: Generate enhanced autopsy for completed training (if past date or today)
        # Allow today's date to generate autopsy and tomorrow's recommendation
        if journal_date_obj <= app_current_date:
            logger.info(f"Generating enhanced autopsy for past date: {journal_date}")

            # Get required data for autopsy
            from strava_app import get_todays_decision_for_date, get_activity_summary_for_date

            prescribed_action = get_todays_decision_for_date(journal_date_obj, user_id)
            activity_summary = get_activity_summary_for_date(journal_date_obj, user_id)

            # Get user observations
            journal_entry = execute_query(
                "SELECT * FROM journal_entries WHERE user_id = %s AND date = %s",
                (user_id, journal_date),
                fetch=True
            )

            if journal_entry and journal_entry[0]:
                observations = dict(journal_entry[0])

                # Check if autopsy already exists (may have been generated in save_journal_entry)
                existing_autopsy = execute_query(
                    "SELECT alignment_score, autopsy_analysis FROM ai_autopsies WHERE user_id = %s AND date = %s",
                    (user_id, journal_date),
                    fetch=True
                )
                
                if existing_autopsy and existing_autopsy[0]:
                    # Use existing autopsy
                    autopsy_result = {
                        'analysis': existing_autopsy[0].get('autopsy_analysis', ''),
                        'alignment_score': existing_autopsy[0].get('alignment_score', 5)
                    }
                    logger.info(f"Using existing autopsy for {journal_date}, alignment: {autopsy_result['alignment_score']}/10")
                else:
                    # Format activity summary as string for autopsy generation
                    if isinstance(activity_summary, dict):
                        actual_activities = f"{activity_summary.get('type', 'Activity').title()} workout: {activity_summary.get('distance', 0)} miles, {activity_summary.get('elevation', 0)} ft elevation, TRIMP: {activity_summary.get('total_trimp', 0)} ({activity_summary.get('workout_classification', 'Unknown')} intensity)"
                    else:
                        actual_activities = str(activity_summary)
                    
                    # Generate enhanced autopsy
                    autopsy_result = generate_activity_autopsy_enhanced(
                        user_id,
                        journal_date,
                        prescribed_action,
                        actual_activities,
                        observations
                    )

                if autopsy_result:
                    # Only save autopsy if it was newly generated (not using existing one)
                    if not (existing_autopsy and existing_autopsy[0]):
                        # Save enhanced autopsy to database
                        execute_query(
                            """
                            INSERT INTO ai_autopsies (user_id, date, prescribed_action, actual_activities, 
                                                    autopsy_analysis, alignment_score, generated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (user_id, date)
                            DO UPDATE SET
                                prescribed_action = EXCLUDED.prescribed_action,
                                actual_activities = EXCLUDED.actual_activities,
                                autopsy_analysis = EXCLUDED.autopsy_analysis,
                                alignment_score = EXCLUDED.alignment_score,
                                generated_at = NOW()
                            """,
                            (
                                user_id,
                                journal_date,
                                prescribed_action[:500] if prescribed_action else '',  # Truncate for storage
                                json.dumps(activity_summary) if isinstance(activity_summary, dict) else str(
                                    activity_summary),
                                autopsy_result['analysis'],
                                autopsy_result['alignment_score']
                            )
                        )
                        logger.info(
                            f"Saved enhanced autopsy for {journal_date}, alignment: {autopsy_result['alignment_score']}/10")
                    else:
                        logger.info(
                            f"Using existing autopsy for {journal_date}, alignment: {autopsy_result['alignment_score']}/10")

                    # STEP 2: Generate new decision for the next needed date with autopsy learning
                    # CRITICAL: Prioritize updating today's preliminary recommendation over generating tomorrow's
                    from timezone_utils import get_user_current_date
                    user_current_date = get_user_current_date(user_id)
                    
                    # CRITICAL: Check if today's recommendation needs updating with LATEST autopsy
                    # Even if marked as autopsy-informed, it might be from an OLD autopsy
                    # We need to check if there's a NEWER autopsy than the recommendation
                    check_today = execute_query(
                        """SELECT target_date, is_autopsy_informed, generated_at 
                           FROM llm_recommendations 
                           WHERE user_id = %s AND target_date = %s""",
                        (user_id, user_current_date.strftime('%Y-%m-%d')),
                        fetch=True
                    )
                    
                    if not check_today or len(check_today) == 0:
                        # No recommendation for user's today - generate for today
                        next_date = user_current_date
                        logger.info(f"📅 No recommendation found for user's today ({user_current_date}), generating autopsy-informed recommendation")
                    else:
                        # Have a recommendation - but is it based on the LATEST autopsy?
                        recommendation_time = check_today[0].get('generated_at')
                        yesterday = user_current_date - timedelta(days=1)
                        
                        # Check if yesterday's autopsy is NEWER than today's recommendation
                        autopsy_time = execute_query(
                            """SELECT generated_at FROM ai_autopsies 
                               WHERE user_id = %s AND date = %s""",
                            (user_id, yesterday.strftime('%Y-%m-%d')),
                            fetch=True
                        )
                        
                        if autopsy_time and autopsy_time[0]:
                            autopsy_generated_at = autopsy_time[0].get('generated_at')
                            
                            if autopsy_generated_at > recommendation_time:
                                # Autopsy is NEWER than recommendation - regenerate!
                                next_date = user_current_date
                                logger.info(f"🔄 Today's recommendation exists (from {recommendation_time})")
                                logger.info(f"🔄 But yesterday's autopsy is NEWER (from {autopsy_generated_at})")
                                logger.info(f"🔄 REGENERATING today's ({user_current_date}) recommendation with latest autopsy insights")
                            else:
                                # Recommendation is already based on latest autopsy.
                                # Generate for journal_date + 1, not user_current_date + 1.
                                # Using user_current_date + 1 would pre-generate a rec for a future
                                # date (e.g. Wednesday) when processing a past journal entry (Monday),
                                # before the intermediate day (Tuesday) has even been logged.
                                next_date = journal_date_obj + timedelta(days=1)
                                logger.info(f"✅ Today's recommendation ({recommendation_time}) already includes latest autopsy ({autopsy_generated_at})")
                                logger.info(f"✅ Generating for {next_date} (journal_date + 1)")
                        else:
                            # No autopsy for yesterday - generate for journal_date + 1
                            next_date = journal_date_obj + timedelta(days=1)
                            logger.info(f"✅ No new autopsy for yesterday, generating for {next_date} (journal_date + 1)")
                    
                    next_date_str = next_date.strftime('%Y-%m-%d')
                    tomorrow_str = next_date_str  # For backward compatibility with existing code
                    
                    # Generate new autopsy-informed decision (returns pre-parsed dict)
                    decision = generate_autopsy_informed_daily_decision(user_id, next_date)

                    if decision:
                        # Get current metrics for snapshot
                        from unified_metrics_service import UnifiedMetricsService
                        current_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id) or {}

                        # Check if recommendation already exists
                        existing_rec = execute_query(
                            """
                            SELECT id FROM llm_recommendations 
                            WHERE user_id = %s AND target_date = %s
                            """,
                            (user_id, tomorrow_str),
                            fetch=True
                        )

                        if existing_rec:
                            # UPDATE existing recommendation with pre-parsed sections
                            logger.info(f"Updating existing recommendation for {tomorrow_str} with autopsy learning")
                            execute_query(
                                """
                                UPDATE llm_recommendations
                                SET daily_recommendation = %s,
                                    weekly_recommendation = %s,
                                    pattern_insights = %s,
                                    raw_response = %s,
                                    generated_at = NOW(),
                                    is_autopsy_informed = TRUE,
                                    autopsy_count = %s,
                                    avg_alignment_score = %s
                                WHERE user_id = %s AND target_date = %s
                                """,
                                (
                                    decision['daily_recommendation'],
                                    decision['weekly_recommendation'] or "Updated with autopsy learning",
                                    decision['pattern_insights'] or f"Alignment: {autopsy_result['alignment_score']}/10",
                                    decision['raw_response'],
                                    1,  # autopsy_count
                                    autopsy_result['alignment_score'],
                                    user_id,
                                    tomorrow_str
                                )
                            )
                            logger.info(f"Updated recommendation for {tomorrow_str} with autopsy-informed decision")
                        else:
                            # INSERT new recommendation with pre-parsed sections
                            recommendation_data = {
                                'generation_date': app_current_date.strftime('%Y-%m-%d'),
                                'target_date': next_date_str,
                                'valid_until': None,
                                'data_start_date': app_current_date.strftime('%Y-%m-%d'),
                                'data_end_date': app_current_date.strftime('%Y-%m-%d'),
                                'metrics_snapshot': current_metrics,
                                'daily_recommendation': decision['daily_recommendation'],
                                'weekly_recommendation': decision['weekly_recommendation'] or 'See previous weekly guidance',
                                'pattern_insights': decision['pattern_insights'] or f"Alignment: {autopsy_result['alignment_score']}/10",
                                'raw_response': decision['raw_response'],
                                'user_id': user_id,
                                'is_autopsy_informed': True,
                                'autopsy_count': 1,
                                'avg_alignment_score': autopsy_result['alignment_score']
                            }

                            recommendation_data = fix_dates_for_json(recommendation_data)
                            save_llm_recommendation(recommendation_data)
                            logger.info(f"Generated new decision for {next_date_str} incorporating autopsy learning")

                        return {
                            'autopsy_generated': True,
                            'alignment_score': autopsy_result['alignment_score'],
                            'decision_updated': True,
                            'next_recommendation_date': next_date_str
                        }

        return {
            'autopsy_generated': False,
            'decision_updated': False,
            'reason': 'Future date or missing data'
        }

    except Exception as e:
        logger.error(f"Error in autopsy learning workflow: {str(e)}")
        return {
            'autopsy_generated': False,
            'decision_updated': False,
            'error': str(e)
        }

def process_markdown(text):
    """Convert markdown formatting to clean plain text."""
    import re

    if not text:
        return text

    # Remove markdown bold formatting
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold** -> bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # *italic* -> italic

    # Remove markdown headers but keep the text
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # Remove # headers

    # Remove markdown links
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # [text](url) -> text

    # Remove markdown list markers
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)

    # Remove markdown code formatting
    text = re.sub(r'`([^`]+)`', r'\1', text)  # `code` -> code

    # Remove markdown table rows (lines containing | ... | syntax)
    text = re.sub(r'^\s*\|.*\|\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\|[-| :]+\|\s*$', '', text, flags=re.MULTILINE)

    # Remove horizontal rules (--- or ***)
    text = re.sub(r'^\s*[-*]{2,}\s*$', '', text, flags=re.MULTILINE)

    # Remove emojis and unicode symbols
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"   # emoticons
        "\U0001F300-\U0001F5FF"    # symbols & pictographs
        "\U0001F680-\U0001F6FF"    # transport & map
        "\U0001F700-\U0001F77F"    # alchemical symbols
        "\U0001F780-\U0001F7FF"    # geometric shapes
        "\U0001F800-\U0001F8FF"    # supplemental arrows
        "\U0001F900-\U0001F9FF"    # supplemental symbols
        "\U0001FA00-\U0001FA6F"    # chess symbols
        "\U0001FA70-\U0001FAFF"    # symbols and pictographs extended
        "\U00002702-\U000027B0"    # dingbats
        "\U000024C2-\U0001F251"    # enclosed characters
        "\U00002600-\U000026FF"    # misc symbols (includes ☑ ⚠ etc.)
        "\U00002700-\U000027BF"    # dingbats
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)

    # Clean up excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Collapse triple+ blank lines
    text = re.sub(r'\n\s*\n', '\n\n', text)        # Normalize double blank lines
    text = re.sub(r'[ \t]+', ' ', text)             # Normalize spaces (preserve newlines)
    text = text.strip()

    return text


# =============================================================================
# PHASE 4 — AGENTIC CONTEXT ASSEMBLY
# =============================================================================
# generate_recommendations_agentic() is a PARALLEL PATH alongside the existing
# generate_recommendations().  The existing function is UNCHANGED.
# =============================================================================

def call_claude_with_tools(messages, tools, model=None, temperature=None, max_tokens=3000):
    """Call Claude using the Anthropic SDK with tool support.

    Args:
        messages: List of message dicts in Anthropic format.
        tools: List of Anthropic tool definition dicts (TOOL_DEFINITIONS from
               llm_context_tools).
        model: Claude model override (defaults to MODEL_SONNET for agentic path).
        temperature: Sampling temperature (defaults to RECOMMENDATION_TEMPERATURE).
        max_tokens: Maximum tokens to generate.

    Returns:
        The Anthropic Message object (not just the text) so callers can inspect
        stop_reason, content blocks, and usage.
    """
    if model is None:
        model = MODEL_SONNET
    if temperature is None:
        temperature = RECOMMENDATION_TEMPERATURE

    import anthropic as anthropic_sdk
    api_key = get_api_key()
    client = anthropic_sdk.Anthropic(api_key=api_key)

    logger.info(
        f"call_claude_with_tools: model={model}, max_tokens={max_tokens}, "
        f"temperature={temperature}, messages={len(messages)}, tools={len(tools)}"
    )

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tools=tools,
        messages=messages,
    )

    logger.info(
        f"call_claude_with_tools: stop_reason={message.stop_reason}, "
        f"input_tokens={message.usage.input_tokens}, "
        f"output_tokens={message.usage.output_tokens}"
    )
    return message


def execute_tool_call(user_id, tool_name, tool_input):
    """Dispatch a tool call to the appropriate function in llm_context_tools.

    Args:
        user_id: The user ID to pass to every tool.
        tool_name: Name of the tool as returned by the model.
        tool_input: Dict of arguments the model provided.

    Returns:
        JSON-serialisable result (list or dict).
    """
    from llm_context_tools import (
        get_activities,
        get_race_goals,
        get_weekly_program_day,
        get_journal_entries,
        get_athlete_model_tool,
    )

    logger.info(f"execute_tool_call: tool={tool_name}, user={user_id}, input={tool_input}")

    if tool_name == "get_activities":
        return get_activities(user_id=user_id, days=tool_input["days"])

    if tool_name == "get_race_goals":
        return get_race_goals(user_id=user_id)

    if tool_name == "get_weekly_program_day":
        return get_weekly_program_day(user_id=user_id, target_date=tool_input["target_date"])

    if tool_name == "get_journal_entries":
        return get_journal_entries(user_id=user_id, days=tool_input["days"])

    if tool_name == "get_athlete_model":
        return get_athlete_model_tool(user_id=user_id)

    raise ValueError(f"Unknown tool: {tool_name!r}")


def generate_recommendations_agentic(user_id, target_date=None, force=False):
    """Generate training recommendations using the two-turn agentic pattern.

    Phase 4 — Agentic Context Assembly.

    Turn 1: Send minimal context (current metrics + tool list) → model responds
            with tool_use blocks requesting the data it needs.
    Turn 2: Execute the requested tools, send results back → model generates the
            full recommendation.

    The function returns the SAME dict structure as generate_recommendations()
    so callers can treat both paths identically.

    Args:
        user_id: Required — user ID.
        target_date: Optional YYYY-MM-DD string.  Derived from current date /
                     activity status if not provided.

    Returns:
        Recommendation dict (same structure as generate_recommendations()) or None.
    """
    if user_id is None:
        raise ValueError("user_id is required for generate_recommendations_agentic")

    from llm_context_tools import TOOL_DEFINITIONS

    try:
        logger.info(f"[AGENTIC] Starting agentic recommendation generation for user {user_id}")

        # ------------------------------------------------------------------ #
        # Determine target_date (same logic as generate_recommendations)      #
        # ------------------------------------------------------------------ #
        from timezone_utils import get_user_current_date
        current_date = get_user_current_date(user_id)
        current_date_str = current_date.strftime('%Y-%m-%d')

        if target_date is None:
            has_activity_today = check_activity_for_date(user_id, current_date_str)
            has_journal_today = check_journal_for_date(user_id, current_date_str)
            if has_activity_today and has_journal_today:
                target_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                logger.info(f"[AGENTIC] Has activity + journal today → targeting tomorrow: {target_date}")
            else:
                target_date = current_date_str
                logger.info(f"[AGENTIC] Targeting today: {target_date} (has_activity={has_activity_today}, has_journal={has_journal_today})")

        # Guard: if a recommendation already exists for this target_date, return it
        # without regenerating. This mirrors the guard in generate_recommendations()
        # and prevents today's prescription from being overwritten with context from
        # journal notes that were saved AFTER the activity — which would create a
        # temporally-confused "prescribed action" for the autopsy generator.
        existing_rec = execute_query(
            "SELECT id FROM llm_recommendations WHERE user_id = %s AND target_date = %s",
            (user_id, target_date),
            fetch=True
        )
        if existing_rec and not force:
            logger.info(
                f"[AGENTIC] Recommendation already exists for target_date {target_date}, "
                f"skipping generation to preserve historical record"
            )
            result = execute_query(
                "SELECT * FROM llm_recommendations WHERE user_id = %s AND target_date = %s ORDER BY generated_at DESC LIMIT 1",
                (user_id, target_date),
                fetch=True
            )
            return dict(result[0]) if result and result[0] else get_latest_recommendation(user_id)
        elif existing_rec and force:
            logger.info(f"[AGENTIC] Force-regenerating recommendation for target_date {target_date}")

        # ------------------------------------------------------------------ #
        # Get current metrics (minimal context for Turn 1)                    #
        # ------------------------------------------------------------------ #
        current_metrics = get_current_metrics(user_id)
        if not current_metrics:
            logger.warning(f"[AGENTIC] No current metrics for user {user_id}, aborting")
            return None

        ext_acwr = current_metrics.get('external_acwr', 0) or 0
        int_acwr = current_metrics.get('internal_acwr', 0) or 0
        divergence = current_metrics.get('normalized_divergence', 0) or 0
        days_rest = current_metrics.get('days_since_rest', 0) or 0

        # ------------------------------------------------------------------ #
        # Fetch tone instructions so the agentic path matches standard path   #
        # ------------------------------------------------------------------ #
        try:
            spectrum_value = get_user_coaching_spectrum(user_id)
            tone_instructions = get_coaching_tone_instructions(spectrum_value)
        except Exception as tone_err:
            logger.warning(f"[AGENTIC] Could not fetch tone instructions for user {user_id}: {tone_err}")
            tone_instructions = ""

        # ------------------------------------------------------------------ #
        # Fetch static context not available as tools (4-C parity fix)       #
        # morning readiness, training guide, weekly strategic context         #
        # ------------------------------------------------------------------ #
        static_context_parts = []

        # Morning readiness — same query as standard path
        try:
            readiness_data = execute_query(
                """SELECT sleep_quality, morning_soreness, hrv_value, resting_hr,
                          sleep_duration_secs, sleep_score, weight, spo2, respiration_rate
                   FROM journal_entries WHERE user_id = %s AND date = %s""",
                (user_id, target_date),
                fetch=True
            )
            hrv_baseline_data = execute_query(
                """SELECT AVG(hrv_value) AS hrv_baseline, COUNT(hrv_value) AS hrv_count
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= %s::date - INTERVAL '30 days'
                     AND date < %s::date
                     AND hrv_value IS NOT NULL""",
                (user_id, target_date, target_date),
                fetch=True
            )
            rhr_baseline_data = execute_query(
                """SELECT AVG(resting_hr) AS rhr_baseline, COUNT(resting_hr) AS rhr_count
                   FROM journal_entries
                   WHERE user_id = %s
                     AND date >= %s::date - INTERVAL '7 days'
                     AND date < %s::date
                     AND resting_hr IS NOT NULL""",
                (user_id, target_date, target_date),
                fetch=True
            )
            if readiness_data and readiness_data[0]:
                row = dict(readiness_data[0])
                sq               = row.get('sleep_quality')
                ms               = row.get('morning_soreness')
                hrv_value        = row.get('hrv_value')
                rhr_value        = row.get('resting_hr')
                sleep_secs       = row.get('sleep_duration_secs')
                sleep_score      = row.get('sleep_score')
                weight           = row.get('weight')
                spo2             = row.get('spo2')
                respiration_rate = row.get('respiration_rate')
                r_parts          = []

                if sleep_secs is not None:
                    hours = float(sleep_secs) / 3600
                    if hours < 6:
                        sleep_status = "significant deficit"
                    elif hours < 7:
                        sleep_status = "suboptimal"
                    else:
                        sleep_status = "adequate"
                    score_str = f", score: {sleep_score}/100" if sleep_score is not None else ""
                    r_parts.append(f"Sleep: {hours:.1f}hrs ({sleep_status}{score_str})")
                elif sq is not None:
                    sleep_labels = {1: "very poor", 2: "poor", 3: "fair", 4: "good", 5: "excellent"}
                    r_parts.append(f"Sleep quality: {sq}/5 ({sleep_labels.get(sq, 'unknown')})")
                if ms is not None:
                    r_parts.append(f"Morning soreness: {ms}/100")

                if hrv_value is not None:
                    hrv_baseline = hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data and hrv_baseline_data[0] else None
                    hrv_count    = hrv_baseline_data[0]['hrv_count']    if hrv_baseline_data and hrv_baseline_data[0] else 0
                    if hrv_baseline and hrv_count >= 7:
                        ratio     = float(hrv_value) / float(hrv_baseline)
                        pct_diff  = (ratio - 1.0) * 100
                        direction = "suppressed" if ratio < 0.85 else ("elevated" if ratio > 1.15 else "normal range")
                        r_parts.append(
                            f"HRV: {hrv_value:.0f}ms "
                            f"(30-day baseline: {hrv_baseline:.0f}ms, "
                            f"{abs(pct_diff):.0f}% {'below' if pct_diff < 0 else 'above'} baseline — {direction})"
                        )
                    else:
                        readings_needed = max(0, 7 - (hrv_count or 0))
                        r_parts.append(f"HRV: {hrv_value:.0f}ms (building baseline — {readings_needed} more readings needed)")

                if rhr_value is not None:
                    rhr_baseline = rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data and rhr_baseline_data[0] else None
                    rhr_count    = rhr_baseline_data[0]['rhr_count']    if rhr_baseline_data and rhr_baseline_data[0] else 0
                    if rhr_baseline and rhr_count >= 3:
                        rhr_diff = rhr_value - float(rhr_baseline)
                        pct_diff = (rhr_diff / float(rhr_baseline)) * 100
                        if pct_diff >= 10:
                            status = "significantly elevated"
                        elif pct_diff >= 5:
                            status = "elevated"
                        elif pct_diff <= -5:
                            status = "below baseline"
                        else:
                            status = "normal range"
                        r_parts.append(
                            f"Resting HR: {rhr_value}bpm "
                            f"(7-day baseline: {rhr_baseline:.0f}bpm, "
                            f"{abs(pct_diff):.0f}% {'above' if rhr_diff > 0 else 'below'} baseline — {status})"
                        )
                    else:
                        r_parts.append(f"Resting HR: {rhr_value}bpm (building baseline)")

                if weight is not None:
                    weight_baseline_data = execute_query(
                        """SELECT AVG(weight) AS weight_avg FROM journal_entries
                           WHERE user_id = %s AND date >= %s::date - INTERVAL '7 days'
                             AND date < %s::date AND weight IS NOT NULL""",
                        (user_id, target_date, target_date), fetch=True
                    )
                    weight_avg = weight_baseline_data[0]['weight_avg'] if weight_baseline_data and weight_baseline_data[0] else None
                    if weight_avg:
                        delta = float(weight) - float(weight_avg)
                        pct   = (delta / float(weight_avg)) * 100
                        note  = " — possible dehydration, monitor" if pct <= -2 else (" — above 7-day avg" if pct >= 2 else "")
                        r_parts.append(f"Weight: {weight:.1f}kg (7-day avg: {float(weight_avg):.1f}kg, {delta:+.1f}kg{note})")
                    else:
                        r_parts.append(f"Weight: {weight:.1f}kg")

                if spo2 is not None and float(spo2) < 95:
                    r_parts.append(f"SpO2: {spo2:.0f}% — low, possible altitude effect or illness")

                if respiration_rate is not None:
                    resp_baseline_data = execute_query(
                        """SELECT AVG(respiration_rate) AS resp_avg FROM journal_entries
                           WHERE user_id = %s AND date >= %s::date - INTERVAL '7 days'
                             AND date < %s::date AND respiration_rate IS NOT NULL""",
                        (user_id, target_date, target_date), fetch=True
                    )
                    resp_avg = resp_baseline_data[0]['resp_avg'] if resp_baseline_data and resp_baseline_data[0] else None
                    if resp_avg and float(respiration_rate) > float(resp_avg) * 1.15:
                        r_parts.append(
                            f"Respiration: {respiration_rate:.0f} breaths/min "
                            f"(7-day avg: {float(resp_avg):.0f} — elevated, possible illness or stress)"
                        )

                if r_parts:
                    _athlete_model_raw = get_athlete_model(user_id)
                    _rs = compute_readiness_state(
                        readiness_row=row,
                        hrv_baseline=hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data and hrv_baseline_data[0] else None,
                        hrv_baseline_count=hrv_baseline_data[0]['hrv_count'] if hrv_baseline_data and hrv_baseline_data[0] else 0,
                        rhr_baseline=rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data and rhr_baseline_data[0] else None,
                        rhr_baseline_count=rhr_baseline_data[0]['rhr_count'] if rhr_baseline_data and rhr_baseline_data[0] else 0,
                        athlete_model=_athlete_model_raw,
                    )
                    static_context_parts.append(
                        "### MORNING READINESS\n" +
                        "\n".join(f"- {p}" for p in r_parts) +
                        f"\n**READINESS STATE: {_rs['state']}** — {_rs['narrative']}"
                    )
                elif hrv_baseline_data or rhr_baseline_data:
                    # No wellness fields today but baselines exist — compute low-confidence state
                    _athlete_model_raw = get_athlete_model(user_id)
                    _rs = compute_readiness_state(
                        readiness_row={},
                        hrv_baseline=hrv_baseline_data[0]['hrv_baseline'] if hrv_baseline_data and hrv_baseline_data[0] else None,
                        hrv_baseline_count=hrv_baseline_data[0]['hrv_count'] if hrv_baseline_data and hrv_baseline_data[0] else 0,
                        rhr_baseline=rhr_baseline_data[0]['rhr_baseline'] if rhr_baseline_data and rhr_baseline_data[0] else None,
                        rhr_baseline_count=rhr_baseline_data[0]['rhr_count'] if rhr_baseline_data and rhr_baseline_data[0] else 0,
                        athlete_model=_athlete_model_raw,
                    )
                    static_context_parts.append(
                        f"### MORNING READINESS\n**READINESS STATE: {_rs['state']}** — {_rs['narrative']}"
                    )
        except Exception as readiness_err:
            logger.warning(f"[AGENTIC] Could not fetch morning readiness for user {user_id}: {readiness_err}")

        # Weekly strategic context — not available via get_weekly_program_day tool
        try:
            week_ctx = get_current_week_context(user_id)
            if week_ctx:
                summary = week_ctx.get('strategic_summary') or {}
                stage = summary.get('training_stage', 'unknown')
                intensity = summary.get('weekly_intensity_target', 'unknown')
                load_low = summary.get('load_target_low', 'N/A')
                load_high = summary.get('load_target_high', 'N/A')
                strategic_notes = summary.get('strategic_notes', '')
                deviation_log = week_ctx.get('deviation_log') or []
                revision_pending = week_ctx.get('revision_pending') or False
                wk_lines = [
                    f"Training stage: {stage} | Intensity target: {intensity} | Load range: {load_low}–{load_high} ACWR",
                    f"This week's deviations: {len(deviation_log)}",
                ]
                if revision_pending:
                    wk_lines.append("Plan revision pending — a mid-week adjustment has been proposed.")
                if strategic_notes:
                    wk_lines.append(f"Strategic notes: {strategic_notes}")
                static_context_parts.append(
                    "### WEEKLY STRATEGIC CONTEXT\n" + "\n".join(wk_lines)
                )
        except Exception as wk_err:
            logger.warning(f"[AGENTIC] Could not fetch weekly context for user {user_id}: {wk_err}")

        # Filtered training guide — critical for framework-grounded recommendations
        try:
            training_guide = load_training_guide()
            if training_guide:
                ext_acwr_val = current_metrics.get('external_acwr', 0) or 0
                int_acwr_val = current_metrics.get('internal_acwr', 0) or 0
                div_val = current_metrics.get('normalized_divergence', 0) or 0
                days_rest_val = current_metrics.get('days_since_rest', 0) or 0
                # Derive assessment category using same logic as standard path
                thresholds_agentic = get_adjusted_thresholds(get_user_recommendation_style(user_id))
                thresholds_agentic = apply_athlete_model_to_thresholds(thresholds_agentic, user_id)
                if days_rest_val > thresholds_agentic['days_since_rest_max']:
                    agentic_category = "mandatory_rest"
                elif div_val < thresholds_agentic['divergence_overtraining']:
                    agentic_category = "overtraining_risk"
                elif ext_acwr_val > thresholds_agentic['acwr_high_risk'] and int_acwr_val > thresholds_agentic['acwr_high_risk']:
                    agentic_category = "high_acwr_risk"
                else:
                    agentic_category = "normal_progression"
                filtered = _select_guide_sections(training_guide, agentic_category)
                static_context_parts.append("### TRAINING REFERENCE FRAMEWORK\n" + filtered)
        except Exception as guide_err:
            logger.warning(f"[AGENTIC] Could not load training guide for user {user_id}: {guide_err}")

        static_context_block = "\n\n".join(static_context_parts)

        # ------------------------------------------------------------------ #
        # Turn 1 — minimal prompt with metrics + tool list                    #
        # ------------------------------------------------------------------ #
        system_turn1 = (
            "You are an expert endurance sports coach with deep knowledge of "
            "training load science (ACWR, TRIMP, divergence). "
            "You have access to tools that can retrieve specific athlete data. "
            "Request ONLY the data you need to generate a high-quality daily "
            "training recommendation. Do not request redundant data.\n\n"
            "WEEKLY PLAN ADHERENCE — DEFAULT IS TO PROCEED AS PLANNED: "
            "The Coach page weekly plan is the primary prescription. "
            "VALID reasons to deviate: ACWR exceeds athlete's high-risk threshold, "
            "OR divergence is NEGATIVE beyond the athlete's personal breakdown threshold, "
            "OR active injury. "
            "INVALID reasons to deviate: positive divergence (means MORE available capacity — "
            "never a reason to downgrade intensity), terrain-elevated TRIMP from prior day, "
            "starting energy 3/5 or higher, or generic 'fatigue carryover' without a threshold breach. "
            "If no threshold is breached, Decision MUST be 'Proceed as planned.'"
            + (f"\n\n{tone_instructions}" if tone_instructions else "")
            + (f"\n\n{static_context_block}" if static_context_block else "")
        )

        user_turn1 = (
            f"Generate a daily training recommendation for {target_date}.\n\n"
            f"Current metrics snapshot:\n"
            f"- External ACWR: {ext_acwr:.2f}\n"
            f"- Internal ACWR (TRIMP): {int_acwr:.2f}\n"
            f"- Normalized Divergence: {divergence:.3f}\n"
            f"- Days Since Rest: {days_rest}\n\n"
            f"Use the available tools to retrieve any additional context you "
            f"need, then generate the recommendation in the standard three-section "
            f"format:\n"
            f"DAILY RECOMMENDATION: [your recommendation]\n"
            f"WEEKLY PLANNING: [weekly context]\n"
            f"PATTERN INSIGHTS: [pattern analysis]\n\n"
            f"Request the tools you need now."
        )

        messages = [
            {"role": "user", "content": user_turn1}
        ]

        logger.info(f"[AGENTIC] Turn 1: sending minimal context to model")
        turn1_response = call_claude_with_tools(
            messages=messages,
            tools=TOOL_DEFINITIONS,
            max_tokens=3000,
        )

        total_input_tokens = turn1_response.usage.input_tokens
        total_output_tokens = turn1_response.usage.output_tokens

        # ------------------------------------------------------------------ #
        # Turn 2 — execute tool calls, send results back                      #
        # ------------------------------------------------------------------ #
        if turn1_response.stop_reason == "tool_use":
            logger.info(f"[AGENTIC] Turn 1 stop_reason=tool_use — executing tool calls")

            # Build tool results
            tool_results = []
            for block in turn1_response.content:
                if block.type != "tool_use":
                    continue

                tool_name = block.name
                tool_input_data = block.input
                tool_use_id = block.id

                try:
                    result = execute_tool_call(user_id, tool_name, tool_input_data)
                    result_content = json.dumps(result)
                    logger.info(
                        f"[AGENTIC] Tool {tool_name!r} executed OK, "
                        f"result length={len(result_content)}"
                    )
                except Exception as tool_err:
                    result_content = json.dumps({"error": str(tool_err)})
                    logger.warning(
                        f"[AGENTIC] Tool {tool_name!r} failed: {tool_err}"
                    )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": result_content,
                })

            # Append Turn 1 assistant message + tool results to conversation
            messages.append({"role": "assistant", "content": turn1_response.content})
            messages.append({"role": "user", "content": tool_results})

            logger.info(f"[AGENTIC] Turn 2: sending tool results ({len(tool_results)} results)")
            turn2_response = call_claude_with_tools(
                messages=messages,
                tools=TOOL_DEFINITIONS,
                max_tokens=3000,
            )

            total_input_tokens += turn2_response.usage.input_tokens
            total_output_tokens += turn2_response.usage.output_tokens

            # Extract text from Turn 2
            llm_response = ""
            for block in turn2_response.content:
                if hasattr(block, 'text'):
                    llm_response += block.text

        else:
            # Model returned the recommendation directly without tool calls
            logger.info(
                f"[AGENTIC] Turn 1 stop_reason={turn1_response.stop_reason} — "
                f"no tool calls, using direct response"
            )
            llm_response = ""
            for block in turn1_response.content:
                if hasattr(block, 'text'):
                    llm_response += block.text

        if not llm_response.strip():
            logger.error(f"[AGENTIC] Empty LLM response for user {user_id}")
            return None

        logger.info(
            f"[AGENTIC] Total tokens: input={total_input_tokens}, "
            f"output={total_output_tokens}"
        )

        # ------------------------------------------------------------------ #
        # Parse response (same parser as legacy path)                         #
        # ------------------------------------------------------------------ #
        sections = parse_llm_response(llm_response)

        # Inject token count into structured_output.meta
        if sections.get('structured_output') is None:
            sections['structured_output'] = {}
        if isinstance(sections['structured_output'], dict):
            sections['structured_output']['meta'] = {
                'agentic': True,
                'tokens_used': total_input_tokens + total_output_tokens,
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
            }

        # ------------------------------------------------------------------ #
        # Build recommendation dict (same structure as generate_recommendations)
        # ------------------------------------------------------------------ #
        activities = get_recent_activities(days=ACTIVITY_ANALYSIS_DAYS, user_id=user_id)
        start_date = activities[0]['date'] if activities else current_date_str
        end_date = activities[-1]['date'] if activities else current_date_str

        recommendation = {
            'generation_date': current_date_str,
            'target_date': target_date,
            'valid_until': None,
            'data_start_date': start_date,
            'data_end_date': end_date,
            'metrics_snapshot': current_metrics,
            'daily_recommendation': sections['daily_recommendation'],
            'weekly_recommendation': sections['weekly_recommendation'],
            'pattern_insights': sections['pattern_insights'],
            'raw_response': llm_response,
            'user_id': user_id,
            'is_autopsy_informed': False,
            'autopsy_count': 0,
            'avg_alignment_score': None,
            'structured_output': sections.get('structured_output'),
        }

        recommendation = fix_dates_for_json(recommendation)
        recommendation_id = save_llm_recommendation(recommendation)
        logger.info(
            f"[AGENTIC] Saved agentic recommendation ID={recommendation_id} "
            f"for user {user_id}, target_date={target_date}"
        )

        recommendation['id'] = recommendation_id
        return recommendation

    except Exception as e:
        logger.error(
            f"[AGENTIC] Error generating agentic recommendation for user {user_id}: {e}",
            exc_info=True
        )
        return None


# =============================================================================
# PHASE C — DEVIATION CLASSIFICATION
# =============================================================================

def classify_deviation(user_id, activity_date, alignment_score, extraction_result, structured_output):
    """Classify whether an autopsy result warrants logging a deviation and/or
    triggering a plan revision proposal.

    This function is always wrapped in try/except at the call site and must
    NEVER raise — classification failure must not break autopsy flow.

    Tier logic:
        Tier 0 — alignment >= 7, or no active weekly plan: no action.
        Tier 1 — alignment 5-6, external cause, or fatigue/injury on filler day:
                  append to deviation_log.
        Tier 2 — injury/fatigue on key session day, key session missed, ACWR
                  spike >20% above load_target_high, or 2+ consecutive injury
                  days: append + set revision_pending.

    Args:
        user_id (int): User ID.
        activity_date (str | date): Date of the activity (YYYY-MM-DD).
        alignment_score (int): 1-10 alignment score from autopsy.
        extraction_result (dict): Extracted signals from recommendation
            conversation (keys: injury_or_pain_notes, preference_note,
            rpe_calibration_signal, nothing_significant).
        structured_output (dict | None): LLM structured_output block for the
            *recommendation* covering this date (may be None if no rec exists).
    """
    try:
        # Normalise activity_date to string
        if isinstance(activity_date, date):
            activity_date_str = activity_date.strftime('%Y-%m-%d')
        else:
            activity_date_str = str(activity_date)

        # --- 1. Fetch week context -----------------------------------------------
        week_ctx = get_current_week_context(user_id)
        if not week_ctx:
            logger.info(
                f"classify_deviation: no weekly_programs row for user {user_id} — Tier 0, no action"
            )
            return

        strategic_summary = week_ctx.get('strategic_summary') or {}
        if not strategic_summary:
            logger.info(
                f"classify_deviation: no strategic_summary for user {user_id} — Tier 0, no action"
            )
            return

        week_start = week_ctx.get('week_start_date')
        deviation_log = week_ctx.get('deviation_log') or []
        key_sessions = strategic_summary.get('key_sessions') or []
        load_target_high = strategic_summary.get('load_target_high')

        # --- 2. Tier 0: high alignment -------------------------------------------
        alignment_score = int(alignment_score) if alignment_score is not None else 5
        if alignment_score >= 7:
            logger.info(
                f"classify_deviation: alignment={alignment_score} >= 7 for user {user_id} — Tier 0, no action"
            )
            return

        # --- 3. Determine key-session day ----------------------------------------
        # key_sessions entries are expected to be day-of-week strings, e.g.
        # "Tuesday", "Thursday", or dicts with a "day" key.
        activity_day_name = datetime.strptime(activity_date_str, '%Y-%m-%d').strftime('%A')

        def _day_name(entry):
            if isinstance(entry, dict):
                return str(entry.get('day', '')).strip().lower()
            return str(entry).strip().lower()

        is_key_day = any(_day_name(e) == activity_day_name.lower() for e in key_sessions)

        # prescribed label for the deviation entry
        if is_key_day:
            matched = next(
                (e for e in key_sessions if _day_name(e) == activity_day_name.lower()), None
            )
            if isinstance(matched, dict):
                prescribed_label = matched.get('session_type') or matched.get('description') or "key session"
            else:
                prescribed_label = "key session"
        else:
            prescribed_label = "filler day"

        # --- 4. Extract signals from extraction_result ---------------------------
        extraction_result = extraction_result or {}
        injury_note = extraction_result.get('injury_or_pain_notes')
        preference_note = extraction_result.get('preference_note') or ''
        rpe_signal = extraction_result.get('rpe_calibration_signal') or ''

        has_injury_flag = bool(injury_note)

        # Also check risk flags in structured_output
        so = structured_output or {}
        risk = so.get('risk') or {}
        so_flags = risk.get('flags') or []

        # Log weekly plan deviation if the LLM flagged one
        so_context = so.get('context') or {}
        if so_context.get('weekly_plan_deviation'):
            logger.info(
                f"Weekly plan deviation recorded for user {user_id} on {activity_date}: "
                f"prescribed='{so_context.get('weekly_plan_prescribed')}' | "
                f"reason='{so_context.get('weekly_plan_deviation_reason')}'"
            )
        if not has_injury_flag:
            has_injury_flag = any(
                'injur' in str(f).lower() or 'pain' in str(f).lower()
                for f in so_flags
            )

        has_fatigue_flag = (
            'fatigue' in rpe_signal.lower()
            or 'fatigue' in preference_note.lower()
            or any('fatigue' in str(f).lower() for f in so_flags)
        )

        external_keywords = ('weather', 'travel', 'work', 'schedule', 'sick', 'illness')
        external_cause = any(kw in preference_note.lower() for kw in external_keywords)

        # --- 5. Check ACWR spike -------------------------------------------------
        acwr_external = risk.get('acwr_external')
        acwr_spike = False
        if acwr_external and load_target_high:
            try:
                acwr_spike = float(acwr_external) > float(load_target_high) * 1.2
            except (TypeError, ValueError):
                pass

        # --- 6. Check consecutive injury days in existing deviation_log ----------
        consecutive_injury = False
        if has_injury_flag and deviation_log:
            try:
                prev_date = (
                    datetime.strptime(activity_date_str, '%Y-%m-%d') - timedelta(days=1)
                ).strftime('%Y-%m-%d')
                for entry in deviation_log:
                    if isinstance(entry, dict) and entry.get('date') == prev_date:
                        entry_reason = str(entry.get('reason', '')).lower()
                        entry_actual = str(entry.get('actual', '')).lower()
                        if 'injur' in entry_reason or 'pain' in entry_reason \
                                or 'injur' in entry_actual or 'pain' in entry_actual:
                            consecutive_injury = True
                            break
            except Exception:
                pass

        # --- 7. Determine tier ---------------------------------------------------
        tier2_reason = None

        if alignment_score <= 4:
            if is_key_day and (has_injury_flag or has_fatigue_flag):
                tier2_reason = f"{'injury' if has_injury_flag else 'fatigue'} flag on key session day"
            elif consecutive_injury:
                tier2_reason = "injury flag on 2+ consecutive days"
            elif acwr_spike:
                tier2_reason = "ACWR spike >20% above weekly load_target_high"
            # else: Tier 1 — alignment <=4 with external cause, fatigue on filler, or plain misalignment
        else:
            # alignment is 5 or 6
            pass  # Tier 1

        # Key session missed entirely (no activity data — check via structured_output decision.action)
        decision = so.get('decision') or {}
        if decision.get('action') == 'rest' and is_key_day and alignment_score <= 4:
            if not tier2_reason:
                tier2_reason = "key session missed entirely"

        tier = 2 if tier2_reason else 1

        # --- 8. Build reason and actual strings ----------------------------------
        if tier2_reason:
            reason = tier2_reason
        elif external_cause:
            reason = f"external constraint: {preference_note[:80]}"
        elif has_injury_flag:
            reason = f"injury/pain noted: {str(injury_note)[:80]}"
        elif has_fatigue_flag:
            reason = f"fatigue signal: {rpe_signal[:80] or 'reported fatigue'}"
        else:
            reason = f"alignment {alignment_score}/10 below threshold"

        actual_str = f"activity completed — alignment {alignment_score}/10"
        if has_injury_flag and injury_note:
            actual_str = f"{str(injury_note)[:100]} — alignment {alignment_score}/10"
        elif has_fatigue_flag and rpe_signal:
            actual_str = f"{rpe_signal[:100]} — alignment {alignment_score}/10"

        # --- 9. Build deviation entry dict ---------------------------------------
        deviation_entry = {
            "date": activity_date_str,
            "tier": tier,
            "alignment": alignment_score,
            "reason": reason,
            "prescribed": prescribed_label,
            "actual": actual_str,
        }

        # --- 10. Append to deviation_log -----------------------------------------
        append_deviation_log(user_id, week_start, deviation_entry)
        logger.info(
            f"classify_deviation: Tier {tier} deviation logged for user {user_id}, "
            f"date={activity_date_str}, alignment={alignment_score}, reason='{reason}'"
        )

        # --- 10a. Write deviation_reason to ai_autopsies -------------------------
        # Makes the category queryable for athlete model threshold calibration.
        if has_injury_flag or has_fatigue_flag:
            deviation_reason = 'physical'
        elif external_cause:
            deviation_reason = 'external'
        else:
            deviation_reason = 'unknown'
        try:
            execute_query(
                """
                UPDATE ai_autopsies
                SET deviation_reason = %s
                WHERE user_id = %s AND date = %s
                """,
                (deviation_reason, user_id, activity_date_str),
                fetch=False
            )
        except Exception as dr_err:
            logger.warning(
                f"classify_deviation: could not write deviation_reason for user {user_id}, "
                f"date={activity_date_str}: {dr_err}"
            )

        # --- 11. Tier 2: set revision_pending ------------------------------------
        if tier == 2:
            prescribed_session_desc = prescribed_label
            if is_key_day:
                proposal_text = (
                    f"{tier2_reason.capitalize()} ({activity_day_name}). "
                    f"Consider replacing {prescribed_session_desc} with easy recovery "
                    f"or adjusting week structure to protect key training stimulus."
                )
            else:
                proposal_text = (
                    f"{tier2_reason.capitalize()} on {activity_day_name}. "
                    f"Review upcoming week load targets and consider reducing intensity."
                )
            proposal = {
                "note": proposal_text,
                "triggered_by": activity_date_str,
                "tier2_reason": tier2_reason,
            }
            set_revision_pending(user_id, week_start, proposal)
            logger.info(
                f"classify_deviation: revision_pending set for user {user_id}, "
                f"week={week_start}, reason='{tier2_reason}'"
            )

    except Exception as e:
        logger.error(
            f"classify_deviation: unexpected error for user {user_id}, "
            f"date={activity_date}, alignment={alignment_score}: {e}",
            exc_info=True
        )


# =============================================================================
# END PHASE 4
# =============================================================================


if __name__ == "__main__":
    # Command line interface for testing
    try:
        print("Training Monkey™ Enhanced LLM Recommendations Generator")
        print("=====================================================")

        import argparse

        parser = argparse.ArgumentParser(description='Generate enhanced training recommendations')
        parser.add_argument('--force', action='store_true', help='Force regeneration of recommendations')
        parser.add_argument('--model', default=DEFAULT_MODEL, help=f'Model to use (default: {DEFAULT_MODEL})')
        args = parser.parse_args()

        # Generate recommendations
        recommendations = generate_recommendations(force=args.force)

        if recommendations:
            print(f"\nEnhanced recommendations generated on {recommendations['generation_date']}")
            print(f"Valid until: {recommendations['valid_until']}")
            print(f"Based on data from: {recommendations['data_start_date']} to {recommendations['data_end_date']}")

            print("\n=== DAILY RECOMMENDATION ===")
            print(recommendations['daily_recommendation'])

            print("\n=== WEEKLY PLANNING ===")
            print(recommendations['weekly_recommendation'])

            print("\n=== PATTERN INSIGHTS ===")
            print(recommendations['pattern_insights'])
        else:
            print("\nFailed to generate enhanced recommendations.")

    except Exception as e:
        print(f"Error: {str(e)}")