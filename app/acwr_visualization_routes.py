#!/usr/bin/env python3
"""
ACWR Visualization Routes
Flask routes for serving the interactive visualization dashboard
"""

import logging
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from acwr_visualization_service import ACWRVisualizationService
from acwr_configuration_service import ACWRConfigurationService

# Create blueprint
acwr_visualization_routes = Blueprint('acwr_visualization_routes', __name__)

# Initialize services
visualization_service = ACWRVisualizationService()
config_service = ACWRConfigurationService()

logger = logging.getLogger(__name__)

# Simple in-memory cache for ACWR calculations
# Format: {cache_key: {'result': acwr_result, 'timestamp': datetime}}
acwr_cache = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache TTL

def get_cache_key(user_id, target_date, chronic_period_days, decay_rate):
    """Generate cache key for ACWR calculation"""
    return f"acwr_{user_id}_{target_date}_{chronic_period_days}_{decay_rate}"

def get_cached_acwr(user_id, target_date, chronic_period_days, decay_rate):
    """Get cached ACWR result if available and not expired"""
    from datetime import datetime
    
    cache_key = get_cache_key(user_id, target_date, chronic_period_days, decay_rate)
    
    if cache_key in acwr_cache:
        cached_entry = acwr_cache[cache_key]
        age_seconds = (datetime.now() - cached_entry['timestamp']).total_seconds()
        
        if age_seconds < CACHE_TTL_SECONDS:
            return cached_entry['result']
        else:
            # Remove expired entry
            del acwr_cache[cache_key]
    
    return None

def cache_acwr_result(user_id, target_date, chronic_period_days, decay_rate, result):
    """Cache ACWR calculation result"""
    from datetime import datetime
    
    cache_key = get_cache_key(user_id, target_date, chronic_period_days, decay_rate)
    acwr_cache[cache_key] = {
        'result': result,
        'timestamp': datetime.now()
    }

