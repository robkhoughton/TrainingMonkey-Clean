#!/usr/bin/env python3
"""
ACWR Migration Rollback Executor
Handles the actual execution of rollback operations with comprehensive safety checks
"""

import logging
import json
import time
import hashlib
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
from acwr_migration_rollback import (
    ACWRMigrationRollbackManager, RollbackImpact, RollbackPlan, RollbackOperation
)
import db_utils

logger = logging.getLogger(__name__)

class RollbackExecutionStatus(Enum):
    """Rollback execution status"""
    PENDING = "pending"
    PREPARING = "preparing"
    BACKING_UP = "backing_up"
    VALIDATING = "validating"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class RollbackExecutionStep:
    """Individual rollback execution step"""
    step_id: str
    step_name: str
    status: RollbackExecutionStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[float]
    success: bool
    error_message: Optional[str]
    affected_records: int
    details: Dict[str, Any]

@dataclass
class RollbackExecutionResult:
    """Result of rollback execution"""
    rollback_id: str
    migration_id: str
    user_id: int
    scope: RollbackScope
    status: RollbackExecutionStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_duration: Optional[float]
    steps: List[RollbackExecutionStep]
    total_affected_records: int
    backup_location: Optional[str]
    verification_passed: bool
    error_log: List[str]
    success: bool

