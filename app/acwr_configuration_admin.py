#!/usr/bin/env python3
"""
ACWR Configuration Admin Interface
Flask blueprint for managing ACWR configurations
"""

import logging
from flask import Blueprint, render_template, request, jsonify
from functools import wraps
from acwr_configuration_service import ACWRConfigurationService
from acwr_feature_flag_monitor import log_acwr_feature_access
import db_utils

logger = logging.getLogger(__name__)

# Create blueprint
acwr_configuration_admin = Blueprint('acwr_configuration_admin', __name__)

# Error handling decorator
def handle_api_errors(f):
    """Decorator for consistent API error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Validation error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Validation error: {str(e)}',
                'error_type': 'validation_error'
            }), 400
        except PermissionError as e:
            logger.error(f"Permission error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Permission denied: {str(e)}',
                'error_type': 'permission_error'
            }), 403
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}',
                'error_type': 'internal_error'
            }), 500
    return decorated_function

# Validation functions
def validate_configuration_data(data):
    """Validate configuration data"""
    if not data:
        raise ValueError("No data provided")
    
    required_fields = ['name', 'chronic_period_days', 'decay_rate']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate chronic period
    chronic_period = data.get('chronic_period_days')
    try:
        chronic_period = int(chronic_period)
    except (ValueError, TypeError):
        raise ValueError("Chronic period must be a valid number")
    
    if chronic_period < 28 or chronic_period > 90:
        raise ValueError("Chronic period must be between 28 and 90 days")
    
    # Validate decay rate
    decay_rate = data.get('decay_rate')
    try:
        decay_rate = float(decay_rate)
    except (ValueError, TypeError):
        raise ValueError("Decay rate must be a valid number")
    
    if decay_rate < 0.01 or decay_rate > 0.20:
        raise ValueError("Decay rate must be between 0.01 and 0.20")
    
    # Validate name length
    name = data.get('name', '').strip()
    if len(name) < 1 or len(name) > 100:
        raise ValueError("Name must be between 1 and 100 characters")
    
    # Validate description length
    description = data.get('description', '')
    if description and len(description) > 255:
        raise ValueError("Description must be 255 characters or less")
    
    # Validate notes length
    notes = data.get('notes', '')
    if notes and len(notes) > 500:
        raise ValueError("Notes must be 500 characters or less")

def validate_user_assignment_data(data):
    """Validate user assignment data"""
    if not data:
        raise ValueError("No data provided")
    
    if 'user_id' not in data:
        raise ValueError("Missing required field: user_id")
    
    if 'configuration_id' not in data:
        raise ValueError("Missing required field: configuration_id")
    
    # Validate user_id
    user_id = data.get('user_id')
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("User ID must be a positive integer")
    
    # Validate configuration_id
    config_id = data.get('configuration_id')
    if not isinstance(config_id, int) or config_id <= 0:
        raise ValueError("Configuration ID must be a positive integer")

def validate_bulk_assignment_data(data):
    """Validate bulk assignment data"""
    if not data:
        raise ValueError("No data provided")
    
    if 'user_ids' not in data:
        raise ValueError("Missing required field: user_ids")
    
    if 'configuration_id' not in data:
        raise ValueError("Missing required field: configuration_id")
    
    # Validate user_ids
    user_ids = data.get('user_ids')
    if not isinstance(user_ids, list) or len(user_ids) == 0:
        raise ValueError("User IDs must be a non-empty list")
    
    for user_id in user_ids:
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("All user IDs must be positive integers")
    
    # Validate configuration_id
    config_id = data.get('configuration_id')
    if not isinstance(config_id, int) or config_id <= 0:
        raise ValueError("Configuration ID must be a positive integer")

# Admin authentication decorator
def require_admin_auth(f):
    """Decorator to require admin authentication for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check if user is authenticated (placeholder for now)
            # In a real implementation, this would check session, JWT token, etc.
            admin_user_id = request.headers.get('X-Admin-User-ID')
            admin_token = request.headers.get('X-Admin-Token')
            
            # For now, we'll use a simple check
            # In production, this should validate against a proper auth system
            if not admin_user_id or not admin_token:
                # Check for session-based auth as fallback
                from flask import session
                if not session.get('admin_user_id'):
                    raise PermissionError("Admin authentication required")
                admin_user_id = session.get('admin_user_id')
            
            # Validate admin user exists and is active
            service = ACWRConfigurationService()
            admin_user = service.get_admin_user(admin_user_id)
            
            if not admin_user or not admin_user.get('is_active'):
                raise PermissionError("Invalid or inactive admin user")
            
            # Add admin user to request context for use in endpoints
            request.admin_user_id = admin_user_id
            request.admin_user = admin_user
            
            return f(*args, **kwargs)
            
        except PermissionError as e:
            logger.warning(f"Admin authentication failed: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Admin authentication required: {str(e)}',
                'error_type': 'authentication_error'
            }), 401
        except Exception as e:
            logger.error(f"Error in admin authentication: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Authentication system error',
                'error_type': 'authentication_error'
            }), 500
    return decorated_function

