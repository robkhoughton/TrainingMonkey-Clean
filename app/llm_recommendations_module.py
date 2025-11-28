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

# Import database utilities
from db_utils import (
    execute_query,
    save_llm_recommendation,
    get_latest_recommendation,
    recommendation_needs_update,
    cleanup_old_recommendations,  # Updated from deprecated clear_old_recommendations
    get_last_activity_date
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
DEFAULT_MODEL = "claude-sonnet-4-5"  # Claude Sonnet 4.5 - current balanced model
DEFAULT_VALID_DAYS = 1
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
ACTIVITY_ANALYSIS_DAYS = 28
RECOMMENDATION_TEMPERATURE = 0.7

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

    return api_key


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


def call_anthropic_api(prompt, model=DEFAULT_MODEL, temperature=RECOMMENDATION_TEMPERATURE, max_tokens=2000, timeout=30):
    """Call the Anthropic API with the enhanced prompt.
    
    Args:
        prompt: The prompt text
        model: Claude model to use
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        timeout: API timeout in seconds (default 30, use 60-90 for complex generations)
    """
    try:
        api_key = get_api_key()

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "anthropic-version": "2023-06-01"
        }

        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        logger.info(f"Calling Anthropic API with model {model}, max_tokens={max_tokens}, temperature={temperature}, timeout={timeout}s")
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=data, timeout=timeout)

        if response.status_code != 200:
            error_msg = f"API call failed with status code {response.status_code}: {response.text}"
            logger.error(error_msg)
            # Log specific error details for debugging
            if response.status_code == 401:
                logger.error("Authentication failed - check API key")
            elif response.status_code == 429:
                logger.error("Rate limit exceeded or insufficient credits")
            elif response.status_code == 400:
                logger.error(f"Bad request - check prompt format: {response.text}")
            raise Exception(error_msg)

        response_json = response.json()
        response_text = response_json.get('content', [{}])[0].get('text', '')
        
        logger.info(f"API call successful, response length: {len(response_text)} chars")
        return response_text

    except requests.exceptions.Timeout:
        logger.error("API request timed out after 30 seconds")
        raise
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {str(e)}", exc_info=True)
        raise


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
- Normalized Divergence: {current_metrics.get('normalized_divergence') or 0:.3f}
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


def generate_recommendations(force=False, user_id=None, target_tomorrow=False):
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

        # Small delay to ensure database updates are committed
        import time
        time.sleep(0.5)

        # Load the training guide
        training_guide = load_training_guide()
        if not training_guide:
            logger.error("Training guide not available - falling back to basic recommendations")
            return None

        # CRITICAL FIX: Proper target_date logic based on activity status
        has_activity_today = check_activity_for_date(user_id, current_date_str)

        # NEW: If target_tomorrow is explicitly requested (rest day), always target tomorrow
        if target_tomorrow:
            target_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"REST DAY: Explicitly targeting tomorrow: {target_date}")
        elif has_activity_today:
            # User has already worked out today → recommendation is for TOMORROW
            target_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            logger.info(f"User {user_id} has activity for {current_date_str}, targeting tomorrow: {target_date}")
        else:
            # User has NOT worked out today → recommendation is for TODAY
            target_date = current_date_str
            logger.info(f"User {user_id} has NO activity for {current_date_str}, targeting today: {target_date}")

        # CRITICAL FIX: Check if recommendation already exists for this target_date
        # This prevents overwriting historical recommendations
        existing_recommendation = execute_query(
            """
            SELECT id FROM llm_recommendations 
            WHERE user_id = %s AND target_date = %s
            """,
            (user_id, target_date),
            fetch=True
        )

        if existing_recommendation:
            logger.info(f"Recommendation already exists for target_date {target_date}, skipping generation to preserve historical record")
            return get_latest_recommendation(user_id)

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

        spectrum_value = get_user_coaching_spectrum(user_id)
        logger.info(f"TONE DEBUG: User {user_id} spectrum={spectrum_value}")

        tone_instructions = get_coaching_tone_instructions(spectrum_value)
        logger.info(f"TONE DEBUG: Instructions preview: {tone_instructions[:100]}...")

        # CRITICAL FIX: Get autopsy insights BEFORE creating prompt so they can be incorporated
        autopsy_insights = get_recent_autopsy_insights(user_id, days=3)
        is_autopsy_informed = bool(autopsy_insights and autopsy_insights.get('count', 0) > 0)
        
        if is_autopsy_informed:
            logger.info(f"Generating autopsy-informed recommendation with {autopsy_insights['count']} recent autopsies, avg alignment: {autopsy_insights['avg_alignment']}")
        else:
            logger.info("Generating standard recommendation without recent autopsy data")

        prompt = create_enhanced_prompt_with_tone(current_metrics, activities, pattern_analysis, training_guide, user_id, tone_instructions, autopsy_insights)

        # Call the API
        llm_response = call_anthropic_api(prompt)

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
            'avg_alignment_score': autopsy_insights['avg_alignment'] if autopsy_insights else None
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

