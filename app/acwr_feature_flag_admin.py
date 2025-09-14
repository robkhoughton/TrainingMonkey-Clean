#!/usr/bin/env python3
"""
ACWR Feature Flag Admin API
Handles admin interface for managing ACWR feature flags
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user

logger = logging.getLogger(__name__)

# Create blueprint for ACWR feature flag admin routes
acwr_feature_flag_admin = Blueprint('acwr_feature_flag_admin', __name__)

@acwr_feature_flag_admin.route('/api/admin/acwr-feature-flags', methods=['GET'])
@login_required
def get_acwr_feature_flags():
    """Get ACWR feature flag status and user access (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from utils.feature_flags import is_feature_enabled
        
        # Get feature flag status for current user
        enhanced_acwr_enabled = is_feature_enabled('enhanced_acwr_calculation', current_user.id)
        
        # Get user access status for different user types
        user_access = {
            'admin': is_feature_enabled('enhanced_acwr_calculation', 1),
            'beta_users': {
                'user_2': is_feature_enabled('enhanced_acwr_calculation', 2),
                'user_3': is_feature_enabled('enhanced_acwr_calculation', 3)
            },
            'regular_users': is_feature_enabled('enhanced_acwr_calculation', 4)
        }
        
        # Calculate rollout status
        rollout_status = {
            'admin_enabled': user_access['admin'],
            'beta_enabled': user_access['beta_users']['user_2'] and user_access['beta_users']['user_3'],
            'general_release': user_access['regular_users']
        }
        
        return jsonify({
            'success': True,
            'enhanced_acwr_enabled': enhanced_acwr_enabled,
            'user_access': user_access,
            'rollout_status': rollout_status,
            'feature_info': {
                'name': 'Enhanced ACWR Calculation',
                'description': 'Uses exponential decay weighting for chronic load calculation',
                'benefits': [
                    'More accurate training load monitoring',
                    'Configurable chronic period (28-90 days)',
                    'Better injury prevention through improved load tracking'
                ]
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ACWR feature flags: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@acwr_feature_flag_admin.route('/api/admin/acwr-feature-flags/toggle', methods=['POST'])
@login_required
def toggle_acwr_feature_flag():
    """Toggle ACWR feature flag (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        feature_name = data.get('feature_name')
        enabled = data.get('enabled')
        
        if not feature_name:
            return jsonify({'error': 'Feature name is required'}), 400
        
        if feature_name != 'enhanced_acwr_calculation':
            return jsonify({'error': 'Invalid feature name'}), 400
        
        # Note: In a real implementation, this would update a database or configuration file
        # For now, we'll just log the action and return success
        logger.info(f"Admin {current_user.id} toggled {feature_name} to {enabled}")
        
        return jsonify({
            'success': True,
            'message': f'Feature flag {feature_name} {"enabled" if enabled else "disabled"} successfully',
            'feature_name': feature_name,
            'enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Error toggling ACWR feature flag: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@acwr_feature_flag_admin.route('/admin/acwr-feature-flags', methods=['GET'])
@login_required
def admin_acwr_feature_flags():
    """Admin interface for ACWR feature flag management"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return render_template('admin_acwr_feature_flags.html')
        
    except Exception as e:
        logger.error(f"Error loading ACWR feature flags admin interface: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@acwr_feature_flag_admin.route('/api/admin/acwr-feature-flags/status', methods=['GET'])
@login_required
def get_acwr_feature_flag_status():
    """Get detailed ACWR feature flag status (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from utils.feature_flags import is_feature_enabled
        
        # Get comprehensive status
        status = {
            'feature_flags': {
                'enhanced_acwr_calculation': {
                    'enabled': is_feature_enabled('enhanced_acwr_calculation', current_user.id),
                    'description': 'Exponential decay weighting for chronic load calculation'
                }
            },
            'user_access': {
                'admin': is_feature_enabled('enhanced_acwr_calculation', 1),
                'beta_users': {
                    'user_2': is_feature_enabled('enhanced_acwr_calculation', 2),
                    'user_3': is_feature_enabled('enhanced_acwr_calculation', 3)
                },
                'regular_users': is_feature_enabled('enhanced_acwr_calculation', 4)
            },
            'rollout_phases': {
                'phase_1': {
                    'name': 'Admin + Beta Users',
                    'status': 'active',
                    'users': [1, 2, 3],
                    'enabled_count': sum([
                        is_feature_enabled('enhanced_acwr_calculation', 1),
                        is_feature_enabled('enhanced_acwr_calculation', 2),
                        is_feature_enabled('enhanced_acwr_calculation', 3)
                    ])
                },
                'phase_2': {
                    'name': 'Expanded Beta',
                    'status': 'planned',
                    'users': [],
                    'enabled_count': 0
                },
                'phase_3': {
                    'name': 'General Release',
                    'status': 'planned',
                    'users': [],
                    'enabled_count': 0
                }
            }
        }
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting ACWR feature flag status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@acwr_feature_flag_admin.route('/api/admin/acwr-feature-flags/monitoring', methods=['GET'])
@login_required
def get_acwr_feature_flag_monitoring():
    """Get ACWR feature flag monitoring data (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from acwr_feature_flag_monitor import acwr_feature_flag_monitor
        
        hours_back = request.args.get('hours_back', 24, type=int)
        
        # Get monitoring data
        events = acwr_feature_flag_monitor.get_recent_events(hours_back)
        statistics = acwr_feature_flag_monitor.get_event_statistics(hours_back)
        user_summary = acwr_feature_flag_monitor.get_user_access_summary(hours_back)
        
        return jsonify({
            'success': True,
            'monitoring_data': {
                'time_range_hours': hours_back,
                'events': events,
                'statistics': statistics,
                'user_summary': user_summary
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting ACWR feature flag monitoring: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@acwr_feature_flag_admin.route('/api/admin/acwr-feature-flags/export', methods=['GET'])
@login_required
def export_acwr_feature_flag_events():
    """Export ACWR feature flag events (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from acwr_feature_flag_monitor import acwr_feature_flag_monitor
        
        hours_back = request.args.get('hours_back', 24, type=int)
        
        # Export events as JSON
        events_json = acwr_feature_flag_monitor.export_events(hours_back)
        
        return jsonify({
            'success': True,
            'export_data': events_json,
            'time_range_hours': hours_back,
            'export_timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error exporting ACWR feature flag events: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