@acwr_configuration_admin.route('/admin/acwr-configuration')
def admin_acwr_configuration():
    """Render the ACWR configuration admin interface"""
    try:
        return render_template('admin_acwr_configuration.html')
    except Exception as e:
        logger.error(f"Error rendering ACWR configuration admin interface: {str(e)}")
        return f"Error loading admin interface: {str(e)}", 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations', methods=['GET'])
def get_configurations():
    """Get all ACWR configurations"""
    try:
        service = ACWRConfigurationService()
        configurations = service.get_all_configurations()
        
        # Add user count for each configuration
        for config in configurations:
            config['user_count'] = service.get_configuration_user_count(config['id'])
        
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

@acwr_configuration_admin.route('/api/admin/acwr-configurations', methods=['POST'])
@handle_api_errors
def create_configuration():
    """Create a new ACWR configuration"""
    data = request.get_json()
    validate_configuration_data(data)
    
    service = ACWRConfigurationService()
    config_id = service.create_configuration(
        name=data['name'],
        chronic_period_days=data['chronic_period_days'],
        decay_rate=data['decay_rate'],
        description=data.get('description', ''),
        notes=data.get('notes', ''),
        created_by=1  # TODO: Get from session/auth
    )
    
    if config_id:
        return jsonify({
            'success': True,
            'config_id': config_id,
            'message': 'Configuration created successfully'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to create configuration'
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>', methods=['PUT'])
@handle_api_errors
def update_configuration(config_id):
    """Update an existing ACWR configuration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'chronic_period_days', 'decay_rate']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Validate chronic period
        chronic_period = int(data['chronic_period_days'])
        if chronic_period < 28 or chronic_period > 90:
            return jsonify({
                'success': False,
                'error': 'Chronic period must be between 28 and 90 days'
            }), 400
        
        # Validate decay rate
        decay_rate = float(data['decay_rate'])
        if decay_rate < 0.01 or decay_rate > 0.20:
            return jsonify({
                'success': False,
                'error': 'Decay rate must be between 0.01 and 0.20'
            }), 400
        
        service = ACWRConfigurationService()
        success = service.update_configuration(
            config_id=config_id,
            name=data['name'],
            chronic_period_days=chronic_period,
            decay_rate=decay_rate,
            description=data.get('description', ''),
            notes=data.get('notes', '')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update configuration'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid input: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Error updating configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>/deactivate', methods=['POST'])
def deactivate_configuration(config_id):
    """Deactivate a configuration"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        service = ACWRConfigurationService()
        success = service.deactivate_configuration(config_id, reason)
        
        if success:
            return jsonify({'success': True, 'message': 'Configuration deactivated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to deactivate configuration'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>/reactivate', methods=['POST'])
def reactivate_configuration(config_id):
    """Reactivate a configuration"""
    try:
        service = ACWRConfigurationService()
        success = service.reactivate_configuration(config_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Configuration reactivated successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to reactivate configuration'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>', methods=['DELETE'])
def delete_configuration(config_id):
    """Delete an ACWR configuration"""
    try:
        service = ACWRConfigurationService()
        
        # Check if configuration is default
        config = service.get_configuration_by_id(config_id)
        if config and config.get('is_default'):
            return jsonify({
                'success': False,
                'error': 'Cannot delete default configuration'
            }), 400
        
        success = service.delete_configuration(config_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error deleting configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/assign', methods=['POST'])
def assign_configuration():
    """Assign a configuration to a user"""
    try:
        data = request.get_json()
        
        if 'config_id' not in data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing config_id or user_id'
            }), 400
        
        service = ACWRConfigurationService()
        success = service.assign_configuration_to_user(
            user_id=data['user_id'],
            configuration_id=data['config_id'],
            assigned_by=1,  # TODO: Get from session/auth
            reason=data.get('reason')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration assigned successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to assign configuration'
            }), 500
            
    except Exception as e:
        logger.error(f"Error assigning configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/unassign', methods=['POST'])
def unassign_configuration():
    """Remove a configuration assignment from a user"""
    try:
        data = request.get_json()
        
        if 'config_id' not in data or 'user_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing config_id or user_id'
            }), 400
        
        service = ACWRConfigurationService()
        success = service.unassign_configuration_from_user(
            config_id=data['config_id'],
            user_id=data['user_id']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration assignment removed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to remove configuration assignment'
            }), 500
            
    except Exception as e:
        logger.error(f"Error unassigning configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/bulk-assign', methods=['POST'])
def bulk_assign_configuration():
    """Bulk assign a configuration to multiple users"""
    try:
        data = request.get_json()
        
        if 'config_id' not in data or 'user_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing config_id or user_ids'
            }), 400
        
        if not isinstance(data['user_ids'], list) or len(data['user_ids']) == 0:
            return jsonify({
                'success': False,
                'error': 'user_ids must be a non-empty list'
            }), 400
        
        service = ACWRConfigurationService()
        success_count = 0
        errors = []
        
        for user_id in data['user_ids']:
            try:
                if service.assign_configuration_to_user(
                    user_id=user_id,
                    configuration_id=data['config_id'],
                    assigned_by=1,  # TODO: Get from session/auth
                    reason=data.get('reason')
                ):
                    success_count += 1
                else:
                    errors.append(f"Failed to assign to user {user_id}")
            except Exception as e:
                errors.append(f"Error assigning to user {user_id}: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Configuration assigned to {success_count} users',
            'success_count': success_count,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error bulk assigning configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/bulk-unassign', methods=['POST'])
def bulk_unassign_configuration():
    """Bulk remove a configuration assignment from multiple users"""
    try:
        data = request.get_json()
        
        if 'config_id' not in data or 'user_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing config_id or user_ids'
            }), 400
        
        if not isinstance(data['user_ids'], list) or len(data['user_ids']) == 0:
            return jsonify({
                'success': False,
                'error': 'user_ids must be a non-empty list'
            }), 400
        
        service = ACWRConfigurationService()
        success_count = 0
        errors = []
        
        for user_id in data['user_ids']:
            try:
                if service.unassign_configuration_from_user(data['config_id'], user_id):
                    success_count += 1
                else:
                    errors.append(f"Failed to unassign from user {user_id}")
            except Exception as e:
                errors.append(f"Error unassigning from user {user_id}: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'Configuration assignment removed from {success_count} users',
            'success_count': success_count,
            'errors': errors
        })
        
    except Exception as e:
        logger.error(f"Error bulk unassigning configuration: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/users', methods=['GET'])
def get_users():
    """Get all users for assignment"""
    try:
        # Get real users from the database
        query = """
            SELECT id, email, email, is_admin, registration_date
            FROM user_settings 
            ORDER BY email
        """
        
        result = db_utils.execute_query(query, fetch=True)
        
        if result:
            users = []
            for row in result:
                users.append({
                    'id': row['id'],
                    'username': row['email'],  # Use email as username since username field doesn't exist
                    'email': row['email'],
                    'is_active': not row['is_admin'] if 'is_admin' in row else True,  # Assume non-admin users are active
                    'created_at': row['registration_date'] if 'registration_date' in row else None
                })
        else:
            users = []
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>/users', methods=['GET'])
def get_configuration_users(config_id):
    """Get users assigned to a specific configuration"""
    try:
        service = ACWRConfigurationService()
        users = service.get_configuration_users(config_id)
        
        return jsonify({
            'success': True,
            'users': users
        })
    except Exception as e:
        logger.error(f"Error getting configuration users: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/statistics', methods=['GET'])
def get_configuration_statistics():
    """Get configuration usage statistics"""
    try:
        service = ACWRConfigurationService()
        stats = service.get_configuration_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Error getting configuration statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/assignment-history', methods=['GET'])
def get_assignment_history():
    """Get assignment history with admin attribution"""
    try:
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        user_id = request.args.get('user_id', type=int)
        configuration_id = request.args.get('configuration_id', type=int)
        admin_id = request.args.get('admin_id', type=int)
        
        service = ACWRConfigurationService()
        
        if user_id:
            history = service.get_user_assignment_history(user_id, limit)
        elif configuration_id:
            history = service.get_configuration_assignment_history(configuration_id, limit)
        elif admin_id:
            history = service.get_admin_assignment_history(admin_id, limit)
        else:
            history = service.get_assignment_history(limit=limit)
        
        return jsonify({
            'success': True,
            'history': history
        })
        
    except Exception as e:
        logger.error(f"Error getting assignment history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/rollback-options/<int:user_id>', methods=['GET'])
def get_rollback_options(user_id):
    """Get available rollback options for a user"""
    try:
        service = ACWRConfigurationService()
        options = service.get_rollback_options(user_id)
        
        return jsonify({
            'success': True,
            'options': options
        })
        
    except Exception as e:
        logger.error(f"Error getting rollback options: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/rollback-impact', methods=['POST'])
def analyze_rollback_impact():
    """Analyze the impact of rollback operations"""
    try:
        data = request.get_json()
        rollback_requests = data.get('rollback_requests', [])
        
        if not rollback_requests:
            return jsonify({
                'success': False,
                'error': 'No rollback requests provided'
            }), 400
        
        service = ACWRConfigurationService()
        impact = service.get_rollback_impact_analysis(rollback_requests)
        
        return jsonify({
            'success': True,
            'impact': impact
        })
        
    except Exception as e:
        logger.error(f"Error analyzing rollback impact: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/rollback', methods=['POST'])
@handle_api_errors
def execute_rollback():
    """Execute rollback operations"""
    try:
        data = request.get_json()
        rollback_requests = data.get('rollback_requests', [])
        reason = data.get('reason', '')
        
        if not rollback_requests:
            return jsonify({
                'success': False,
                'error': 'No rollback requests provided'
            }), 400
        
        # For now, we'll use admin ID 1 (you might want to get this from session/auth)
        admin_id = 1
        
        service = ACWRConfigurationService()
        
        if len(rollback_requests) == 1:
            # Single rollback
            request_data = rollback_requests[0]
            user_id = request_data.get('user_id')
            rollback_to_config_id = request_data.get('rollback_to_config_id')
            
            if not user_id or not rollback_to_config_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required parameters'
                }), 400
            
            success = service.rollback_assignment(
                user_id=user_id,
                configuration_id=None,  # Will be determined from current assignment
                rollback_to_config_id=rollback_to_config_id,
                rolled_back_by=admin_id,
                reason=reason
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Rollback executed successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to execute rollback'
                }), 400
        else:
            # Bulk rollback
            results = service.bulk_rollback_assignments(
                rollback_requests=rollback_requests,
                rolled_back_by=admin_id,
                reason=reason
            )
            
            return jsonify({
                'success': True,
                'results': results
            })
        
    except Exception as e:
        logger.error(f"Error executing rollback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/<int:config_id>/preview', methods=['GET'])
def preview_configuration_calculation(config_id):
    """Preview ACWR calculation with a specific configuration"""
    try:
        # Get configuration details
        service = ACWRConfigurationService()
        config = service.get_configuration_by_id(config_id)
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Configuration not found'
            }), 404
        
        # Get sample user for preview (first user with activities)
        sample_user = service.get_sample_user_for_preview()
        
        if not sample_user:
            return jsonify({
                'success': False,
                'error': 'No sample user available for preview'
            }), 404
        
        # Calculate ACWR with the configuration
        user_id = sample_user['id']
        chronic_period_days = config['chronic_period_days']
        decay_rate = config['decay_rate']
        
        # Calculate enhanced ACWR using the configuration service
        acwr_result = service.calculate_enhanced_acwr(
            user_id=user_id,
            activity_date='2025-09-09',  # Use today's date
            configuration=config
        )
        
        # For comparison, we'll just return the enhanced result
        # (Standard ACWR calculation would need to be implemented separately)
        
        # Prepare preview data
        preview_data = {
            'configuration': {
                'id': config['id'],
                'name': config['name'],
                'chronic_period_days': config['chronic_period_days'],
                'decay_rate': config['decay_rate']
            },
            'sample_user': {
                'id': sample_user['id'],
                'username': sample_user.get('username', sample_user.get('email', 'Unknown')),
                'email': sample_user.get('email', 'Unknown')
            },
            'enhanced_acwr': {
                'success': acwr_result.get('success', False),
                'acute_load_avg': acwr_result.get('acute_load_avg', 0),
                'enhanced_chronic_load': acwr_result.get('enhanced_chronic_load', 0),
                'enhanced_acute_chronic_ratio': acwr_result.get('enhanced_acute_chronic_ratio', 0),
                'enhanced_trimp_acute_chronic_ratio': acwr_result.get('enhanced_trimp_acute_chronic_ratio', 0),
                'enhanced_normalized_divergence': acwr_result.get('enhanced_normalized_divergence', 0),
                'calculation_method': acwr_result.get('calculation_method', 'Unknown'),
                'data_quality': acwr_result.get('data_quality', 'Unknown'),
                'error': acwr_result.get('error', None)
            }
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data
        })
        
    except Exception as e:
        logger.error(f"Error previewing configuration calculation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@acwr_configuration_admin.route('/api/admin/acwr-configurations/recalculate', methods=['POST'])
def trigger_recalculation():
    """Trigger recalculation of ACWR values for all users"""
    try:
        data = request.get_json()
        configuration_id = data.get('configuration_id')
        user_ids = data.get('user_ids', [])
        force_recalculate = data.get('force_recalculate', False)
        
        # Get configuration details
        service = ACWRConfigurationService()
        if configuration_id:
            config = service.get_configuration(configuration_id)
            if not config:
                return jsonify({
                    'success': False,
                    'error': 'Configuration not found'
                }), 404
        
        # Import calculation service
        from acwr_calculation_service import ACWRCalculationService
        calc_service = ACWRCalculationService()
        
        # Determine which users to recalculate
        if user_ids:
            # Recalculate specific users
            users_to_process = user_ids
        else:
            # Recalculate all users with the specified configuration
            if configuration_id:
                users_to_process = service.get_users_with_configuration(configuration_id)
            else:
                # Recalculate all active users
                users_to_process = service.get_all_active_users()
        
        # Start recalculation process
        recalculation_results = {
            'total_users': len(users_to_process),
            'processed_users': 0,
            'successful_calculations': 0,
            'failed_calculations': 0,
            'errors': []
        }
        
        # Process users in batches
        batch_size = 10
        for i in range(0, len(users_to_process), batch_size):
            batch = users_to_process[i:i + batch_size]
            
            for user_id in batch:
                try:
                    # Get user's configuration
                    user_config = service.get_user_configuration(user_id)
                    
                    if not user_config and not force_recalculate:
                        continue
                    
                    # Calculate ACWR
                    if user_config:
                        # Use user's specific configuration
                        acwr_result = calc_service.calculate_enhanced_acwr(
                            user_id=user_id,
                            chronic_period_days=user_config['chronic_period_days'],
                            decay_rate=user_config['decay_rate']
                        )
                    else:
                        # Use default configuration
                        acwr_result = calc_service.calculate_standard_acwr(user_id)
                    
                    # Store the result
                    calc_service.store_acwr_calculation(user_id, acwr_result)
                    
                    recalculation_results['successful_calculations'] += 1
                    
                except Exception as e:
                    recalculation_results['failed_calculations'] += 1
                    recalculation_results['errors'].append({
                        'user_id': user_id,
                        'error': str(e)
                    })
                    logger.error(f"Error recalculating ACWR for user {user_id}: {str(e)}")
                
                recalculation_results['processed_users'] += 1
        
        return jsonify({
            'success': True,
            'recalculation_results': recalculation_results,
            'message': f'Recalculation completed. {recalculation_results["successful_calculations"]} successful, {recalculation_results["failed_calculations"]} failed.'
        })
        
    except Exception as e:
        logger.error(f"Error triggering recalculation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