def create_enhanced_prompt_with_tone(current_metrics, activities, pattern_analysis, training_guide, user_id, tone_instructions, autopsy_insights=None):
    """Create an enhanced prompt using the training guide framework with coaching tone and optional autopsy learning."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    # Get athlete profile and pattern flags
    athlete_profile = classify_athlete_profile(user_id)
    
    # Get user's recommendation style and adjusted thresholds
    recommendation_style = get_user_recommendation_style(user_id)
    thresholds = get_adjusted_thresholds(recommendation_style)
    
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

    # Build autopsy context section if insights available
    autopsy_context = ""
    if autopsy_insights and autopsy_insights.get('count', 0) > 0:
        alignment_trend = autopsy_insights.get('alignment_trend', [])
        trend_description = "improving" if len(alignment_trend) >= 2 and alignment_trend[-1] > alignment_trend[0] else "mixed"
        
        autopsy_context = f"""
### RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses)
- Average Alignment Score: {autopsy_insights['avg_alignment']:.1f}/10
- Alignment Trend: {trend_description} ({alignment_trend})
- Latest Insights: {autopsy_insights.get('latest_insights', 'No specific insights')[:200]}

**COACHING ADAPTATION STRATEGY:**
- If alignment >7: Athlete follows guidance well - build on successful patterns
- If alignment 4-7: Address recurring deviations - simplify recommendations
- If alignment <4: Major strategy adjustment needed - focus on compliance over optimization

**IMPORTANT:** Use this autopsy learning to adapt today's recommendation. If recent alignment is low, recommend more conservative/achievable targets. If alignment is high, maintain current approach.
"""
    else:
        autopsy_context = ""

    # Build the enhanced prompt with tone integration and risk tolerance context
    prompt = f"""You are an expert endurance sports coach specializing in data-driven training recommendations.

{tone_instructions}