class ACWRMigrationRollbackExecutor:
    """Executor for migration rollback operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.integrity_validator = ACWRMigrationIntegrityValidator()
        self.rollback_manager = ACWRMigrationRollbackManager()
        self.execution_lock = threading.Lock()
        
        # Active rollback executions
        self.active_executions: Dict[str, RollbackExecutionResult] = {}
        
        # Rollback execution history
        self.execution_history: List[RollbackExecutionResult] = []
    
    def execute_rollback(self, plan: RollbackPlan, initiated_by: int, 
                        force_execution: bool = False) -> RollbackExecutionResult:
        """Execute a rollback operation with comprehensive safety checks"""
        rollback_id = f"rollback_exec_{plan.target_migration_id}_{int(time.time())}"
        
        try:
            with self.execution_lock:
                self.logger.info(f"Starting rollback execution {rollback_id} for migration {plan.target_migration_id}")
                
                # Create execution result
                execution_result = RollbackExecutionResult(
                    rollback_id=rollback_id,
                    migration_id=plan.target_migration_id,
                    user_id=plan.target_user_id,
                    scope=plan.rollback_scope,
                    status=RollbackExecutionStatus.PENDING,
                    start_time=datetime.now(),
                    end_time=None,
                    total_duration=None,
                    steps=[],
                    total_affected_records=0,
                    backup_location=None,
                    verification_passed=False,
                    error_log=[],
                    success=False
                )
                
                # Add to active executions
                self.active_executions[rollback_id] = execution_result
                
                # Execute rollback steps
                try:
                    self._execute_rollback_steps(execution_result, plan, force_execution)
                    
                    # Complete execution
                    execution_result.end_time = datetime.now()
                    execution_result.total_duration = (
                        execution_result.end_time - execution_result.start_time
                    ).total_seconds()
                    execution_result.success = execution_result.status == RollbackExecutionStatus.COMPLETED
                    
                    if execution_result.success:
                        self.logger.info(f"Rollback execution {rollback_id} completed successfully")
                    else:
                        self.logger.error(f"Rollback execution {rollback_id} failed")
                    
                except Exception as e:
                    execution_result.status = RollbackExecutionStatus.FAILED
                    execution_result.error_log.append(f"Rollback execution error: {str(e)}")
                    self.logger.error(f"Rollback execution {rollback_id} failed: {str(e)}")
                
                # Move to history
                self.execution_history.append(execution_result)
                if rollback_id in self.active_executions:
                    del self.active_executions[rollback_id]
                
                # Store execution result
                self._store_execution_result(execution_result)
                
                return execution_result
                
        except Exception as e:
            self.logger.error(f"Error executing rollback: {str(e)}")
            raise
    
    def _execute_rollback_steps(self, execution_result: RollbackExecutionResult, 
                               plan: RollbackPlan, force_execution: bool):
        """Execute individual rollback steps"""
        execution_result.status = RollbackExecutionStatus.PREPARING
        
        for step_config in plan.steps:
            step_id = step_config['step_id']
            step_name = step_config['description']
            
            # Create execution step
            execution_step = RollbackExecutionStep(
                step_id=step_id,
                step_name=step_name,
                status=RollbackExecutionStatus.PENDING,
                start_time=None,
                end_time=None,
                duration=None,
                success=False,
                error_message=None,
                affected_records=0,
                details={}
            )
            
            execution_result.steps.append(execution_step)
            
            try:
                # Execute step
                self._execute_single_step(execution_step, execution_result, plan, force_execution)
                
                # Update execution status based on step result
                if not execution_step.success and step_config.get('critical', False):
                    execution_result.status = RollbackExecutionStatus.FAILED
                    execution_result.error_log.append(f"Critical step {step_id} failed: {execution_step.error_message}")
                    break
                elif execution_step.success:
                    execution_result.total_affected_records += execution_step.affected_records
                
            except Exception as e:
                execution_step.success = False
                execution_step.error_message = str(e)
                execution_step.end_time = datetime.now()
                if execution_step.start_time:
                    execution_step.duration = (execution_step.end_time - execution_step.start_time).total_seconds()
                
                if step_config.get('critical', False):
                    execution_result.status = RollbackExecutionStatus.FAILED
                    execution_result.error_log.append(f"Critical step {step_id} failed: {str(e)}")
                    break
        
        # Set final status
        if execution_result.status == RollbackExecutionStatus.PREPARING:
            if all(step.success for step in execution_result.steps):
                execution_result.status = RollbackExecutionStatus.COMPLETED
            else:
                execution_result.status = RollbackExecutionStatus.FAILED
    
    def _execute_single_step(self, execution_step: RollbackExecutionStep, 
                           execution_result: RollbackExecutionResult, 
                           plan: RollbackPlan, force_execution: bool):
        """Execute a single rollback step"""
        execution_step.start_time = datetime.now()
        execution_step.status = RollbackExecutionStatus.PREPARING
        
        try:
            step_id = execution_step.step_id
            
            if step_id == 'create_backup':
                self._execute_create_backup_step(execution_step, execution_result)
            elif step_id == 'validate_current_state':
                self._execute_validate_current_state_step(execution_step, execution_result)
            elif step_id == 'rollback_single_batch':
                self._execute_rollback_single_batch_step(execution_step, execution_result, plan)
            elif step_id == 'rollback_user_migration':
                self._execute_rollback_user_migration_step(execution_step, execution_result, plan)
            elif step_id == 'rollback_configuration':
                self._execute_rollback_configuration_step(execution_step, execution_result, plan)
            elif step_id == 'rollback_full_system':
                self._execute_rollback_full_system_step(execution_step, execution_result, plan)
            elif step_id == 'validate_rollback_result':
                self._execute_validate_rollback_result_step(execution_step, execution_result)
            elif step_id == 'update_migration_status':
                self._execute_update_migration_status_step(execution_step, execution_result, plan)
            else:
                raise ValueError(f"Unknown rollback step: {step_id}")
            
            # Mark step as completed
            execution_step.success = True
            execution_step.status = RollbackExecutionStatus.COMPLETED
            
        except Exception as e:
            execution_step.success = False
            execution_step.error_message = str(e)
            execution_step.status = RollbackExecutionStatus.FAILED
            self.logger.error(f"Error executing step {execution_step.step_id}: {str(e)}")
        
        finally:
            execution_step.end_time = datetime.now()
            if execution_step.start_time:
                execution_step.duration = (execution_step.end_time - execution_step.start_time).total_seconds()
    
    def _execute_create_backup_step(self, execution_step: RollbackExecutionStep, 
                                  execution_result: RollbackExecutionResult):
        """Execute backup creation step"""
        execution_step.status = RollbackExecutionStatus.BACKING_UP
        
        try:
            # Create backup of current enhanced calculations
            backup_data = self._create_enhanced_calculations_backup(
                execution_result.migration_id, execution_result.user_id, execution_result.scope
            )
            
            # Store backup location
            backup_location = self._store_backup_data(backup_data, execution_result.rollback_id)
            execution_result.backup_location = backup_location
            
            execution_step.details = {
                'backup_location': backup_location,
                'backup_size': len(json.dumps(backup_data)),
                'backup_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Backup created successfully: {backup_location}")
            
        except Exception as e:
            raise Exception(f"Failed to create backup: {str(e)}")
    
    def _execute_validate_current_state_step(self, execution_step: RollbackExecutionStep, 
                                           execution_result: RollbackExecutionResult):
        """Execute current state validation step"""
        execution_step.status = RollbackExecutionStatus.VALIDATING
        
        try:
            # Validate current data integrity
            validation_result = self.integrity_validator.validate_migration_data(
                execution_result.migration_id, 
                execution_result.user_id, 
                ValidationLevel.STANDARD
            )
            
            execution_step.details = {
                'validation_level': validation_result.validation_level.value,
                'is_valid': validation_result.is_valid,
                'validated_count': validation_result.validated_count,
                'failed_count': validation_result.failed_count,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings
            }
            
            if not validation_result.is_valid:
                raise Exception(f"Current state validation failed: {validation_result.errors}")
            
            self.logger.info(f"Current state validation passed: {validation_result.validated_count} records validated")
            
        except Exception as e:
            raise Exception(f"Current state validation failed: {str(e)}")
    
    def _execute_rollback_single_batch_step(self, execution_step: RollbackExecutionStep, 
                                          execution_result: RollbackExecutionResult, 
                                          plan: RollbackPlan):
        """Execute single batch rollback step"""
        execution_step.status = RollbackExecutionStatus.EXECUTING
        
        try:
            # Get batch to rollback (simplified - in practice, you'd track batch membership)
            affected_records = self._rollback_enhanced_calculations_batch(
                execution_result.user_id, execution_result.migration_id
            )
            
            execution_step.affected_records = affected_records
            execution_step.details = {
                'rollback_scope': 'single_batch',
                'affected_records': affected_records,
                'rollback_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Single batch rollback completed: {affected_records} records affected")
            
        except Exception as e:
            raise Exception(f"Single batch rollback failed: {str(e)}")
    
    def _execute_rollback_user_migration_step(self, execution_step: RollbackExecutionStep, 
                                            execution_result: RollbackExecutionResult, 
                                            plan: RollbackPlan):
        """Execute user migration rollback step"""
        execution_step.status = RollbackExecutionStatus.EXECUTING
        
        try:
            # Rollback all enhanced calculations for user
            affected_records = self._rollback_enhanced_calculations_user(
                execution_result.user_id, execution_result.migration_id
            )
            
            execution_step.affected_records = affected_records
            execution_step.details = {
                'rollback_scope': 'user_migration',
                'affected_records': affected_records,
                'rollback_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"User migration rollback completed: {affected_records} records affected")
            
        except Exception as e:
            raise Exception(f"User migration rollback failed: {str(e)}")
    
    def _execute_rollback_configuration_step(self, execution_step: RollbackExecutionStep, 
                                           execution_result: RollbackExecutionResult, 
                                           plan: RollbackPlan):
        """Execute configuration rollback step"""
        execution_step.status = RollbackExecutionStatus.EXECUTING
        
        try:
            # Get configuration ID from plan
            config_id = plan.rollback_data.get('migration_data', {}).get('configuration_id')
            if not config_id:
                raise Exception("Configuration ID not found in rollback data")
            
            # Rollback all enhanced calculations for configuration
            affected_records = self._rollback_enhanced_calculations_configuration(
                config_id, execution_result.migration_id
            )
            
            execution_step.affected_records = affected_records
            execution_step.details = {
                'rollback_scope': 'configuration',
                'configuration_id': config_id,
                'affected_records': affected_records,
                'rollback_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Configuration rollback completed: {affected_records} records affected")
            
        except Exception as e:
            raise Exception(f"Configuration rollback failed: {str(e)}")
    
    def _execute_rollback_full_system_step(self, execution_step: RollbackExecutionStep, 
                                         execution_result: RollbackExecutionResult, 
                                         plan: RollbackPlan):
        """Execute full system rollback step"""
        execution_step.status = RollbackExecutionStatus.EXECUTING
        
        try:
            # Rollback all enhanced calculations
            affected_records = self._rollback_enhanced_calculations_full_system(
                execution_result.migration_id
            )
            
            execution_step.affected_records = affected_records
            execution_step.details = {
                'rollback_scope': 'full_system',
                'affected_records': affected_records,
                'rollback_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Full system rollback completed: {affected_records} records affected")
            
        except Exception as e:
            raise Exception(f"Full system rollback failed: {str(e)}")
    
    def _execute_validate_rollback_result_step(self, execution_step: RollbackExecutionStep, 
                                             execution_result: RollbackExecutionResult):
        """Execute rollback result validation step"""
        execution_step.status = RollbackExecutionStatus.VERIFYING
        
        try:
            # Validate that rollback was successful
            validation_result = self.integrity_validator.validate_migration_data(
                execution_result.migration_id, 
                execution_result.user_id, 
                ValidationLevel.BASIC
            )
            
            execution_step.details = {
                'validation_level': validation_result.validation_level.value,
                'is_valid': validation_result.is_valid,
                'validated_count': validation_result.validated_count,
                'failed_count': validation_result.failed_count
            }
            
            # Check if rollback was successful (no enhanced calculations should remain)
            if execution_result.scope in [RollbackScope.USER_MIGRATION, RollbackScope.CONFIGURATION, RollbackScope.FULL_SYSTEM]:
                if validation_result.validated_count > 0:
                    raise Exception(f"Rollback validation failed: {validation_result.validated_count} enhanced calculations still exist")
            
            execution_result.verification_passed = True
            self.logger.info(f"Rollback result validation passed")
            
        except Exception as e:
            raise Exception(f"Rollback result validation failed: {str(e)}")
    
    def _execute_update_migration_status_step(self, execution_step: RollbackExecutionStep, 
                                            execution_result: RollbackExecutionResult, 
                                            plan: RollbackPlan):
        """Execute migration status update step"""
        execution_step.status = RollbackExecutionStatus.EXECUTING
        
        try:
            # Update migration status to rolled back
            self._update_migration_status_to_rolled_back(
                execution_result.migration_id, execution_result.rollback_id
            )
            
            execution_step.details = {
                'migration_id': execution_result.migration_id,
                'new_status': 'rolled_back',
                'rollback_id': execution_result.rollback_id,
                'update_timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Migration status updated to rolled back")
            
        except Exception as e:
            raise Exception(f"Failed to update migration status: {str(e)}")
    
    def _create_enhanced_calculations_backup(self, migration_id: str, user_id: int, 
                                           scope: RollbackScope) -> Dict[str, Any]:
        """Create backup of enhanced calculations"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get enhanced calculations based on scope
                    if scope == RollbackScope.USER_MIGRATION:
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                        """, (user_id,))
                    elif scope == RollbackScope.CONFIGURATION:
                        # Get configuration ID from migration
                        cursor.execute("""
                            SELECT configuration_id FROM acwr_migration_history 
                            WHERE migration_id = %s
                        """, (migration_id,))
                        result = cursor.fetchone()
                        if result:
                            config_id = result['configuration_id']
                            cursor.execute("""
                                SELECT * FROM acwr_enhanced_calculations 
                                WHERE configuration_id = %s
                            """, (config_id,))
                        else:
                            return {}
                    else:  # FULL_SYSTEM
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations
                        """)
                    
                    records = cursor.fetchall()
                    
                    return {
                        'backup_timestamp': datetime.now().isoformat(),
                        'migration_id': migration_id,
                        'user_id': user_id,
                        'scope': scope.value,
                        'records': [dict(record) for record in records],
                        'record_count': len(records)
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise
    
    def _store_backup_data(self, backup_data: Dict[str, Any], rollback_id: str) -> str:
        """Store backup data and return location"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Store backup in database
                    backup_location = f"backup_{rollback_id}_{int(time.time())}"
                    
                    cursor.execute("""
                        INSERT INTO acwr_rollback_backups 
                        (backup_id, rollback_id, backup_data, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        backup_location,
                        rollback_id,
                        json.dumps(backup_data),
                        datetime.now()
                    ))
                    conn.commit()
                    
                    return backup_location
                    
        except Exception as e:
            self.logger.error(f"Error storing backup: {str(e)}")
            raise
    
    def _rollback_enhanced_calculations_batch(self, user_id: int, migration_id: str) -> int:
        """Rollback single batch of enhanced calculations"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete enhanced calculations for user (simplified batch approach)
                    cursor.execute("""
                        DELETE FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        LIMIT 1000
                    """, (user_id,))
                    
                    affected_records = cursor.rowcount
                    conn.commit()
                    
                    return affected_records
                    
        except Exception as e:
            self.logger.error(f"Error rolling back batch: {str(e)}")
            raise
    
    def _rollback_enhanced_calculations_user(self, user_id: int, migration_id: str) -> int:
        """Rollback all enhanced calculations for user"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete all enhanced calculations for user
                    cursor.execute("""
                        DELETE FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                    """, (user_id,))
                    
                    affected_records = cursor.rowcount
                    conn.commit()
                    
                    return affected_records
                    
        except Exception as e:
            self.logger.error(f"Error rolling back user calculations: {str(e)}")
            raise
    
    def _rollback_enhanced_calculations_configuration(self, config_id: int, migration_id: str) -> int:
        """Rollback all enhanced calculations for configuration"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete all enhanced calculations for configuration
                    cursor.execute("""
                        DELETE FROM acwr_enhanced_calculations 
                        WHERE configuration_id = %s
                    """, (config_id,))
                    
                    affected_records = cursor.rowcount
                    conn.commit()
                    
                    return affected_records
                    
        except Exception as e:
            self.logger.error(f"Error rolling back configuration calculations: {str(e)}")
            raise
    
    def _rollback_enhanced_calculations_full_system(self, migration_id: str) -> int:
        """Rollback all enhanced calculations"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete all enhanced calculations
                    cursor.execute("""
                        DELETE FROM acwr_enhanced_calculations
                    """)
                    
                    affected_records = cursor.rowcount
                    conn.commit()
                    
                    return affected_records
                    
        except Exception as e:
            self.logger.error(f"Error rolling back full system: {str(e)}")
            raise
    
    def _update_migration_status_to_rolled_back(self, migration_id: str, rollback_id: str):
        """Update migration status to rolled back"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Update migration status
                    cursor.execute("""
                        UPDATE acwr_migration_history 
                        SET status = 'rolled_back', 
                            rollback_id = %s,
                            rollback_timestamp = %s
                        WHERE migration_id = %s
                    """, (rollback_id, datetime.now(), migration_id))
                    
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error updating migration status: {str(e)}")
            raise
    
    def _store_execution_result(self, execution_result: RollbackExecutionResult):
        """Store rollback execution result in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_rollback_executions 
                        (rollback_id, migration_id, user_id, scope, status, start_time, end_time, 
                         total_duration, total_affected_records, backup_location, verification_passed, 
                         error_log, execution_steps, success)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        execution_result.rollback_id,
                        execution_result.migration_id,
                        execution_result.user_id,
                        execution_result.scope.value,
                        execution_result.status.value,
                        execution_result.start_time,
                        execution_result.end_time,
                        execution_result.total_duration,
                        execution_result.total_affected_records,
                        execution_result.backup_location,
                        execution_result.verification_passed,
                        json.dumps(execution_result.error_log),
                        json.dumps([asdict(step) for step in execution_result.steps]),
                        execution_result.success
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing execution result: {str(e)}")
    
    def get_rollback_execution_history(self, user_id: Optional[int] = None) -> List[RollbackExecutionResult]:
        """Get rollback execution history"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM acwr_rollback_executions 
                        WHERE ($1 IS NULL OR user_id = $1)
                        ORDER BY start_time DESC
                        LIMIT 100
                    """
                    cursor.execute(query, (user_id,))
                    results = cursor.fetchall()
                    
                    return [self._dict_to_execution_result(dict(row)) for row in results]
                    
        except Exception as e:
            self.logger.error(f"Failed to get rollback execution history: {str(e)}")
            return []
    
    def _dict_to_execution_result(self, data: Dict[str, Any]) -> RollbackExecutionResult:
        """Convert dictionary to RollbackExecutionResult"""
        return RollbackExecutionResult(
            rollback_id=data['rollback_id'],
            migration_id=data['migration_id'],
            user_id=data['user_id'],
            scope=RollbackScope(data['scope']),
            status=RollbackExecutionStatus(data['status']),
            start_time=data['start_time'],
            end_time=data['end_time'],
            total_duration=data['total_duration'],
            steps=[],  # Would need to parse from JSON
            total_affected_records=data['total_affected_records'],
            backup_location=data['backup_location'],
            verification_passed=data['verification_passed'],
            error_log=json.loads(data['error_log']) if data['error_log'] else [],
            success=data['success']
        )
    
    def get_active_rollback_executions(self) -> List[RollbackExecutionResult]:
        """Get active rollback executions"""
        return list(self.active_executions.values())
    
    def cancel_rollback_execution(self, rollback_id: str) -> bool:
        """Cancel an active rollback execution"""
        try:
            with self.execution_lock:
                if rollback_id in self.active_executions:
                    execution_result = self.active_executions[rollback_id]
                    execution_result.status = RollbackExecutionStatus.CANCELLED
                    execution_result.end_time = datetime.now()
                    execution_result.success = False
                    
                    # Move to history
                    self.execution_history.append(execution_result)
                    del self.active_executions[rollback_id]
                    
                    self.logger.info(f"Rollback execution {rollback_id} cancelled")
                    return True
                else:
                    self.logger.warning(f"Rollback execution {rollback_id} not found")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error cancelling rollback execution: {str(e)}")
            return False

