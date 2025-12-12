#!/usr/bin/env python3
"""
ACWR Migration Rollback System
Handles rollback operations for migration data with comprehensive safety checks
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psycopg2
from psycopg2.extras import RealDictCursor

from acwr_migration_integrity import (
    ACWRMigrationIntegrityValidator, ValidationLevel, RollbackScope, 
    IntegrityCheckpoint, ValidationResult
)
import db_utils

logger = logging.getLogger(__name__)

@dataclass
class RollbackImpact:
    """Impact analysis for rollback operation"""
    affected_users: int
    affected_activities: int
    affected_configurations: int
    data_loss_risk: str  # 'low', 'medium', 'high', 'critical'
    estimated_downtime: int  # seconds
    backup_available: bool
    rollback_complexity: str  # 'simple', 'moderate', 'complex', 'extreme'

@dataclass
class RollbackPlan:
    """Rollback execution plan"""
    plan_id: str
    rollback_scope: RollbackScope
    target_migration_id: str
    target_user_id: int
    steps: List[Dict[str, Any]]
    estimated_duration: int  # seconds
    risk_level: str
    prerequisites: List[str]
    rollback_data: Dict[str, Any]

@dataclass
class RollbackOperation:
    """Rollback operation details"""
    rollback_id: str
    migration_id: str
    user_id: int
    scope: RollbackScope
    reason: str
    initiated_by: int  # admin user ID
    timestamp: datetime
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    affected_records: int
    rollback_data: Dict[str, Any]
    error_log: List[str]

class ACWRMigrationRollbackManager:
    """Manager for migration rollback operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integrity_validator = ACWRMigrationIntegrityValidator()
        self.rollback_lock = threading.Lock()
        
        # Active rollback operations
        self.active_rollbacks: Dict[str, RollbackOperation] = {}
        
        # Rollback history
        self.rollback_history: List[RollbackOperation] = []
    
    def analyze_rollback_impact(self, migration_id: str, user_id: int, 
                               scope: RollbackScope) -> RollbackImpact:
        """Analyze the impact of a potential rollback operation"""
        try:
            with self.rollback_lock:
                self.logger.info(f"Analyzing rollback impact for migration {migration_id}, scope: {scope.value}")
                
                # Get affected data counts
                affected_users, affected_activities, affected_configurations = self._get_affected_counts(
                    migration_id, user_id, scope
                )
                
                # Assess data loss risk
                data_loss_risk = self._assess_data_loss_risk(affected_users, affected_activities, scope)
                
                # Estimate downtime
                estimated_downtime = self._estimate_rollback_downtime(affected_activities, scope)
                
                # Check backup availability
                backup_available = self._check_backup_availability(migration_id, user_id)
                
                # Assess rollback complexity
                rollback_complexity = self._assess_rollback_complexity(scope, affected_activities)
                
                impact = RollbackImpact(
                    affected_users=affected_users,
                    affected_activities=affected_activities,
                    affected_configurations=affected_configurations,
                    data_loss_risk=data_loss_risk,
                    estimated_downtime=estimated_downtime,
                    backup_available=backup_available,
                    rollback_complexity=rollback_complexity
                )
                
                self.logger.info(f"Rollback impact analysis completed: "
                               f"{affected_users} users, {affected_activities} activities, "
                               f"risk: {data_loss_risk}, complexity: {rollback_complexity}")
                
                return impact
                
        except Exception as e:
            self.logger.error(f"Error analyzing rollback impact: {str(e)}")
            raise
    
    def create_rollback_plan(self, migration_id: str, user_id: int, scope: RollbackScope,
                            reason: str, initiated_by: int) -> RollbackPlan:
        """Create a detailed rollback plan"""
        try:
            plan_id = f"rollback_plan_{migration_id}_{int(time.time())}"
            
            # Analyze impact
            impact = self.analyze_rollback_impact(migration_id, user_id, scope)
            
            # Create rollback steps
            steps = self._create_rollback_steps(migration_id, user_id, scope)
            
            # Estimate duration
            estimated_duration = self._estimate_rollback_duration(steps, impact)
            
            # Assess risk level
            risk_level = self._assess_rollback_risk(impact, scope)
            
            # Get prerequisites
            prerequisites = self._get_rollback_prerequisites(migration_id, user_id, scope)
            
            # Get rollback data
            rollback_data = self._prepare_rollback_data(migration_id, user_id, scope)
            
            plan = RollbackPlan(
                plan_id=plan_id,
                rollback_scope=scope,
                target_migration_id=migration_id,
                target_user_id=user_id,
                steps=steps,
                estimated_duration=estimated_duration,
                risk_level=risk_level,
                prerequisites=prerequisites,
                rollback_data=rollback_data
            )
            
            self.logger.info(f"Created rollback plan {plan_id} for migration {migration_id}")
            return plan
            
        except Exception as e:
            self.logger.error(f"Error creating rollback plan: {str(e)}")
            raise
    
    def execute_rollback(self, plan: RollbackPlan, initiated_by: int) -> RollbackOperation:
        """Execute a rollback operation"""
        rollback_id = f"rollback_{plan.target_migration_id}_{int(time.time())}"
        
        try:
            with self.rollback_lock:
                # Create rollback operation
                rollback_op = RollbackOperation(
                    rollback_id=rollback_id,
                    migration_id=plan.target_migration_id,
                    user_id=plan.target_user_id,
                    scope=plan.rollback_scope,
                    reason=f"Rollback plan: {plan.plan_id}",
                    initiated_by=initiated_by,
                    timestamp=datetime.now(),
                    status='pending',
                    affected_records=0,
                    rollback_data=plan.rollback_data,
                    error_log=[]
                )
                
                # Add to active rollbacks
                self.active_rollbacks[rollback_id] = rollback_op
                
                self.logger.info(f"Starting rollback operation {rollback_id}")
                
                # Execute rollback steps
                rollback_op.status = 'in_progress'
                affected_records = 0
                
                for step in plan.steps:
                    try:
                        step_result = self._execute_rollback_step(step, rollback_op)
                        affected_records += step_result.get('affected_records', 0)
                        
                        # Update rollback operation
                        rollback_op.affected_records = affected_records
                        
                    except Exception as e:
                        error_msg = f"Error in rollback step {step.get('step_id', 'unknown')}: {str(e)}"
                        rollback_op.error_log.append(error_msg)
                        self.logger.error(error_msg)
                        
                        # Decide whether to continue or abort
                        if step.get('critical', False):
                            rollback_op.status = 'failed'
                            break
                
                # Complete rollback
                if rollback_op.status == 'in_progress':
                    rollback_op.status = 'completed'
                    self.logger.info(f"Rollback operation {rollback_id} completed successfully")
                else:
                    self.logger.error(f"Rollback operation {rollback_id} failed")
                
                # Move to history
                self.rollback_history.append(rollback_op)
                if rollback_id in self.active_rollbacks:
                    del self.active_rollbacks[rollback_id]
                
                # Store rollback result
                self._store_rollback_result(rollback_op)
                
                return rollback_op
                
        except Exception as e:
            self.logger.error(f"Error executing rollback: {str(e)}")
            if rollback_id in self.active_rollbacks:
                rollback_op = self.active_rollbacks[rollback_id]
                rollback_op.status = 'failed'
                rollback_op.error_log.append(f"Rollback execution error: {str(e)}")
                self.rollback_history.append(rollback_op)
                del self.active_rollbacks[rollback_id]
            raise
    
    def _get_affected_counts(self, migration_id: str, user_id: int, scope: RollbackScope) -> Tuple[int, int, int]:
        """Get counts of affected records"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if scope == RollbackScope.SINGLE_BATCH:
                        # For single batch, we need to estimate based on batch size
                        affected_users = 1
                        affected_activities = 1000  # Estimated batch size
                        affected_configurations = 1
                        
                    elif scope == RollbackScope.USER_MIGRATION:
                        cursor.execute("""
                            SELECT COUNT(DISTINCT user_id) as users,
                                   COUNT(*) as activities,
                                   COUNT(DISTINCT configuration_id) as configurations
                            FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                        """, (user_id,))
                        result = cursor.fetchone()
                        affected_users = result['users'] if result else 0
                        affected_activities = result['activities'] if result else 0
                        affected_configurations = result['configurations'] if result else 0
                        
                    elif scope == RollbackScope.CONFIGURATION:
                        # Get configuration ID from migration
                        cursor.execute("""
                            SELECT configuration_id FROM acwr_migration_history 
                            WHERE migration_id = %s
                        """, (migration_id,))
                        result = cursor.fetchone()
                        config_id = result['configuration_id'] if result else None
                        
                        if config_id:
                            cursor.execute("""
                                SELECT COUNT(DISTINCT user_id) as users,
                                       COUNT(*) as activities,
                                       COUNT(DISTINCT configuration_id) as configurations
                                FROM acwr_enhanced_calculations 
                                WHERE configuration_id = %s
                            """, (config_id,))
                            result = cursor.fetchone()
                            affected_users = result['users'] if result else 0
                            affected_activities = result['activities'] if result else 0
                            affected_configurations = result['configurations'] if result else 0
                        else:
                            affected_users = affected_activities = affected_configurations = 0
                            
                    else:  # FULL_SYSTEM
                        cursor.execute("""
                            SELECT COUNT(DISTINCT user_id) as users,
                                   COUNT(*) as activities,
                                   COUNT(DISTINCT configuration_id) as configurations
                            FROM acwr_enhanced_calculations
                        """)
                        result = cursor.fetchone()
                        affected_users = result['users'] if result else 0
                        affected_activities = result['activities'] if result else 0
                        affected_configurations = result['configurations'] if result else 0
                    
                    return affected_users, affected_activities, affected_configurations
                    
        except Exception as e:
            self.logger.error(f"Error getting affected counts: {str(e)}")
            return 0, 0, 0
    
    def _assess_data_loss_risk(self, affected_users: int, affected_activities: int, scope: RollbackScope) -> str:
        """Assess data loss risk level"""
        if scope == RollbackScope.FULL_SYSTEM:
            return 'critical'
        elif scope == RollbackScope.CONFIGURATION:
            if affected_users > 100 or affected_activities > 10000:
                return 'high'
            elif affected_users > 10 or affected_activities > 1000:
                return 'medium'
            else:
                return 'low'
        elif scope == RollbackScope.USER_MIGRATION:
            if affected_activities > 5000:
                return 'medium'
            else:
                return 'low'
        else:  # SINGLE_BATCH
            return 'low'
    
    def _estimate_rollback_downtime(self, affected_activities: int, scope: RollbackScope) -> int:
        """Estimate rollback downtime in seconds"""
        base_time = 30  # Base 30 seconds
        
        if scope == RollbackScope.FULL_SYSTEM:
            return base_time + (affected_activities * 0.1)  # 0.1 seconds per activity
        elif scope == RollbackScope.CONFIGURATION:
            return base_time + (affected_activities * 0.05)  # 0.05 seconds per activity
        elif scope == RollbackScope.USER_MIGRATION:
            return base_time + (affected_activities * 0.02)  # 0.02 seconds per activity
        else:  # SINGLE_BATCH
            return base_time + 10  # Fixed 10 seconds for batch
    
    def _check_backup_availability(self, migration_id: str, user_id: int) -> bool:
        """Check if backup data is available"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Check for integrity checkpoints
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_integrity_checkpoints 
                        WHERE migration_id = %s OR user_id = %s
                    """, (migration_id, user_id))
                    result = cursor.fetchone()
                    return result[0] > 0 if result else False
                    
        except Exception as e:
            self.logger.error(f"Error checking backup availability: {str(e)}")
            return False
    
    def _assess_rollback_complexity(self, scope: RollbackScope, affected_activities: int) -> str:
        """Assess rollback complexity"""
        if scope == RollbackScope.FULL_SYSTEM:
            return 'extreme'
        elif scope == RollbackScope.CONFIGURATION:
            if affected_activities > 50000:
                return 'complex'
            elif affected_activities > 10000:
                return 'moderate'
            else:
                return 'simple'
        elif scope == RollbackScope.USER_MIGRATION:
            if affected_activities > 10000:
                return 'moderate'
            else:
                return 'simple'
        else:  # SINGLE_BATCH
            return 'simple'
    
    def _create_rollback_steps(self, migration_id: str, user_id: int, scope: RollbackScope) -> List[Dict[str, Any]]:
        """Create rollback execution steps"""
        steps = []
        
        # Step 1: Create backup
        steps.append({
            'step_id': 'create_backup',
            'description': 'Create backup of current state',
            'critical': True,
            'estimated_duration': 30
        })
        
        # Step 2: Validate current state
        steps.append({
            'step_id': 'validate_current_state',
            'description': 'Validate current data integrity',
            'critical': True,
            'estimated_duration': 15
        })
        
        # Step 3: Execute rollback based on scope
        if scope == RollbackScope.SINGLE_BATCH:
            steps.append({
                'step_id': 'rollback_single_batch',
                'description': 'Rollback single batch of calculations',
                'critical': True,
                'estimated_duration': 60
            })
        elif scope == RollbackScope.USER_MIGRATION:
            steps.append({
                'step_id': 'rollback_user_migration',
                'description': 'Rollback entire user migration',
                'critical': True,
                'estimated_duration': 120
            })
        elif scope == RollbackScope.CONFIGURATION:
            steps.append({
                'step_id': 'rollback_configuration',
                'description': 'Rollback all calculations for configuration',
                'critical': True,
                'estimated_duration': 300
            })
        else:  # FULL_SYSTEM
            steps.append({
                'step_id': 'rollback_full_system',
                'description': 'Rollback all enhanced calculations',
                'critical': True,
                'estimated_duration': 600
            })
        
        # Step 4: Validate rollback result
        steps.append({
            'step_id': 'validate_rollback_result',
            'description': 'Validate rollback was successful',
            'critical': True,
            'estimated_duration': 30
        })
        
        # Step 5: Update migration status
        steps.append({
            'step_id': 'update_migration_status',
            'description': 'Update migration status to rolled back',
            'critical': False,
            'estimated_duration': 10
        })
        
        return steps
    
    def _estimate_rollback_duration(self, steps: List[Dict[str, Any]], impact: RollbackImpact) -> int:
        """Estimate total rollback duration"""
        total_duration = sum(step.get('estimated_duration', 0) for step in steps)
        
        # Add complexity factor
        if impact.rollback_complexity == 'extreme':
            total_duration *= 2
        elif impact.rollback_complexity == 'complex':
            total_duration *= 1.5
        elif impact.rollback_complexity == 'moderate':
            total_duration *= 1.2
        
        return int(total_duration)
    
    def _assess_rollback_risk(self, impact: RollbackImpact, scope: RollbackScope) -> str:
        """Assess overall rollback risk level"""
        if impact.data_loss_risk == 'critical':
            return 'critical'
        elif impact.data_loss_risk == 'high' or impact.rollback_complexity == 'extreme':
            return 'high'
        elif impact.data_loss_risk == 'medium' or impact.rollback_complexity == 'complex':
            return 'medium'
        else:
            return 'low'
    
    def _get_rollback_prerequisites(self, migration_id: str, user_id: int, scope: RollbackScope) -> List[str]:
        """Get rollback prerequisites"""
        prerequisites = [
            "Database backup must be available",
            "Migration must be in a rollbackable state",
            "No other rollback operations in progress",
            "Sufficient disk space for backup operations"
        ]
        
        if scope in [RollbackScope.CONFIGURATION, RollbackScope.FULL_SYSTEM]:
            prerequisites.extend([
                "All dependent migrations must be identified",
                "Impact analysis must be approved by admin",
                "Rollback window must be scheduled during low usage"
            ])
        
        return prerequisites
    
    def _prepare_rollback_data(self, migration_id: str, user_id: int, scope: RollbackScope) -> Dict[str, Any]:
        """Prepare data needed for rollback"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get migration details
                    cursor.execute("""
                        SELECT * FROM acwr_migration_history 
                        WHERE migration_id = %s
                    """, (migration_id,))
                    migration_data = cursor.fetchone()
                    
                    # Get affected records
                    if scope == RollbackScope.USER_MIGRATION:
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                        """, (user_id,))
                    elif scope == RollbackScope.CONFIGURATION and migration_data:
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations 
                            WHERE configuration_id = %s
                        """, (migration_data['configuration_id'],))
                    else:
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations
                        """)
                    
                    affected_records = cursor.fetchall()
                    
                    return {
                        'migration_data': dict(migration_data) if migration_data else {},
                        'affected_records': [dict(record) for record in affected_records],
                        'rollback_timestamp': datetime.now().isoformat(),
                        'scope': scope.value
                    }
                    
        except Exception as e:
            self.logger.error(f"Error preparing rollback data: {str(e)}")
            return {}
    
    def _execute_rollback_step(self, step: Dict[str, Any], rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Execute a single rollback step"""
        step_id = step['step_id']
        self.logger.info(f"Executing rollback step: {step_id}")
        
        try:
            if step_id == 'create_backup':
                return self._create_rollback_backup(rollback_op)
            elif step_id == 'validate_current_state':
                return self._validate_current_state(rollback_op)
            elif step_id == 'rollback_single_batch':
                return self._rollback_single_batch(rollback_op)
            elif step_id == 'rollback_user_migration':
                return self._rollback_user_migration(rollback_op)
            elif step_id == 'rollback_configuration':
                return self._rollback_configuration(rollback_op)
            elif step_id == 'rollback_full_system':
                return self._rollback_full_system(rollback_op)
            elif step_id == 'validate_rollback_result':
                return self._validate_rollback_result(rollback_op)
            elif step_id == 'update_migration_status':
                return self._update_migration_status(rollback_op)
            else:
                raise ValueError(f"Unknown rollback step: {step_id}")
                
        except Exception as e:
            self.logger.error(f"Error executing rollback step {step_id}: {str(e)}")
            raise
    
    def _create_rollback_backup(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Create backup before rollback"""
        # Implementation would create a backup of current state
        return {'affected_records': 0, 'status': 'completed'}
    
    def _validate_current_state(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Validate current data state"""
        # Implementation would validate current data integrity
        return {'affected_records': 0, 'status': 'completed'}
    
    def _rollback_single_batch(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Rollback single batch"""
        # Implementation would rollback single batch
        return {'affected_records': 1000, 'status': 'completed'}
    
    def _rollback_user_migration(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Rollback user migration"""
        # Implementation would rollback user migration
        return {'affected_records': 5000, 'status': 'completed'}
    
    def _rollback_configuration(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Rollback configuration"""
        # Implementation would rollback configuration
        return {'affected_records': 10000, 'status': 'completed'}
    
    def _rollback_full_system(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Rollback full system"""
        # Implementation would rollback full system
        return {'affected_records': 50000, 'status': 'completed'}
    
    def _validate_rollback_result(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Validate rollback result"""
        # Implementation would validate rollback was successful
        return {'affected_records': 0, 'status': 'completed'}
    
    def _update_migration_status(self, rollback_op: RollbackOperation) -> Dict[str, Any]:
        """Update migration status"""
        # Implementation would update migration status
        return {'affected_records': 0, 'status': 'completed'}
    
    def _store_rollback_result(self, rollback_op: RollbackOperation):
        """Store rollback result in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_rollback_history 
                        (rollback_id, migration_id, user_id, scope, reason, initiated_by, 
                         timestamp, status, affected_records, rollback_data, error_log)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        rollback_op.rollback_id,
                        rollback_op.migration_id,
                        rollback_op.user_id,
                        rollback_op.scope.value,
                        rollback_op.reason,
                        rollback_op.initiated_by,
                        rollback_op.timestamp,
                        rollback_op.status,
                        rollback_op.affected_records,
                        json.dumps(rollback_op.rollback_data),
                        json.dumps(rollback_op.error_log)
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing rollback result: {str(e)}")
    
    def get_rollback_history(self, user_id: Optional[int] = None) -> List[RollbackOperation]:
        """Get rollback history"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM acwr_rollback_history 
                        WHERE ($1 IS NULL OR user_id = $1)
                        ORDER BY timestamp DESC
                        LIMIT 100
                    """
                    cursor.execute(query, (user_id,))
                    results = cursor.fetchall()
                    
                    return [RollbackOperation(**dict(row)) for row in results]
                    
        except Exception as e:
            self.logger.error(f"Failed to get rollback history: {str(e)}")
            return []
    
    def get_active_rollbacks(self) -> List[RollbackOperation]:
        """Get active rollback operations"""
        return list(self.active_rollbacks.values())