ATHLETE RISK TOLERANCE: {recommendation_style.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days
- Divergence Overtraining Risk: <{thresholds['divergence_overtraining']}

### ATHLETE PROFILE
Athlete Type: {athlete_profile}
Analysis Period: {start_date} to {end_date} ({days_analyzed} days)
Assessment Category: {assessment_category}

### CURRENT METRICS (as of {current_date})
- External ACWR: {formatted_metrics['external_acwr']} (Optimal: 0.8-1.3)
- Internal ACWR: {formatted_metrics['internal_acwr']} (Optimal: 0.8-1.3)  
- Normalized Divergence: {formatted_metrics['normalized_divergence']} (Balance zone: -0.05 to +0.05)
- 7-day Average Load: {formatted_metrics['seven_day_avg_load']} miles/day
- 7-day Average TRIMP: {formatted_metrics['seven_day_avg_trimp']}/day
- Days Since Rest: {formatted_metrics['days_since_rest']}
{autopsy_context}
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
{training_guide}

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
- Reference athlete profile considerations

**PATTERN INSIGHTS:**
- Identify 2-3 specific observations using the pattern recognition framework
- Apply your coaching tone to the delivery of insights
- Interpret metrics relative to this athlete's personalized thresholds
- Include forward-looking trend analysis based on recent patterns

CRITICAL REQUIREMENTS:
- Use the ATHLETE'S PERSONALIZED THRESHOLDS, not the standard guide thresholds
- Apply the specified coaching tone consistently throughout all sections
- Keep each section focused and actionable
- Reference specific numbers from the metrics and use established classification terms (e.g., "Optimal Zone," "High Risk," "Efficient") from the training guide
- Maintain evidence-based analysis while adapting communication style and risk tolerance
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


def classify_athlete_profile(user_id=None):
    """Classify the athlete based on recent training patterns."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Get recent training data to classify athlete type
        recent_activities = execute_query(
            """
            SELECT AVG(total_load_miles) as avg_daily_miles,
                   AVG(elevation_gain_feet) as avg_elevation,
                   COUNT(*) as activity_days,
                   AVG(trimp) as avg_trimp
            FROM activities 
            WHERE date >= %s AND activity_id != 0 AND user_id = %s
            """,
            ((get_app_current_date() - timedelta(days=28)).strftime(DEFAULT_DATE_FORMAT), user_id),
            fetch=True
        )

        if not recent_activities or not recent_activities[0]['avg_daily_miles']:
            return "recreational_runner"

        stats = recent_activities[0]
        avg_daily_miles = stats['avg_daily_miles']
        avg_elevation = stats['avg_elevation'] or 0
        avg_trimp = stats['avg_trimp'] or 0

        # Classification logic based on training patterns
        if avg_daily_miles >= 8 and avg_elevation >= 500:
            return "masters_trail_runner"
        elif avg_daily_miles >= 6 and avg_trimp >= 50:
            return "competitive_runner"
        elif avg_daily_miles >= 4:
            return "recreational_runner"
        else:
            return "beginner_runner"

    except Exception as e:
        logger.error(f"Error classifying athlete profile for user {user_id}: {str(e)}")
        return "recreational_runner"


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
    """Parse the LLM response to extract the different recommendation sections."""
    import re

    sections = {
        'daily_recommendation': '',
        'weekly_recommendation': '',
        'pattern_insights': ''
    }

    if not response_text or not response_text.strip():
        logger.error("Empty response text received")
        return sections

    # Clean the response
    cleaned_response = response_text.strip()

    # Debug log the response format
    logger.info(f"Parsing response of length {len(cleaned_response)}")
    logger.info(f"Response preview: {cleaned_response[:200]}...")

    # FIXED: Handle the actual format Claude is using based on database evidence
    # Database shows Claude is using **DAILY RECOMMENDATION:** format, not ## headers

    # Method 1: Look for **DAILY RECOMMENDATION:** format (current Claude format)
    daily_match = re.search(r'\*\*DAILY\s+RECOMMENDATION:\*\*\s*(.*?)(?=\*\*WEEKLY|\*\*PATTERN|$)',
                            cleaned_response, re.DOTALL | re.IGNORECASE)

    weekly_match = re.search(r'\*\*WEEKLY\s+(?:PLANNING|RECOMMENDATION):\*\*\s*(.*?)(?=\*\*PATTERN|$)',
                             cleaned_response, re.DOTALL | re.IGNORECASE)

    insights_match = re.search(r'\*\*PATTERN\s+INSIGHTS:\*\*\s*(.*?)$',
                               cleaned_response, re.DOTALL | re.IGNORECASE)

    # Method 2: Try ## headers (fallback for compatibility)
    if not daily_match:
        daily_match = re.search(r'##\s*DAILY\s+RECOMMENDATION:?\s*(.*?)(?=##\s*WEEKLY|$)',
                                cleaned_response, re.DOTALL | re.IGNORECASE)

    if not weekly_match:
        weekly_match = re.search(r'##\s*WEEKLY\s+(?:PLANNING|RECOMMENDATION):?\s*(.*?)(?=##\s*PATTERN|$)',
                                 cleaned_response, re.DOTALL | re.IGNORECASE)

    if not insights_match:
        insights_match = re.search(r'##\s*PATTERN\s+INSIGHTS:?\s*(.*?)$',
                                   cleaned_response, re.DOTALL | re.IGNORECASE)

    # Extract matched sections
    if daily_match:
        sections['daily_recommendation'] = daily_match.group(1).strip()
        logger.info(f"Found daily section: {len(sections['daily_recommendation'])} chars")

    if weekly_match:
        sections['weekly_recommendation'] = weekly_match.group(1).strip()
        logger.info(f"Found weekly section: {len(sections['weekly_recommendation'])} chars")

    if insights_match:
        sections['pattern_insights'] = insights_match.group(1).strip()
        logger.info(f"Found insights section: {len(sections['pattern_insights'])} chars")

    # CRITICAL FIX: Based on database evidence, Claude is returning single consolidated responses
    # If no separate sections found, use the entire response as daily recommendation
    if not any(sections.values()):
        logger.warning("No structured sections found, using entire response as daily recommendation")
        sections['daily_recommendation'] = cleaned_response
        sections['weekly_recommendation'] = "Continue monitoring current training approach based on daily guidance."
        sections['pattern_insights'] = "Analysis integrated into daily recommendation above."
        logger.info(f"Using consolidated response: daily section now has {len(sections['daily_recommendation'])} chars")

    # Also handle case where only daily was found (partial match)
    elif sections['daily_recommendation'] and not sections['weekly_recommendation']:
        logger.info("Found daily section but no weekly/pattern sections, providing defaults")
        if not sections['weekly_recommendation']:
            sections['weekly_recommendation'] = "Continue current training approach with focus on ACWR management."
        if not sections['pattern_insights']:
            sections['pattern_insights'] = "Monitor recovery indicators and training load progression."

    # Clean up markdown formatting in each section
    for key in sections:
        if sections[key]:
            sections[key] = process_markdown(sections[key])

    # Final validation and logging
    logger.info("FINAL PARSED SECTIONS:")
    for key, value in sections.items():
        if value and len(value) > 10:
            logger.info(f"✅ {key}: {len(value)} characters")
        else:
            logger.warning(f"❌ {key}: EMPTY or too short")

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

        # Load the training guide for evidence-based analysis
        training_guide = load_training_guide()
        if not training_guide:
            logger.warning("Training guide not available for autopsy generation")
            return generate_basic_autopsy_fallback_enhanced(prescribed_action, actual_activities, observations)

        # Get recent context for better analysis
        activities = UnifiedMetricsService.get_recent_activities_for_analysis(days=7, user_id=user_id)
        current_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)

        if not current_metrics:
            logger.warning(f"No current metrics available for autopsy user {user_id}")
            current_metrics = {
                'external_acwr': 0,
                'internal_acwr': 0,
                'normalized_divergence': 0,
                'days_since_rest': 0
            }

        # Get user's coaching style preference
        spectrum_value = get_user_coaching_spectrum(user_id)
        tone_instructions = get_coaching_tone_instructions(spectrum_value)

        # Create comprehensive autopsy prompt with alignment scoring and tone
        prompt = create_enhanced_autopsy_prompt_with_scoring(
            date_str,
            prescribed_action,
            actual_activities,
            observations,
            current_metrics,
            training_guide,
            tone_instructions  # Add this parameter
        )

        # Get specialized settings for autopsy analysis from config
        autopsy_settings = CONFIG.get('specialized_prompts', {}).get('autopsy_analysis', {})
        autopsy_temperature = autopsy_settings.get('temperature', 0.25)
        autopsy_max_tokens = autopsy_settings.get('max_tokens', 3000)
        
        logger.info(f"Calling API for autopsy with temperature={autopsy_temperature}, max_tokens={autopsy_max_tokens}")
        
        # Call Anthropic API with autopsy-specific settings
        response = call_anthropic_api(prompt, temperature=autopsy_temperature, max_tokens=autopsy_max_tokens)

        if not response:
            logger.error("No response from Anthropic API for enhanced autopsy generation")
            return generate_basic_autopsy_fallback_enhanced(prescribed_action, actual_activities, observations)

        # Parse autopsy response to extract analysis and alignment score
        autopsy_data = parse_enhanced_autopsy_response(response)

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
                                                current_metrics, training_guide, tone_instructions=None):
    """Create comprehensive autopsy prompt that generates alignment scores for learning."""
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

        prompt = f"""You are an expert endurance coach conducting a detailed training autopsy analysis for learning purposes.

{tone_section}ANALYSIS DATE: {date_str}

CURRENT ATHLETE CONTEXT:
- External ACWR: {current_metrics.get('external_acwr') or 0:.2f} (Optimal: 0.8-1.3)
- Internal ACWR: {current_metrics.get('internal_acwr') or 0:.2f} (Optimal: 0.8-1.3)
- Normalized Divergence: {current_metrics.get('normalized_divergence') or 0:.3f} (Balance: -0.05 to +0.05)
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}

