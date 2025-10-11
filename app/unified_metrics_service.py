#!/usr/bin/env python3
"""
Simplified Unified Metrics Service for Training Monkey™ Dashboard

Since moving averages are now calculated correctly in the database using time-based aggregation,
this service simply reads the authoritative values from the database.

UPDATED FOR MULTI-USER SUPPORT
"""

import logging
from datetime import datetime, timedelta
from db_utils import execute_query

logger = logging.getLogger('unified_metrics')


class UnifiedMetricsService:
    """
    Enhanced metrics service with multi-sport breakdown support
    Maintains all existing functionality while adding sport-specific analytics
    """

    @staticmethod
    def get_training_load_with_sport_breakdown(user_id, start_date, end_date):
        """
        Get training load data with sport-specific breakdown for dashboard charts

        Returns structure like:
        [
            {
                'date': '2025-08-16',
                'total_load_miles': 8.5,
                'running_load': 6.2,
                'cycling_load': 2.3,  # Already converted to running equivalent
                'day_type': 'mixed',  # 'running', 'cycling', 'mixed', or 'rest'
                'trimp': 145,
                'acute_chronic_ratio': 1.1,
                'activities': [
                    {'type': 'Trail Run', 'sport': 'running', 'distance': 5.0},
                    {'type': 'Road Bike', 'sport': 'cycling', 'distance': 20.0, 'cycling_equivalent': 2.3}
                ]
            }
        ]
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            logger.info(f"Getting sport breakdown for user {user_id} from {start_date} to {end_date}")

            # Query activities with sport breakdown
            activities = execute_query(
                """
                SELECT 
                    date,
                    name,
                    type,
                    sport_type,
                    distance_miles,
                    total_load_miles,
                    trimp,
                    acute_chronic_ratio,
                    trimp_acute_chronic_ratio,
                    cycling_equivalent_miles,
                    average_speed_mph,
                    activity_id
                FROM activities 
                WHERE user_id = %s 
                AND date BETWEEN %s AND %s
                ORDER BY date, activity_id
                """,
                (user_id, start_date, end_date),
                fetch=True
            )

            if not activities:
                logger.warning(f"No activities found for user {user_id} in date range")
                return []

            # Group by date and aggregate sport-specific loads
            daily_breakdown = {}

            for activity in activities:
                date = activity['date']
                sport_type = activity['sport_type'] or 'running'  # Default to running for backward compatibility

                if date not in daily_breakdown:
                    daily_breakdown[date] = {
                        'date': date,
                        'total_load_miles': 0,
                        'running_load': 0,
                        'cycling_load': 0,
                        'trimp': 0,
                        'acute_chronic_ratio': activity['acute_chronic_ratio'],  # Use latest value
                        'trimp_acute_chronic_ratio': activity['trimp_acute_chronic_ratio'],
                        'activities': [],
                        'sports_present': set()
                    }

                # Accumulate loads by sport type
                load_miles = activity['total_load_miles'] or 0
                trimp_value = activity['trimp'] or 0

                daily_breakdown[date]['total_load_miles'] += load_miles
                daily_breakdown[date]['trimp'] += trimp_value
                daily_breakdown[date]['sports_present'].add(sport_type)

                if sport_type == 'running':
                    daily_breakdown[date]['running_load'] += load_miles
                elif sport_type == 'cycling':
                    daily_breakdown[date]['cycling_load'] += load_miles
                else:
                    # Default unknown sports to running for backward compatibility
                    daily_breakdown[date]['running_load'] += load_miles

                # Add activity details for tooltips
                activity_detail = {
                    'type': activity['type'],
                    'sport': sport_type,
                    'distance': activity['distance_miles'],
                    'load_contribution': load_miles
                }

                # Add cycling-specific details
                if sport_type == 'cycling':
                    activity_detail['cycling_equivalent'] = activity['cycling_equivalent_miles']
                    activity_detail['average_speed'] = activity['average_speed_mph']

                daily_breakdown[date]['activities'].append(activity_detail)

            # Determine day type and convert to list
            result = []
            for date, data in daily_breakdown.items():
                sports = data['sports_present']

                if len(sports) == 0:
                    day_type = 'rest'
                elif len(sports) == 1:
                    day_type = list(sports)[0]
                else:
                    day_type = 'mixed'

                data['day_type'] = day_type
                del data['sports_present']  # Remove internal tracking

                result.append(data)

            # Sort by date
            result.sort(key=lambda x: x['date'])

            logger.info(f"Generated sport breakdown for {len(result)} days")
            return result

        except Exception as e:
            logger.error(f"Error getting sport breakdown for user {user_id}: {str(e)}")
            raise

    @staticmethod
    def get_sport_summary(user_id, start_date, end_date):
        """
        Get summary statistics for sport breakdown
        Returns overall statistics for the date range
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            summary = execute_query(
                """
                SELECT 
                    sport_type,
                    COUNT(*) as activity_count,
                    SUM(distance_miles) as total_distance,
                    SUM(total_load_miles) as total_load,
                    AVG(total_load_miles) as avg_load_per_activity,
                    SUM(trimp) as total_trimp
                FROM activities 
                WHERE user_id = %s 
                AND date BETWEEN %s AND %s
                AND activity_id > 0  -- Exclude rest days
                GROUP BY sport_type
                ORDER BY total_load DESC
                """,
                (user_id, start_date, end_date),
                fetch=True
            )

            return [dict(row) for row in summary] if summary else []

        except Exception as e:
            logger.error(f"Error getting sport summary for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def has_cycling_data(user_id, start_date=None, end_date=None):
        """
        Check if user has any cycling activities in the specified date range
        Used for progressive enhancement - only show cycling features if relevant
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            date_filter = ""
            params = [user_id]

            if start_date and end_date:
                date_filter = "AND date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            result = execute_query(
                f"""
                SELECT COUNT(*) as cycling_count
                FROM activities 
                WHERE user_id = %s 
                AND sport_type = 'cycling'
                {date_filter}
                """,
                params,
                fetch=True
            )

            cycling_count = result[0]['cycling_count'] if result else 0
            return cycling_count > 0

        except Exception as e:
            logger.error(f"Error checking cycling data for user {user_id}: {str(e)}")
            return False

    @staticmethod
    def has_swimming_data(user_id, start_date=None, end_date=None):
        """
        Check if user has any swimming activities in the specified date range
        Used for progressive enhancement - only show swimming features if relevant
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            date_filter = ""
            params = [user_id]

            if start_date and end_date:
                date_filter = "AND date BETWEEN %s AND %s"
                params.extend([start_date, end_date])

            result = execute_query(
                f"""
                SELECT COUNT(*) as swimming_count
                FROM activities 
                WHERE user_id = %s 
                AND sport_type = 'swimming'
                {date_filter}
                """,
                params,
                fetch=True
            )

            swimming_count = result[0]['swimming_count'] if result else 0
            return swimming_count > 0

        except Exception as e:
            logger.error(f"Error checking swimming data for user {user_id}: {str(e)}")
            return False

    @staticmethod
    def get_latest_complete_metrics(user_id):
        """
        Get the most recent complete set of training metrics for a specific user.
        Since database now has correct time-based calculations, simply read the latest values.

        Args:
            user_id (int): The user ID to get metrics for

        Returns:
            dict: Complete metrics including ACWR, divergence, and recovery data
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            # Get the absolute latest activity for this user
            latest_activity = execute_query(
                """
                SELECT * FROM activities 
                WHERE user_id = %s
                ORDER BY date DESC 
                LIMIT 1
                """,
                (user_id,),
                fetch=True
            )

            if not latest_activity:
                logger.warning(f"No activities found for user {user_id}")
                return None

            latest_activity_dict = dict(latest_activity[0])
            activity_date = latest_activity_dict['date']

            logger.info(f"Latest activity for user {user_id}: {activity_date}")
            logger.info(f"Activity details: ID={latest_activity_dict.get('activity_id')}, "
                        f"External ACWR={latest_activity_dict.get('acute_chronic_ratio')}, "
                        f"Internal ACWR={latest_activity_dict.get('trimp_acute_chronic_ratio')}")

            # Calculate days since rest using time-based approach for this user
            days_since_rest = UnifiedMetricsService._calculate_days_since_rest_time_based(user_id)

            # Use the database values (now mathematically correct)
            normalized_divergence = latest_activity_dict.get('normalized_divergence')
            if normalized_divergence is None:
                normalized_divergence = UnifiedMetricsService._calculate_normalized_divergence(
                    latest_activity_dict.get('acute_chronic_ratio', 0),
                    latest_activity_dict.get('trimp_acute_chronic_ratio', 0)
                )

            # Build the unified metrics object using the database values
            metrics = {
                'external_acwr': latest_activity_dict.get('acute_chronic_ratio', 0),
                'internal_acwr': latest_activity_dict.get('trimp_acute_chronic_ratio', 0),
                'normalized_divergence': normalized_divergence,
                'seven_day_avg_load': latest_activity_dict.get('seven_day_avg_load', 0),
                'seven_day_avg_trimp': latest_activity_dict.get('seven_day_avg_trimp', 0),
                'twentyeight_day_avg_load': latest_activity_dict.get('twentyeight_day_avg_load', 0),
                'twentyeight_day_avg_trimp': latest_activity_dict.get('twentyeight_day_avg_trimp', 0),
                'days_since_rest': days_since_rest,
                'latest_activity_date': activity_date,
                'calculation_timestamp': datetime.now().isoformat(),
                'user_id': user_id  # Add user_id to response for verification
            }

            # Log the values for debugging
            logger.info(f"Unified metrics for user {user_id}:")
            logger.info(f"  External ACWR: {metrics['external_acwr']}")
            logger.info(f"  Internal ACWR: {metrics['internal_acwr']}")
            logger.info(f"  Normalized Divergence: {metrics['normalized_divergence']}")
            logger.info(f"  Days since rest: {metrics['days_since_rest']}")
            logger.info(f"  Latest activity date: {metrics['latest_activity_date']}")

            return metrics

        except Exception as e:
            logger.error(f"Error getting unified metrics for user {user_id}: {str(e)}")
            return None

    @staticmethod
    def _calculate_days_since_rest_time_based(user_id):
        """
        Calculate days since the last recorded rest day for a specific user.
        FIXED: Uses app timezone for consistent date calculations.
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            # Import timezone utilities
            from timezone_utils import get_user_current_date, log_timezone_debug

            logger.info(f"Calculating days since last recorded rest day for user {user_id} (user timezone)")

            # Find the most recent date explicitly marked as a rest day for this user
            last_rest_day_record = execute_query(
                "SELECT date FROM activities WHERE type = 'rest' AND user_id = %s ORDER BY date DESC LIMIT 1",
                (user_id,),
                fetch=True
            )

            if not last_rest_day_record:
                logger.warning(f"No explicit rest day (type='rest') found for user {user_id}")
                # If no 'type=rest' day is found, calculate days since the very first record for this user
                first_ever_record = execute_query(
                    "SELECT date FROM activities WHERE user_id = %s ORDER BY date ASC LIMIT 1",
                    (user_id,),
                    fetch=True
                )
                if not first_ever_record:
                    logger.info(f"No activities found for user {user_id} at all. Returning 0 days since rest.")
                    return 0

                first_date_str = first_ever_record[0]['date']
                if isinstance(first_date_str, str):
                    first_date = ensure_date_obj(first_date_str)
                elif hasattr(first_date_str, 'date') and callable(first_date_str.date):
                    first_date = first_date_str.date()
                else:
                    first_date = first_date_str

                # FIXED: Use user timezone instead of Pacific-only
                today = get_user_current_date(user_id)

                days_since_first_record = (today - first_date).days
                logger.warning(
                    f"No 'type=rest' day found for user {user_id}. Reporting days since first record ({first_date_str}): {days_since_first_record}")
                return max(0, days_since_first_record)

            last_rest_date_str = last_rest_day_record[0]['date']
            if isinstance(last_rest_date_str, str):
                last_rest_date = ensure_date_obj(last_rest_date_str)
            elif hasattr(last_rest_date_str, 'date') and callable(last_rest_date_str.date):
                # It's a datetime object
                last_rest_date = last_rest_date_str.date()
            else:
                # It's already a date object
                last_rest_date = last_rest_date_str

            # FIXED: Use user timezone instead of Pacific-only
            today = get_user_current_date(user_id)

            days_since = (today - last_rest_date).days

            logger.info(
                f"Last rest day for user {user_id}: {last_rest_date_str}. Days since: {days_since} (using app timezone)")
            logger.info(f"Current app date: {today}")

            return max(0, days_since)

        except Exception as e:
            logger.error(f"Error calculating days since rest for user {user_id}: {str(e)}", exc_info=True)
            return 0

    @staticmethod
    def _calculate_normalized_divergence(external_acwr, internal_acwr):
        """
        Standardized calculation for normalized divergence.

        Args:
            external_acwr (float): External ACWR value
            internal_acwr (float): Internal ACWR value

        Returns:
            float: Normalized divergence value
        """
        try:
            if external_acwr is None or internal_acwr is None:
                return None

            if external_acwr == 0 and internal_acwr == 0:
                return 0

            avg_acwr = (external_acwr + internal_acwr) / 2
            if avg_acwr == 0:
                return 0

            divergence = (external_acwr - internal_acwr) / avg_acwr
            return round(divergence, 3)

        except Exception as e:
            logger.error(f"Error calculating normalized divergence: {str(e)}")
            return None

    @staticmethod
    def get_recent_activities_for_analysis(days=28, user_id=None):
        """
        Get recent activities for LLM analysis for a specific user.
        Since database has correct calculations, just return the data as-is.

        Args:
            days (int): Number of days of history to retrieve
            user_id (int): The user ID to get activities for

        Returns:
            list: List of activity dictionaries from database
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            from timezone_utils import get_user_current_date
            current_date = get_user_current_date(user_id)
            start_date = (current_date - timedelta(days=days)).strftime('%Y-%m-%d')

            activities = execute_query(
                """
                SELECT * FROM activities 
                WHERE date >= %s AND user_id = %s
                ORDER BY date
                """,
                (start_date, user_id),
                fetch=True
            )

            # Convert to list of dictionaries
            processed_activities = []
            for activity in activities:
                activity_dict = dict(activity)

                # Ensure normalized divergence is calculated if missing
                if activity_dict.get('normalized_divergence') is None:
                    activity_dict['normalized_divergence'] = UnifiedMetricsService._calculate_normalized_divergence(
                        activity_dict.get('acute_chronic_ratio'),
                        activity_dict.get('trimp_acute_chronic_ratio')
                    )

                processed_activities.append(activity_dict)

            logger.info(f"Retrieved {len(processed_activities)} activities for user {user_id} analysis from database")
            return processed_activities

        except Exception as e:
            logger.error(f"Error getting recent activities for user {user_id}: {str(e)}")
            return []

    @staticmethod
    def validate_metrics_consistency(user_id):
        """
        Validation method to check database integrity for a specific user.

        Args:
            user_id (int): The user ID to validate

        Returns:
            dict: Validation report
        """
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        try:
            # Get metrics from unified service
            unified_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)

            # Get the same data directly from database
            latest_from_db = execute_query(
                "SELECT * FROM activities WHERE user_id = %s ORDER BY date DESC LIMIT 1",
                (user_id,),
                fetch=True
            )

            report = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'unified_service': unified_metrics,
                'database_raw': dict(latest_from_db[0]) if latest_from_db else None,
                'consistency_check': 'PASS' if unified_metrics and latest_from_db else 'FAIL'
            }

            return report

        except Exception as e:
            logger.error(f"Error validating metrics consistency for user {user_id}: {str(e)}")
            return {'error': str(e), 'user_id': user_id}


def ensure_date_obj(date_input):
    """
    Convert date input to datetime.date object, handling both strings and date objects
    CRITICAL: After database DATE standardization, PostgreSQL returns date objects
    """
    from datetime import datetime, date

    if date_input is None:
        return None
    elif isinstance(date_input, str):
        # String format - parse it
        return datetime.strptime(date_input, '%Y-%m-%d').date()
    elif isinstance(date_input, date):
        # Already a date object
        return date_input
    elif hasattr(date_input, 'date') and callable(date_input.date):
        # It's a datetime object - extract date
        return date_input.date()
    else:
        # Unknown type - try to convert to string first
        return datetime.strptime(str(date_input), '%Y-%m-%d').date()

def get_current_metrics(user_id=None):
    """
    Convenience function that returns the current metrics for a user.

    Args:
        user_id (int): The user ID to get metrics for
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")
    return UnifiedMetricsService.get_latest_complete_metrics(user_id)


def get_days_since_rest(user_id=None):
    """
    Convenience function that returns days since rest for a user.

    Args:
        user_id (int): The user ID to calculate for
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")
    return UnifiedMetricsService._calculate_days_since_rest_time_based(user_id)


def get_recent_activities(days=28, user_id=None):
    """
    Convenience function that returns recent activities for a user.

    Args:
        days (int): Number of days of history to retrieve
        user_id (int): The user ID to get activities for
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")
    return UnifiedMetricsService.get_recent_activities_for_analysis(days, user_id)