def calculate_acwr_from_memory(activities_dict, target_date, chronic_period_days, decay_rate, acute_period_days=7):
    """
    Calculate ACWR using in-memory activities data (no database queries)
    
    Args:
        activities_dict: Dictionary of activities keyed by date string
        target_date: Target date object
        chronic_period_days: Number of days for chronic period
        decay_rate: Exponential decay rate
    
    Returns:
        Dictionary with ACWR calculation results
    """
    from datetime import timedelta
    import math
    
    try:
        # Calculate date ranges
        seven_days_ago = target_date - timedelta(days=6)
        chronic_start = target_date - timedelta(days=chronic_period_days-1)
        
        # Get acute activities (configurable period)
        acute_activities = []
        for i in range(acute_period_days):
            date_key = (target_date - timedelta(days=i)).strftime('%Y-%m-%d')
            if date_key in activities_dict:
                acute_activities.append(activities_dict[date_key])
            else:
                acute_activities.append({'total_load_miles': 0.0, 'trimp': 0.0})
        
        # Get chronic activities (full chronic period including acute)
        # This is the standard ACWR approach where chronic includes acute
        chronic_activities = []
        for i in range(chronic_period_days):  # Use full chronic period
            date_key = (target_date - timedelta(days=i)).strftime('%Y-%m-%d')
            if date_key in activities_dict:
                chronic_activities.append({
                    'date': target_date - timedelta(days=i),
                    'total_load_miles': activities_dict[date_key]['total_load_miles'],
                    'trimp': activities_dict[date_key]['trimp']
                })
            else:
                chronic_activities.append({
                    'date': target_date - timedelta(days=i),
                    'total_load_miles': 0.0,
                    'trimp': 0.0
                })
        
        # Debug logging
        logger.info(f"Acute activities: {len(acute_activities)}, Chronic activities: {len(chronic_activities)}")
        
        # Log sample acute and chronic data for debugging
        acute_loads = [a.get('total_load_miles', 0) for a in acute_activities]
        logger.info(f"Acute loads (7 days): {acute_loads}")
        chronic_loads = [a.get('total_load_miles', 0) for a in chronic_activities[:10]]  # First 10 days
        logger.info(f"Chronic loads (first 10 days): {chronic_loads}")
        
        # Calculate acute averages (simple average for configurable period)
        acute_load_avg = sum(a['total_load_miles'] for a in acute_activities) / acute_period_days
        acute_trimp_avg = sum(a['trimp'] for a in acute_activities) / acute_period_days
        
        # Calculate chronic averages using exponential decay
        total_weight = 0.0
        weighted_load_sum = 0.0
        weighted_trimp_sum = 0.0
        
        for activity in chronic_activities:
            # Calculate days ago from target date
            days_ago = (target_date - activity['date']).days
            
            # Calculate exponential weight
            weight = math.exp(-decay_rate * days_ago)
            total_weight += weight
            
            weighted_load_sum += activity['total_load_miles'] * weight
            weighted_trimp_sum += activity['trimp'] * weight
        
        # Calculate weighted averages
        chronic_load_avg = weighted_load_sum / total_weight if total_weight > 0 else 0.0
        chronic_trimp_avg = weighted_trimp_sum / total_weight if total_weight > 0 else 0.0
        
        # Debug logging for chronic calculation
        logger.info(f"Chronic calculation: total_weight={total_weight:.3f}, chronic_load_avg={chronic_load_avg:.3f}, chronic_trimp_avg={chronic_trimp_avg:.3f}")
        
        # Log first few weights to see decay effect
        sample_weights = []
        for i, activity in enumerate(chronic_activities[:5]):
            days_ago = (target_date - activity['date']).days
            weight = math.exp(-decay_rate * days_ago)
            sample_weights.append(f"day-{days_ago}:{weight:.4f}")
        logger.info(f"Sample weights (first 5): {sample_weights}")
        
        # Calculate ACWR ratios
        external_acwr = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0.0
        internal_acwr = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0.0

        # Calculate normalized divergence using CANONICAL formula (mean-normalized, preserves valence)
        # FIXED: Changed from max-normalized abs() to mean-normalized signed for consistency
        avg_acwr = (external_acwr + internal_acwr) / 2
        if avg_acwr > 0:
            normalized_divergence = (external_acwr - internal_acwr) / avg_acwr
        else:
            normalized_divergence = 0.0
        normalized_divergence = round(normalized_divergence, 3)
        
        # Debug final results
        logger.info(f"Final ACWR: external={external_acwr:.3f}, internal={internal_acwr:.3f}, acute_load={acute_load_avg:.3f}, chronic_load={chronic_load_avg:.3f}")
        
        return {
            'success': True,
            'enhanced_acute_chronic_ratio': external_acwr,
            'enhanced_trimp_acute_chronic_ratio': internal_acwr,
            'enhanced_normalized_divergence': normalized_divergence,
            'acute_load_avg': acute_load_avg,
            'enhanced_chronic_load': chronic_load_avg,
            'acute_trimp_avg': acute_trimp_avg,
            'enhanced_chronic_trimp': chronic_trimp_avg
        }
        
    except Exception as e:
        logger.error(f"Error in calculate_acwr_from_memory: {str(e)}")
        return {
            'success': False,
            'enhanced_acute_chronic_ratio': 0.0,
            'enhanced_trimp_acute_chronic_ratio': 0.0,
            'enhanced_normalized_divergence': 0.0,
            'acute_load_avg': 0.0,
            'enhanced_chronic_load': 0.0,
            'acute_trimp_avg': 0.0,
            'enhanced_chronic_trimp': 0.0
        }