PRESCRIBED TRAINING DECISION:
{prescribed_action}

ACTUAL TRAINING COMPLETED:
{activity_summary}

USER OBSERVATIONS:
- Energy Level: {energy_level}/5 (How did the athlete feel going into the session? 5=Fired up, 1=Barely got out of bed)
- RPE (Rate of Perceived Exertion): {rpe_score}/10 (How hard did the workout feel? 10=Maximum effort, 1=Very easy)
- Pain %: {pain_percentage}% (Percentage of time during the activity that the athlete was thinking about pain)
- Additional Notes: {notes}

TRAINING REFERENCE FRAMEWORK:
{training_guide[:1500]}
...

AUTOPSY ANALYSIS INSTRUCTIONS:

You must provide analysis in EXACTLY this format for parsing{', applying the specified coaching tone throughout' if tone_instructions else ''}:

ALIGNMENT_SCORE: [X/10]

ALIGNMENT ASSESSMENT:
[{('Apply the specified coaching tone. ' if tone_instructions else '')}Detailed comparison of prescribed vs actual training. Score 10=perfect compliance, 8-9=minor deviations, 5-7=moderate changes, 1-4=major deviations. Consider volume, intensity, type, and appropriateness given current metrics.]

PHYSIOLOGICAL RESPONSE ANALYSIS:
[{('Use the specified coaching style. ' if tone_instructions else '')}Evaluate energy/RPE/pain levels in context of training load. Compare expected vs actual response. Identify signs of positive adaptation, fatigue, or red flags. Reference Training Reference Guide principles.]

LEARNING INSIGHTS & TOMORROW'S IMPLICATIONS:
[{('Apply the coaching tone throughout. ' if tone_instructions else '')}Key takeaways for future training decisions. Why did athlete deviate (if applicable)? What does response reveal about adaptation state? How should this influence next recommendation? Specific coaching adjustments needed?]

CRITICAL REQUIREMENTS:
- Start with "ALIGNMENT_SCORE: X/10" where X is a number 1-10
- Keep total response under 300 words for Journal display
- Focus on actionable insights that will improve future recommendations
- Use evidence-based analysis referencing Training Reference Guide principles{(' - Apply the specified coaching tone consistently throughout all sections' if tone_instructions else '')}
"""

        return prompt

    except Exception as e:
        logger.error(f"Error creating enhanced autopsy prompt: {str(e)}")
        return create_autopsy_prompt(date_str, prescribed_action, actual_activities, observations, current_metrics,
                                     training_guide)


def parse_enhanced_autopsy_response(response):
    """Parse enhanced autopsy response to extract alignment score and analysis."""
    try:
        import re

        # Extract alignment score
        score_match = re.search(r'ALIGNMENT_SCORE:\s*(\d+)/10', response, re.IGNORECASE)
        alignment_score = int(score_match.group(1)) if score_match else 5

        # Ensure score is in valid range
        alignment_score = max(1, min(10, alignment_score))

        # Clean up the response text for storage
        cleaned_analysis = response.replace('ALIGNMENT_SCORE:', '').strip()
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
            'alignment_score': alignment_score
        }

    except Exception as e:
        logger.error(f"Error generating enhanced fallback autopsy: {str(e)}")
        return {
            'analysis': f"Enhanced autopsy generation failed: {str(e)}",
            'alignment_score': 5
        }


def get_recent_autopsy_insights(user_id, days=3):
    """
    Get recent autopsy insights to inform future training decisions.
    This is the key function that creates the learning loop.
    """
    try:
        cutoff_date = (get_app_current_date() - timedelta(days=days)).strftime('%Y-%m-%d')

        recent_autopsies = execute_query(
            """
            SELECT date, autopsy_analysis, alignment_score, generated_at
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

        # Calculate average alignment and extract key insights
        alignment_scores = []
        key_insights = []

        for row in recent_autopsies:
            autopsy = dict(row)
            if autopsy['alignment_score']:
                alignment_scores.append(autopsy['alignment_score'])

            # Extract learning insights section
            analysis = autopsy['autopsy_analysis'] or ""
            if "LEARNING INSIGHTS" in analysis.upper():
                insights_section = analysis.split("LEARNING INSIGHTS")[-1]
                key_insights.append(insights_section[:200])  # First 200 chars

        avg_alignment = sum(alignment_scores) / len(alignment_scores) if alignment_scores else 5

        return {
            'count': len(recent_autopsies),
            'avg_alignment': round(avg_alignment, 1),
            'latest_insights': key_insights[0] if key_insights else None,
            'alignment_trend': alignment_scores[-3:] if len(alignment_scores) >= 3 else alignment_scores
        }

    except Exception as e:
        logger.error(f"Error getting recent autopsy insights: {str(e)}")
        return None