@acwr_visualization_routes.route('/acwr-visualization')
def visualization_dashboard():
    """Serve the main ACWR visualization dashboard"""
    try:
        return render_template('acwr_visualization_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving visualization dashboard: {str(e)}")
        return f"Error loading dashboard: {str(e)}", 500

@acwr_visualization_routes.route('/api/visualization/users', methods=['GET'])
@login_required
def get_users():
    """Get list of users for visualization - admin sees all users, regular users see only themselves"""
    try:
        from flask_login import current_user
        
        # Fetch real users from database
        import db_utils
        
        # Check if current user is admin
        if current_user.is_admin:
            # Admin users can see all users
            query = """
                SELECT id, email, is_admin, registration_date
                FROM user_settings 
                ORDER BY registration_date DESC
            """
            result = db_utils.execute_query(query, fetch=True)
        else:
            # Non-admin users can only see themselves
            query = """
                SELECT id, email, is_admin, registration_date
                FROM user_settings 
                WHERE id = %s
            """
            result = db_utils.execute_query(query, (current_user.id,), fetch=True)
        
        users = []
        for row in result:
            users.append({
                'id': row['id'],
                'name': row['email'],  # Use email as name since there's no username field
                'email': row['email'],
                'created_at': row['registration_date'].isoformat() if row['registration_date'] else None,
                'is_admin': row['is_admin']
            })
        
        return jsonify({
            'success': True,
            'users': users,
            'is_admin': current_user.is_admin
        })
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/configurations', methods=['GET'])
def get_configurations():
    """Get list of ACWR configurations for visualization"""
    try:
        configurations = config_service.get_all_configurations()
        
        return jsonify({
            'success': True,
            'configurations': configurations
        })
    except Exception as e:
        logger.error(f"Error getting configurations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/activities-data', methods=['GET'])
def get_activities_data():
    """Get real activities data for visualization charts - OPTIMIZED VERSION"""
    try:
        user_id = request.args.get('user_id', type=int)
        days_back = request.args.get('days_back', 90, type=int)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id parameter is required'
            }), 400

        # Load user's saved config from database (if exists)
        import db_utils
        user_config = db_utils.execute_query("""
            SELECT chronic_period_days, decay_rate
            FROM user_dashboard_configs
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,), fetch=True)

        # Use saved config as defaults, allow override via query params
        if user_config and len(user_config) > 0:
            default_chronic = user_config[0]['chronic_period_days']
            default_decay = float(user_config[0]['decay_rate'])
        else:
            # Fallback to hardcoded defaults if no config exists
            default_chronic = 42
            default_decay = 0.05

        chronic_period_days = request.args.get('chronic_period_days', default_chronic, type=int)
        decay_rate = request.args.get('decay_rate', default_decay, type=float)

        # Fetch real activities data from database
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # OPTIMIZATION: Single query to get ALL needed activities data
        # Include total_load_miles for complete ACWR calculations
        # Extend date range to include chronic period data
        extended_start_date = start_date - timedelta(days=chronic_period_days)
        
        query = """
            SELECT 
                date,
                total_load_miles,
                trimp
            FROM activities 
            WHERE user_id = %s 
            AND date >= %s 
            AND date <= %s
            ORDER BY date
        """
        
        all_activities = db_utils.execute_query(query, (user_id, extended_start_date, end_date), fetch=True)
        
        logger.info(f"Database query returned {len(all_activities) if all_activities else 0} activities")
        
        if not all_activities:
            return jsonify({
                'success': False,
                'error': 'No activity data found for the specified period'
            }), 404
        
        # Create activities lookup dictionary for fast access
        activities_dict = {}
        for activity in all_activities:
            # Normalize date to string format
            if hasattr(activity['date'], 'date'):
                date_str = activity['date'].date().strftime('%Y-%m-%d')
            elif hasattr(activity['date'], 'strftime'):
                date_str = activity['date'].strftime('%Y-%m-%d')
            else:
                date_str = str(activity['date'])
            
            activities_dict[date_str] = {
                'total_load_miles': float(activity['total_load_miles']) if activity['total_load_miles'] is not None else 0.0,
                'trimp': float(activity['trimp']) if activity['trimp'] is not None else 0.0
            }
        
        # Get activities only in the display period (not the extended period)
        display_activities = [a for a in all_activities 
                            if (hasattr(a['date'], 'date') and start_date <= a['date'].date() <= end_date) or
                               (hasattr(a['date'], 'strftime') and start_date <= a['date'] <= end_date) or
                               (isinstance(a['date'], str) and start_date.strftime('%Y-%m-%d') <= a['date'] <= end_date.strftime('%Y-%m-%d'))]
        
        # Format data for charts
        activities_data = {
            'dates': [],
            'acwr': [],
            'trimp_acwr': [],
            'normalized_divergence': [],
            'acute_load': [],
            'chronic_load': [],
            'acute_trimp': [],
            'chronic_trimp': [],
            'trimp': []
        }
        
        # OPTIMIZATION: Calculate ACWR using in-memory data (no additional DB queries)
        for activity in display_activities:
            # Handle date conversion consistently
            if hasattr(activity['date'], 'date'):
                activity_date = activity['date'].date().strftime('%Y-%m-%d')
                date_obj = activity['date'].date()
            elif hasattr(activity['date'], 'strftime'):
                activity_date = activity['date'].strftime('%Y-%m-%d')
                date_obj = activity['date']
            else:
                activity_date = str(activity['date'])
                date_obj = datetime.strptime(activity_date, '%Y-%m-%d').date()
            
            try:
                # Check cache first
                cached_result = get_cached_acwr(user_id, activity_date, chronic_period_days, decay_rate)
                
                if cached_result:
                    acwr_result = cached_result
                else:
                    # Calculate ACWR using in-memory data
                    acwr_result = calculate_acwr_from_memory(
                        activities_dict=activities_dict,
                        target_date=date_obj,
                        chronic_period_days=chronic_period_days,
                        decay_rate=decay_rate
                    )
                    
                    # Cache the result
                    cache_acwr_result(user_id, activity_date, chronic_period_days, decay_rate, acwr_result)
                
                activities_data['dates'].append(activity_date)
                activities_data['acwr'].append(float(acwr_result.get('enhanced_acute_chronic_ratio', 0)))
                activities_data['trimp_acwr'].append(float(acwr_result.get('enhanced_trimp_acute_chronic_ratio', 0)))
                activities_data['normalized_divergence'].append(float(acwr_result.get('enhanced_normalized_divergence', 0)))
                activities_data['acute_load'].append(float(acwr_result.get('acute_load_avg', 0)))
                activities_data['chronic_load'].append(float(acwr_result.get('enhanced_chronic_load', 0)))
                activities_data['acute_trimp'].append(float(acwr_result.get('acute_trimp_avg', 0)))
                activities_data['chronic_trimp'].append(float(acwr_result.get('enhanced_chronic_trimp', 0)))
                activities_data['trimp'].append(float(activity['trimp']) if activity['trimp'] is not None else 0.0)
                
            except Exception as e:
                logger.warning(f"Error calculating ACWR for date {activity_date}: {str(e)}")
                # Add zero values for failed calculations
                activities_data['dates'].append(activity_date)
                activities_data['acwr'].append(0.0)
                activities_data['trimp_acwr'].append(0.0)
                activities_data['normalized_divergence'].append(0.0)
                activities_data['acute_load'].append(0.0)
                activities_data['chronic_load'].append(0.0)
                activities_data['acute_trimp'].append(0.0)
                activities_data['chronic_trimp'].append(0.0)
                activities_data['trimp'].append(float(activity['trimp']) if activity['trimp'] is not None else 0.0)
        
        logger.info(f"Processed {len(activities_data['dates'])} activities for user {user_id} using optimized method")
        
        return jsonify({
            'success': True,
            'data': activities_data,
            'metadata': {
                'user_id': user_id,
                'days_back': days_back,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'data_points': len(display_activities),
                'chronic_period_days': chronic_period_days,
                'decay_rate': decay_rate,
                'optimization': 'batch_query_enabled',
                'caching_enabled': True,
                'cache_ttl_seconds': CACHE_TTL_SECONDS
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching activities data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/multi-config-data', methods=['GET'])
def get_multi_config_data():
    """Get activities data for multiple ACWR configurations in one request - CONFIGURABLE"""
    try:
        user_id = request.args.get('user_id', type=int)
        days_back = request.args.get('days_back', 90, type=int)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id parameter is required'
            }), 400

        # Load user's saved config as defaults
        import db_utils
        user_config = db_utils.execute_query("""
            SELECT chronic_period_days, decay_rate
            FROM user_dashboard_configs
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,), fetch=True)

        if user_config and len(user_config) > 0:
            default_chronic = user_config[0]['chronic_period_days']
            default_decay = float(user_config[0]['decay_rate'])
        else:
            default_chronic = 42
            default_decay = 0.05

        # Get configurable parameters for the comparison
        base_acute_period = request.args.get('acute_period', 7, type=int)
        base_chronic_period = request.args.get('chronic_period', default_chronic, type=int)
        base_decay_rate = request.args.get('decay_rate', default_decay, type=float)
        
        # Get variation ranges
        chronic_variations = request.args.get('chronic_variations', '28,42,56,70').split(',')
        decay_variations = request.args.get('decay_variations', '0.03,0.05,0.07').split(',')
        
        chronic_variations = [int(x.strip()) for x in chronic_variations]
        decay_variations = [float(x.strip()) for x in decay_variations]

        # Generate configurations based on parameters
        preset_configs = []
        colors = ['#007bff', '#28a745', '#dc3545', '#ffc107', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c']
        
        # Create configurations for chronic period variations
        for i, chronic_days in enumerate(chronic_variations):
            preset_configs.append({
                'name': f'Chronic-{chronic_days}d (decay: {base_decay_rate})',
                'chronic_period_days': chronic_days,
                'acute_period_days': base_acute_period,
                'decay_rate': base_decay_rate,
                'color': colors[i % len(colors)]
            })
        
        # Create configurations for decay rate variations (if different from chronic variations)
        if len(decay_variations) > 1 and len(chronic_variations) == 1:
            preset_configs = []  # Reset if we're doing decay variations instead
            for i, decay_rate in enumerate(decay_variations):
                preset_configs.append({
                    'name': f'Decay-{decay_rate} (chronic: {base_chronic_period}d)',
                    'chronic_period_days': base_chronic_period,
                    'acute_period_days': base_acute_period,
                    'decay_rate': decay_rate,
                    'color': colors[i % len(colors)]
                })
        
        import db_utils
        from datetime import datetime, timedelta
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        # OPTIMIZATION: Single query to get ALL needed activities data
        # Use the largest chronic period (56 days) to ensure we have all data needed
        max_chronic_period = max(config['chronic_period_days'] for config in preset_configs)
        extended_start_date = start_date - timedelta(days=max_chronic_period)
        
        query = """
            SELECT 
                date,
                total_load_miles,
                trimp
            FROM activities 
            WHERE user_id = %s 
            AND date >= %s 
            AND date <= %s
            ORDER BY date
        """
        
        all_activities = db_utils.execute_query(query, (user_id, extended_start_date, end_date), fetch=True)
        
        logger.info(f"Multi-config query returned {len(all_activities) if all_activities else 0} activities")
        
        if not all_activities:
            return jsonify({
                'success': False,
                'error': 'No activity data found for the specified period'
            }), 404
        
        # Create activities lookup dictionary for fast access
        activities_dict = {}
        for activity in all_activities:
            # Normalize date to string format
            if hasattr(activity['date'], 'date'):
                date_str = activity['date'].date().strftime('%Y-%m-%d')
            elif hasattr(activity['date'], 'strftime'):
                date_str = activity['date'].strftime('%Y-%m-%d')
            else:
                date_str = str(activity['date'])
            
            activities_dict[date_str] = {
                'total_load_miles': float(activity['total_load_miles']) if activity['total_load_miles'] is not None else 0.0,
                'trimp': float(activity['trimp']) if activity['trimp'] is not None else 0.0
            }
        
        # Get activities only in the display period
        display_activities = [a for a in all_activities 
                            if (hasattr(a['date'], 'date') and start_date <= a['date'].date() <= end_date) or
                               (hasattr(a['date'], 'strftime') and start_date <= a['date'] <= end_date) or
                               (isinstance(a['date'], str) and start_date.strftime('%Y-%m-%d') <= a['date'] <= end_date.strftime('%Y-%m-%d'))]
        
        # Calculate data for all configurations
        configurations_data = {}
        
        for config in preset_configs:
            config_name = config['name']
            chronic_period_days = config['chronic_period_days']
            acute_period_days = config.get('acute_period_days', 7)
            decay_rate = config['decay_rate']
            
            
            # Format data for this configuration
            config_data = {
                'dates': [],
                'acwr': [],
                'trimp_acwr': [],
                'normalized_divergence': [],
                'acute_load': [],
                'chronic_load': [],
                'acute_trimp': [],
                'chronic_trimp': [],
                'trimp': []
            }
            
            # Calculate ACWR for each activity using in-memory data
            for activity in display_activities:
                # Handle date conversion consistently
                if hasattr(activity['date'], 'date'):
                    activity_date = activity['date'].date().strftime('%Y-%m-%d')
                    date_obj = activity['date'].date()
                elif hasattr(activity['date'], 'strftime'):
                    activity_date = activity['date'].strftime('%Y-%m-%d')
                    date_obj = activity['date']
                else:
                    activity_date = str(activity['date'])
                    date_obj = datetime.strptime(activity_date, '%Y-%m-%d').date()
                
                try:
                    # Check cache first
                    cached_result = get_cached_acwr(user_id, activity_date, chronic_period_days, decay_rate)
                    
                    if cached_result:
                        acwr_result = cached_result
                    else:
                        # Calculate ACWR using in-memory data
                        acwr_result = calculate_acwr_from_memory(
                            activities_dict=activities_dict,
                            target_date=date_obj,
                            chronic_period_days=chronic_period_days,
                            decay_rate=decay_rate,
                            acute_period_days=acute_period_days
                        )
                        
                        # Cache the result
                        cache_acwr_result(user_id, activity_date, chronic_period_days, decay_rate, acwr_result)
                    
                    config_data['dates'].append(activity_date)
                    config_data['acwr'].append(float(acwr_result.get('enhanced_acute_chronic_ratio', 0)))
                    config_data['trimp_acwr'].append(float(acwr_result.get('enhanced_trimp_acute_chronic_ratio', 0)))
                    config_data['normalized_divergence'].append(float(acwr_result.get('enhanced_normalized_divergence', 0)))
                    config_data['acute_load'].append(float(acwr_result.get('acute_load_avg', 0)))
                    config_data['chronic_load'].append(float(acwr_result.get('enhanced_chronic_load', 0)))
                    config_data['acute_trimp'].append(float(acwr_result.get('acute_trimp_avg', 0)))
                    config_data['chronic_trimp'].append(float(acwr_result.get('enhanced_chronic_trimp', 0)))
                    config_data['trimp'].append(float(activity['trimp']) if activity['trimp'] is not None else 0.0)
                    
                except Exception as e:
                    logger.warning(f"Error calculating ACWR for date {activity_date}, config {config_name}: {str(e)}")
                    # Add zero values for failed calculations
                    config_data['dates'].append(activity_date)
                    config_data['acwr'].append(0.0)
                    config_data['trimp_acwr'].append(0.0)
                    config_data['normalized_divergence'].append(0.0)
                    config_data['acute_load'].append(0.0)
                    config_data['chronic_load'].append(0.0)
                    config_data['acute_trimp'].append(0.0)
                    config_data['chronic_trimp'].append(0.0)
                    config_data['trimp'].append(float(activity['trimp']) if activity['trimp'] is not None else 0.0)
            
            # Add configuration metadata
            config_data['config'] = {
                'name': config_name,
                'chronic_period_days': chronic_period_days,
                'decay_rate': decay_rate,
                'color': config['color']
            }
            
            configurations_data[config_name] = config_data
        
        logger.info(f"Processed multi-config data for {len(configurations_data)} configurations, user {user_id}")
        
        return jsonify({
            'success': True,
            'configurations': configurations_data,
            'metadata': {
                'user_id': user_id,
                'days_back': days_back,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'data_points': len(display_activities),
                'configurations_count': len(preset_configs),
                'optimization': 'multi_config_batch_enabled',
                'caching_enabled': True,
                'cache_ttl_seconds': CACHE_TTL_SECONDS
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching multi-config data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Removed unused 3D visualization, heatmap, timeseries, and acwr-ratio endpoints
# These were not being used by the active dashboard charts



@acwr_visualization_routes.route('/api/visualization/sensitivity', methods=['POST'])
def generate_sensitivity():
    """Generate optimized sensitivity analysis data using single query + in-memory calculations"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        analysis_date = data.get('analysis_date')  # Date to analyze (defaults to today)
        base_chronic_period = data.get('base_chronic_period', 42)
        base_decay_rate = data.get('base_decay_rate', 0.05)
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Use provided date or default to today
        if analysis_date is None:
            analysis_date = datetime.now().date().strftime('%Y-%m-%d')
        
        # OPTIMIZATION: Single query approach like other fast charts
        import db_utils
        from datetime import datetime, timedelta
        
        analysis_date_obj = datetime.strptime(analysis_date, '%Y-%m-%d').date()
        
        # Get enough data for the largest chronic period (84 days)
        max_chronic_period = 84
        extended_start_date = analysis_date_obj - timedelta(days=max_chronic_period)
        
        query = """
            SELECT 
                date,
                total_load_miles,
                trimp
            FROM activities 
            WHERE user_id = %s 
            AND date >= %s 
            AND date <= %s
            ORDER BY date
        """
        
        all_activities = db_utils.execute_query(query, (user_id, extended_start_date, analysis_date), fetch=True)
        
        logger.info(f"Sensitivity analysis query returned {len(all_activities) if all_activities else 0} activities")
        
        if not all_activities:
            return jsonify({
                'success': False,
                'error': 'No activity data found for the specified period'
            }), 404
        
        # Create activities lookup dictionary for fast access
        activities_dict = {}
        for activity in all_activities:
            # Normalize date to string format
            if hasattr(activity['date'], 'date'):
                date_key = activity['date'].date().strftime('%Y-%m-%d')
            elif hasattr(activity['date'], 'strftime'):
                date_key = activity['date'].strftime('%Y-%m-%d')
            else:
                date_key = str(activity['date'])
            
            activities_dict[date_key] = {
                'total_load_miles': float(activity['total_load_miles']) if activity['total_load_miles'] else 0.0,
                'trimp': float(activity['trimp']) if activity['trimp'] else 0.0
            }
        
        # Define parameter variations for sensitivity analysis
        chronic_variations = [28, 42, 56, 70, 84]
        decay_variations = [base_decay_rate - 0.02, base_decay_rate, base_decay_rate + 0.02, 0.09]
        
        # Filter valid decay rates
        decay_variations = [rate for rate in decay_variations if 0.01 <= rate <= 0.20]
        
        # Calculate results for each combination using in-memory data
        sensitivity_results = []
        base_result = None
        
        for chronic_period in chronic_variations:
            for decay_rate in decay_variations:
                try:
                    # Calculate ACWR using in-memory data
                    acwr_result = calculate_acwr_from_memory(
                        activities_dict=activities_dict,
                        target_date=analysis_date_obj,
                        chronic_period_days=chronic_period,
                        decay_rate=decay_rate
                    )
                    
                    result = {
                        'chronic_period_days': chronic_period,
                        'decay_rate': decay_rate,
                        'external_acwr': float(acwr_result.get('enhanced_acute_chronic_ratio', 0)),
                        'internal_acwr': float(acwr_result.get('enhanced_trimp_acute_chronic_ratio', 0)),
                        'external_work': float(acwr_result.get('enhanced_chronic_load', 0)),
                        'internal_load': float(acwr_result.get('enhanced_chronic_trimp', 0)),
                        'normalized_divergence': float(acwr_result.get('enhanced_normalized_divergence', 0)),
                        'chronic_load': float(acwr_result.get('enhanced_chronic_load', 0)),
                        'risk_level': 'Unknown',
                        'data_quality': acwr_result.get('data_quality', 'Good')
                    }
                    
                    sensitivity_results.append(result)
                    
                    # Store base result for comparison
                    if (chronic_period == base_chronic_period and 
                        decay_rate == base_decay_rate):
                        base_result = result
                        
                except Exception as e:
                    logger.warning(f"Error in sensitivity analysis for combination {chronic_period}d/{decay_rate}: {str(e)}")
                    # Add a default result to avoid breaking the analysis
                    result = {
                        'chronic_period_days': chronic_period,
                        'decay_rate': decay_rate,
                        'external_acwr': 0,
                        'internal_acwr': 0,
                        'external_work': 0,
                        'internal_load': 0,
                        'normalized_divergence': 0,
                        'chronic_load': 0,
                        'risk_level': 'Error',
                        'data_quality': 'Error'
                    }
                    sensitivity_results.append(result)
                    continue
        
        # Calculate sensitivity metrics
        sensitivity_metrics = {}
        if base_result and sensitivity_results:
            # Basic sensitivity metrics
            external_acwr_values = [r['external_acwr'] for r in sensitivity_results]
            internal_acwr_values = [r['internal_acwr'] for r in sensitivity_results]
            
            if external_acwr_values:
                sensitivity_metrics = {
                    'external_acwr_range': max(external_acwr_values) - min(external_acwr_values),
                    'internal_acwr_range': max(internal_acwr_values) - min(internal_acwr_values),
                    'parameter_combinations': len(sensitivity_results)
                }
        
        analysis_result = {
            'base_parameters': {
                'chronic_period_days': base_chronic_period,
                'decay_rate': base_decay_rate
            },
            'base_result': base_result,
            'sensitivity_results': sensitivity_results,
            'sensitivity_metrics': sensitivity_metrics,
            'parameter_combinations': len(sensitivity_results)
        }
        
        logger.info(f"Completed optimized sensitivity analysis with {len(sensitivity_results)} results")
        
        return jsonify({
            'success': True,
            'sensitivity_data': analysis_result,
            'analysis_date': analysis_date
        })
        
    except Exception as e:
        logger.error(f"Error generating sensitivity analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Removed unused data-quality and current-metrics endpoints
# These were not being used by the active dashboard

@acwr_visualization_routes.route('/api/visualization/export/png', methods=['POST'])
def export_png():
    """Export visualizations as PNG"""
    try:
        data = request.get_json()
        visualization_type = data.get('type', 'all')
        
        # Mock export functionality
        # In real implementation, this would generate actual PNG files
        
        return jsonify({
            'success': True,
            'message': f'PNG export for {visualization_type} initiated',
            'download_url': '/downloads/export.png'
        })
        
    except Exception as e:
        logger.error(f"Error exporting PNG: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/export/svg', methods=['POST'])
def export_svg():
    """Export visualizations as SVG"""
    try:
        data = request.get_json()
        visualization_type = data.get('type', 'all')
        
        # Mock export functionality
        # In real implementation, this would generate actual SVG files
        
        return jsonify({
            'success': True,
            'message': f'SVG export for {visualization_type} initiated',
            'download_url': '/downloads/export.svg'
        })
        
    except Exception as e:
        logger.error(f"Error exporting SVG: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/export/csv', methods=['POST'])
def export_csv():
    """Export data as CSV"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        data_type = data.get('data_type', 'all')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Mock export functionality
        # In real implementation, this would generate actual CSV files
        
        return jsonify({
            'success': True,
            'message': f'CSV export for {data_type} initiated',
            'download_url': '/downloads/export.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_visualization_routes.route('/api/visualization/export/pdf', methods=['POST'])
def export_pdf():
    """Export report as PDF"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        report_type = data.get('report_type', 'comprehensive')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Mock export functionality
        # In real implementation, this would generate actual PDF files
        
        return jsonify({
            'success': True,
            'message': f'PDF report export initiated',
            'download_url': '/downloads/report.pdf'
        })
        
    except Exception as e:
        logger.error(f"Error exporting PDF: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