def generate_autopsy_informed_daily_decision(user_id, target_date=None):
    """
    Generate daily training decision that incorporates recent autopsy learning.
    This is the CORE INNOVATION - autopsy influences next decision.
    """
    try:
        if target_date is None:
            # Use USER'S TIMEZONE for date calculation
            from timezone_utils import get_user_current_date
            target_date = get_user_current_date(user_id) + timedelta(days=1)  # Tomorrow

        target_date_str = target_date.strftime('%Y-%m-%d')

        logger.info(f"Generating autopsy-informed decision for user {user_id}, target {target_date_str}")

        # Get current metrics
        current_metrics = get_current_metrics(user_id)
        if not current_metrics:
            logger.warning(f"No current metrics for autopsy-informed decision user {user_id}")
            return None

        # Get recent autopsy insights (this is the learning component)
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
            # Clean markdown formatting for better display
            cleaned_response = process_markdown(response.strip())
            return cleaned_response
        else:
            logger.warning("No response from autopsy-informed decision generation")
            return None

    except Exception as e:
        logger.error(f"Error generating autopsy-informed decision: {str(e)}")
        return None


def get_user_coaching_spectrum(user_id):
    """NEW FUNCTION: Helper function to get user's coaching spectrum preference"""
    try:
        # Use execute_query (already imported) instead of db.execute
        result = execute_query("""
            SELECT coaching_style_spectrum 
            FROM user_settings 
            WHERE id = %s
        """, (user_id,), fetch=True)

        if result and len(result) > 0:
            return result[0]['coaching_style_spectrum']
        else:
            return 50  # Default to supportive

    except Exception as e:
        logger.error(f"Error fetching coaching spectrum for user {user_id}: {str(e)}")
        return 50  # Default to supportive


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
- Normalized Divergence: {current_metrics.get('normalized_divergence') or 0:.3f}
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}

### TRAINING REFERENCE FRAMEWORK
{training_guide}

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
    """

    # Get user's risk tolerance and personalized thresholds
    recommendation_style = get_user_recommendation_style(user_id)
    thresholds = get_adjusted_thresholds(recommendation_style)
    
    # Load training guide for evidence-based recommendations
    training_guide = load_training_guide()
    if not training_guide:
        logger.warning("Training guide not available for autopsy-informed prompt")
        training_guide = "Apply evidence-based training principles focusing on ACWR management and recovery."

    autopsy_context = ""
    if autopsy_insights:
        alignment_trend = autopsy_insights.get('alignment_trend', [])
        trend_description = "improving" if len(alignment_trend) >= 2 and alignment_trend[-1] > alignment_trend[
            0] else "mixed"

        autopsy_context = f"""
RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses):
- Average Alignment Score: {autopsy_insights['avg_alignment']}/10
- Alignment Trend: {trend_description} ({alignment_trend})
- Key Learning: {autopsy_insights['latest_insights'][:150] if autopsy_insights['latest_insights'] else 'No specific insights'}

COACHING ADAPTATION STRATEGY:
- If alignment >7: Build on successful patterns, athlete follows guidance well
- If alignment 4-7: Address recurring deviations, simplify recommendations
- If alignment <4: Major strategy change needed, focus on compliance over optimization
"""
    else:
        autopsy_context = """
RECENT AUTOPSY LEARNING: No recent autopsy data available
COACHING STRATEGY: Standard evidence-based recommendation without learning context
"""
    # Extract day name safely before f-string
    target_date_obj = safe_datetime_parse(target_date_str)
    day_name = target_date_obj.strftime('%A')

    prompt = f"""You are an expert endurance coach providing tomorrow's training decision with learning from recent autopsy analyses.

TARGET DATE: {target_date_str} ({day_name})

ATHLETE RISK TOLERANCE: {recommendation_style.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days
- Divergence Overtraining Risk: <{thresholds['divergence_overtraining']}

CURRENT METRICS:
- External ACWR: {current_metrics.get('external_acwr') or 0:.2f} (Optimal: 0.8-1.3)
- Internal ACWR: {current_metrics.get('internal_acwr') or 0:.2f} (Optimal: 0.8-1.3)  
- Normalized Divergence: {current_metrics.get('normalized_divergence') or 0:.3f} (Balance: -0.05 to +0.05)
- Days Since Rest: {current_metrics.get('days_since_rest') or 0}
- 7-day Avg Load: {current_metrics.get('seven_day_avg_load') or 0:.2f} miles/day

{autopsy_context}

### TRAINING REFERENCE FRAMEWORK
{training_guide}

INSTRUCTIONS:
Using the Training Reference Framework above, provide a complete training analysis with three sections that demonstrates learning from recent autopsy patterns.
Adapt your coaching approach based on the athlete's demonstrated preferences, adherence patterns, and risk tolerance.

ADAPTIVE COACHING LOGIC:
- High recent alignment: Reinforce successful approaches, maintain recommendation style
- Mixed alignment: Address specific recurring deviations, provide clearer guidance
- Low alignment: Simplify recommendations, focus on achievable targets over optimization
- Always respect the athlete's personalized risk tolerance thresholds listed above

REQUIRED OUTPUT FORMAT:

**DAILY RECOMMENDATION:**
[Provide tomorrow's specific workout recommendation. Apply the Decision Framework assessment order (Safety → Overtraining → ACWR → Recovery → Progression) from the Training Reference Framework. Use the athlete's personalized thresholds, not standard ranges. Assessment paragraph + workout details + monitoring guidance. 150-200 words]

**WEEKLY PLANNING:**
[Provide weekly strategy analysis: address current ACWR trend, recovery cycle, upcoming week structure. Reference autopsy learning patterns and apply weekly planning priorities from the guide. Adjust recommendations to match the athlete's {recommendation_style} risk tolerance. 100-150 words]

**PATTERN INSIGHTS:**
[Identify 2-3 key observations from recent training patterns and autopsy analyses using the pattern recognition framework. Interpret metrics relative to this athlete's personalized thresholds. What's working well? What needs attention? Forward-looking insights. 75-100 words]

CRITICAL REQUIREMENTS:
- Use the athlete's PERSONALIZED THRESHOLDS listed above, not standard guide thresholds
- Apply the Training Reference Framework principles throughout
- Keep each section focused and actionable
- Reference specific numbers from the metrics
- Write naturally and concisely
- Focus on actionable guidance that demonstrates learning from recent patterns
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
                                # Recommendation is already based on latest autopsy
                                next_date = user_current_date + timedelta(days=1)
                                logger.info(f"✅ Today's recommendation ({recommendation_time}) already includes latest autopsy ({autopsy_generated_at})")
                                logger.info(f"✅ Generating for tomorrow ({next_date})")
                        else:
                            # No autopsy for yesterday - generate for tomorrow
                            next_date = user_current_date + timedelta(days=1)
                            logger.info(f"✅ No new autopsy for yesterday, generating for tomorrow ({next_date})")
                    
                    next_date_str = next_date.strftime('%Y-%m-%d')
                    tomorrow_str = next_date_str  # For backward compatibility with existing code
                    
                    # Generate new autopsy-informed decision
                    new_decision = generate_autopsy_informed_daily_decision(user_id, next_date)

                    if new_decision:
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
                            # UPDATE existing recommendation with autopsy-informed decision
                            logger.info(f"Updating existing recommendation for {tomorrow_str} with autopsy learning")
                            execute_query(
                                """
                                UPDATE llm_recommendations
                                SET daily_recommendation = %s,
                                    pattern_insights = %s,
                                    raw_response = %s,
                                    generated_at = NOW(),
                                    is_autopsy_informed = TRUE,
                                    autopsy_count = %s,
                                    avg_alignment_score = %s
                                WHERE user_id = %s AND target_date = %s
                                """,
                                (
                                    new_decision,
                                    f"Updated with autopsy learning (alignment: {autopsy_result['alignment_score']}/10)",
                                    new_decision,
                                    1,  # autopsy_count
                                    autopsy_result['alignment_score'],
                                    user_id,
                                    tomorrow_str
                                )
                            )
                            logger.info(f"Updated recommendation for {tomorrow_str} with autopsy-informed decision")
                        else:
                            # INSERT new recommendation
                            recommendation_data = {
                                'generation_date': app_current_date.strftime('%Y-%m-%d'),
                                'target_date': next_date_str,
                                'valid_until': None,
                                'data_start_date': app_current_date.strftime('%Y-%m-%d'),
                                'data_end_date': app_current_date.strftime('%Y-%m-%d'),
                                'metrics_snapshot': current_metrics,
                                'daily_recommendation': new_decision,
                                'weekly_recommendation': 'See previous weekly guidance',
                                'pattern_insights': f"Generated with autopsy learning (alignment: {autopsy_result['alignment_score']}/10)",
                                'raw_response': new_decision,
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

    # Clean up excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize line breaks
    text = re.sub(r'\s+', ' ', text)  # Normalize spaces
    text = text.strip()

    return text


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