#!/usr/bin/env python3
"""
ACWR Migration Data Integrity and Rollback System
Handles data integrity validation during migration and provides rollback capabilities
"""

import logging
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psycopg2
from psycopg2.extras import RealDictCursor

import db_utils

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Data validation levels"""
    BASIC = "basic"           # Basic data type and constraint validation
    STANDARD = "standard"     # Standard validation with business rules
    STRICT = "strict"         # Strict validation with comprehensive checks
    PARANOID = "paranoid"     # Paranoid validation with cross-references

class RollbackScope(Enum):
    """Rollback scope options"""
    SINGLE_BATCH = "single_batch"     # Rollback single batch
    USER_MIGRATION = "user_migration" # Rollback entire user migration
    CONFIGURATION = "configuration"   # Rollback all migrations for configuration
    FULL_SYSTEM = "full_system"       # Rollback all enhanced calculations

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    validation_level: ValidationLevel
    errors: List[str]
    warnings: List[str]
    validated_count: int
    failed_count: int
    validation_time: float
    checksum: Optional[str] = None

@dataclass
class IntegrityCheckpoint:
    """Data integrity checkpoint"""
    checkpoint_id: str
    migration_id: str
    user_id: int
    batch_id: Optional[int]
    timestamp: datetime
    validation_result: ValidationResult
    data_snapshot: Dict[str, Any]
    checksum: str
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

class ACWRMigrationIntegrityValidator:
    """Data integrity validator for migration operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_lock = threading.Lock()
        
        # Validation rules
        self.validation_rules = {
            ValidationLevel.BASIC: self._basic_validation,
            ValidationLevel.STANDARD: self._standard_validation,
            ValidationLevel.STRICT: self._strict_validation,
            ValidationLevel.PARANOID: self._paranoid_validation
        }
    
    def validate_migration_data(self, migration_id: str, user_id: int, 
                               validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """Validate data integrity for a migration"""
        start_time = time.time()
        errors = []
        warnings = []
        validated_count = 0
        failed_count = 0
        
        try:
            with self.validation_lock:
                self.logger.info(f"Starting data validation for migration {migration_id} at {validation_level.value} level")
                
                # Get validation function
                validation_func = self.validation_rules.get(validation_level)
                if not validation_func:
                    raise ValueError(f"Unknown validation level: {validation_level}")
                
                # Perform validation
                result = validation_func(migration_id, user_id)
                errors.extend(result.get('errors', []))
                warnings.extend(result.get('warnings', []))
                validated_count += result.get('validated_count', 0)
                failed_count += result.get('failed_count', 0)
                
                # Calculate checksum
                checksum = self._calculate_data_checksum(migration_id, user_id)
                
                validation_time = time.time() - start_time
                is_valid = len(errors) == 0
                
                validation_result = ValidationResult(
                    is_valid=is_valid,
                    validation_level=validation_level,
                    errors=errors,
                    warnings=warnings,
                    validated_count=validated_count,
                    failed_count=failed_count,
                    validation_time=validation_time,
                    checksum=checksum
                )
                
                self.logger.info(f"Data validation completed for migration {migration_id}: "
                               f"{'VALID' if is_valid else 'INVALID'} "
                               f"({validated_count} validated, {failed_count} failed, {len(warnings)} warnings)")
                
                return validation_result
                
        except Exception as e:
            self.logger.error(f"Error during data validation: {str(e)}")
            return ValidationResult(
                is_valid=False,
                validation_level=validation_level,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                validated_count=0,
                failed_count=1,
                validation_time=time.time() - start_time
            )
    
    def _basic_validation(self, migration_id: str, user_id: int) -> Dict[str, Any]:
        """Basic data validation"""
        errors = []
        warnings = []
        validated_count = 0
        failed_count = 0
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check enhanced calculations exist
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                    """, (user_id,))
                    result = cursor.fetchone()
                    enhanced_count = result['count'] if result else 0
                    
                    if enhanced_count == 0:
                        errors.append(f"No enhanced calculations found for user {user_id}")
                        failed_count += 1
                    else:
                        validated_count += enhanced_count
                    
                    # Check for null values in critical fields
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s 
                        AND (acwr_ratio IS NULL OR acute_load IS NULL OR chronic_load IS NULL)
                    """, (user_id,))
                    result = cursor.fetchone()
                    null_count = result['count'] if result else 0
                    
                    if null_count > 0:
                        errors.append(f"Found {null_count} records with null values in critical fields")
                        failed_count += null_count
                        validated_count -= null_count
                    
                    # Check for invalid ACWR ratios
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s 
                        AND (acwr_ratio < 0 OR acwr_ratio > 10)
                    """, (user_id,))
                    result = cursor.fetchone()
                    invalid_ratio_count = result['count'] if result else 0
                    
                    if invalid_ratio_count > 0:
                        warnings.append(f"Found {invalid_ratio_count} records with ACWR ratios outside normal range (0-10)")
                    
                    # Check for negative loads
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s 
                        AND (acute_load < 0 OR chronic_load < 0)
                    """, (user_id,))
                    result = cursor.fetchone()
                    negative_load_count = result['count'] if result else 0
                    
                    if negative_load_count > 0:
                        errors.append(f"Found {negative_load_count} records with negative load values")
                        failed_count += negative_load_count
                        validated_count -= negative_load_count
                    
        except Exception as e:
            errors.append(f"Database error during basic validation: {str(e)}")
            failed_count += 1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'validated_count': validated_count,
            'failed_count': failed_count
        }
    
    def _standard_validation(self, migration_id: str, user_id: int) -> Dict[str, Any]:
        """Standard validation with business rules"""
        result = self._basic_validation(migration_id, user_id)
        errors = result['errors']
        warnings = result['warnings']
        validated_count = result['validated_count']
        failed_count = result['failed_count']
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check for duplicate calculations
                    cursor.execute("""
                        SELECT activity_id, configuration_id, COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        GROUP BY activity_id, configuration_id
                        HAVING COUNT(*) > 1
                    """, (user_id,))
                    duplicates = cursor.fetchall()
                    
                    if duplicates:
                        duplicate_count = sum(dup['count'] for dup in duplicates)
                        errors.append(f"Found {len(duplicates)} duplicate calculation groups with {duplicate_count} total records")
                        failed_count += duplicate_count
                        validated_count -= duplicate_count
                    
                    # Check for orphaned records (activities that don't exist)
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations eec
                        LEFT JOIN activities a ON eec.activity_id = a.activity_id
                        WHERE eec.user_id = %s AND a.activity_id IS NULL
                    """, (user_id,))
                    result = cursor.fetchone()
                    orphaned_count = result['count'] if result else 0
                    
                    if orphaned_count > 0:
                        errors.append(f"Found {orphaned_count} orphaned calculation records")
                        failed_count += orphaned_count
                        validated_count -= orphaned_count
                    
                    # Check for configuration consistency
                    cursor.execute("""
                        SELECT DISTINCT configuration_id
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                    """, (user_id,))
                    configs = cursor.fetchall()
                    
                    for config in configs:
                        config_id = config['configuration_id']
                        cursor.execute("""
                            SELECT COUNT(*) as count
                            FROM acwr_configurations 
                            WHERE id = %s AND is_active = true
                        """, (config_id,))
                        result = cursor.fetchone()
                        if not result or result['count'] == 0:
                            errors.append(f"Configuration {config_id} is not active or does not exist")
                    
                    # Check for reasonable ACWR progression
                    cursor.execute("""
                        SELECT activity_id, acwr_ratio, calculation_date
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        ORDER BY calculation_date ASC
                        LIMIT 100
                    """, (user_id,))
                    recent_calculations = cursor.fetchall()
                    
                    if len(recent_calculations) > 10:
                        # Check for extreme ACWR changes
                        extreme_changes = 0
                        for i in range(1, len(recent_calculations)):
                            prev_ratio = recent_calculations[i-1]['acwr_ratio']
                            curr_ratio = recent_calculations[i]['acwr_ratio']
                            if prev_ratio and curr_ratio:
                                change = abs(curr_ratio - prev_ratio)
                                if change > 2.0:  # More than 2.0 ACWR change
                                    extreme_changes += 1
                        
                        if extreme_changes > len(recent_calculations) * 0.1:  # More than 10% extreme changes
                            warnings.append(f"Found {extreme_changes} extreme ACWR changes in recent calculations")
                    
        except Exception as e:
            errors.append(f"Database error during standard validation: {str(e)}")
            failed_count += 1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'validated_count': validated_count,
            'failed_count': failed_count
        }
    
    def _strict_validation(self, migration_id: str, user_id: int) -> Dict[str, Any]:
        """Strict validation with comprehensive checks"""
        result = self._standard_validation(migration_id, user_id)
        errors = result['errors']
        warnings = result['warnings']
        validated_count = result['validated_count']
        failed_count = result['failed_count']
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Check for data consistency across configurations
                    cursor.execute("""
                        SELECT configuration_id, COUNT(*) as count, 
                               AVG(acwr_ratio) as avg_acwr, 
                               MIN(acwr_ratio) as min_acwr, 
                               MAX(acwr_ratio) as max_acwr
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        GROUP BY configuration_id
                    """, (user_id,))
                    config_stats = cursor.fetchall()
                    
                    if len(config_stats) > 1:
                        # Check for reasonable differences between configurations
                        for i in range(len(config_stats)):
                            for j in range(i+1, len(config_stats)):
                                config1 = config_stats[i]
                                config2 = config_stats[j]
                                
                                avg_diff = abs(config1['avg_acwr'] - config2['avg_acwr'])
                                if avg_diff > 1.0:  # More than 1.0 ACWR difference
                                    warnings.append(f"Large ACWR difference between configurations "
                                                  f"{config1['configuration_id']} and {config2['configuration_id']}: "
                                                  f"{avg_diff:.2f}")
                    
                    # Check for temporal consistency
                    cursor.execute("""
                        SELECT calculation_date, COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        GROUP BY calculation_date
                        ORDER BY calculation_date
                    """, (user_id,))
                    daily_counts = cursor.fetchall()
                    
                    if len(daily_counts) > 1:
                        # Check for unusual daily calculation counts
                        counts = [dc['count'] for dc in daily_counts]
                        avg_count = sum(counts) / len(counts)
                        for dc in daily_counts:
                            if dc['count'] > avg_count * 3:  # More than 3x average
                                warnings.append(f"Unusual calculation count on {dc['calculation_date']}: "
                                              f"{dc['count']} (avg: {avg_count:.1f})")
                    
                    # Check for calculation method consistency
                    cursor.execute("""
                        SELECT calculation_method, COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        GROUP BY calculation_method
                    """, (user_id,))
                    method_counts = cursor.fetchall()
                    
                    non_enhanced = [mc for mc in method_counts if mc['calculation_method'] != 'enhanced']
                    if non_enhanced:
                        method_strings = [f"{mc['calculation_method']}: {mc['count']}" for mc in non_enhanced]
                        warnings.append(f"Found calculations with non-enhanced methods: "
                                      f"{', '.join(method_strings)}")
                    
        except Exception as e:
            errors.append(f"Database error during strict validation: {str(e)}")
            failed_count += 1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'validated_count': validated_count,
            'failed_count': failed_count
        }
    
    def _paranoid_validation(self, migration_id: str, user_id: int) -> Dict[str, Any]:
        """Paranoid validation with cross-references"""
        result = self._strict_validation(migration_id, user_id)
        errors = result['errors']
        warnings = result['warnings']
        validated_count = result['validated_count']
        failed_count = result['failed_count']
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Cross-reference with original activities
                    cursor.execute("""
                        SELECT eec.activity_id, eec.acwr_ratio, a.trimp_score
                        FROM acwr_enhanced_calculations eec
                        JOIN activities a ON eec.activity_id = a.activity_id
                        WHERE eec.user_id = %s
                        ORDER BY eec.calculation_date DESC
                        LIMIT 50
                    """, (user_id,))
                    cross_ref_data = cursor.fetchall()
                    
                    # Check for reasonable ACWR to TRIMP relationships
                    unreasonable_ratios = 0
                    for record in cross_ref_data:
                        acwr_ratio = record['acwr_ratio']
                        trimp_score = record['trimp_score']
                        
                        if acwr_ratio and trimp_score:
                            # Very rough sanity check: ACWR should be somewhat related to TRIMP
                            if trimp_score > 0:
                                # This is a very basic check - in reality, ACWR depends on many factors
                                if acwr_ratio > 5.0 and trimp_score < 10:  # High ACWR with low TRIMP
                                    unreasonable_ratios += 1
                                elif acwr_ratio < 0.5 and trimp_score > 100:  # Low ACWR with high TRIMP
                                    unreasonable_ratios += 1
                    
                    if unreasonable_ratios > len(cross_ref_data) * 0.2:  # More than 20% unreasonable
                        warnings.append(f"Found {unreasonable_ratios} potentially unreasonable ACWR/TRIMP relationships")
                    
                    # Check for data integrity with migration history
                    cursor.execute("""
                        SELECT mh.migration_id, mh.successful_calculations, mh.failed_calculations
                        FROM acwr_migration_history mh
                        WHERE mh.user_id = %s
                        ORDER BY mh.start_time DESC
                        LIMIT 5
                    """, (user_id,))
                    migration_history = cursor.fetchall()
                    
                    if migration_history:
                        latest_migration = migration_history[0]
                        expected_successful = latest_migration['successful_calculations']
                        
                        cursor.execute("""
                            SELECT COUNT(*) as count
                            FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                        """, (user_id,))
                        result = cursor.fetchone()
                        actual_count = result['count'] if result else 0
                        
                        if abs(actual_count - expected_successful) > 10:  # Allow 10 record difference
                            warnings.append(f"Migration history shows {expected_successful} successful calculations, "
                                          f"but found {actual_count} enhanced calculation records")
                    
        except Exception as e:
            errors.append(f"Database error during paranoid validation: {str(e)}")
            failed_count += 1
        
        return {
            'errors': errors,
            'warnings': warnings,
            'validated_count': validated_count,
            'failed_count': failed_count
        }
    
    def _calculate_data_checksum(self, migration_id: str, user_id: int) -> str:
        """Calculate checksum for data integrity verification"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT activity_id, configuration_id, acwr_ratio, acute_load, chronic_load, calculation_date
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        ORDER BY activity_id, configuration_id
                    """, (user_id,))
                    records = cursor.fetchall()
                    
                    # Create checksum from record data
                    data_string = json.dumps([dict(record) for record in records], sort_keys=True)
                    checksum = hashlib.sha256(data_string.encode()).hexdigest()
                    
                    return checksum
                    
        except Exception as e:
            self.logger.error(f"Error calculating checksum: {str(e)}")
            return ""
    
    def create_integrity_checkpoint(self, migration_id: str, user_id: int, 
                                   batch_id: Optional[int] = None) -> IntegrityCheckpoint:
        """Create an integrity checkpoint"""
        try:
            checkpoint_id = f"checkpoint_{migration_id}_{int(time.time())}"
            
            # Perform validation
            validation_result = self.validate_migration_data(migration_id, user_id, ValidationLevel.STANDARD)
            
            # Create data snapshot
            data_snapshot = self._create_data_snapshot(migration_id, user_id, batch_id)
            
            # Calculate checksum
            checksum = self._calculate_data_checksum(migration_id, user_id)
            
            # Create rollback data
            rollback_data = self._create_rollback_data(migration_id, user_id, batch_id)
            
            checkpoint = IntegrityCheckpoint(
                checkpoint_id=checkpoint_id,
                migration_id=migration_id,
                user_id=user_id,
                batch_id=batch_id,
                timestamp=datetime.now(),
                validation_result=validation_result,
                data_snapshot=data_snapshot,
                checksum=checksum,
                rollback_data=rollback_data
            )
            
            # Store checkpoint
            self._store_checkpoint(checkpoint)
            
            self.logger.info(f"Created integrity checkpoint {checkpoint_id} for migration {migration_id}")
            return checkpoint
            
        except Exception as e:
            self.logger.error(f"Error creating integrity checkpoint: {str(e)}")
            raise
    
    def _create_data_snapshot(self, migration_id: str, user_id: int, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a snapshot of current data state"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get enhanced calculations count
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                    """, (user_id,))
                    result = cursor.fetchone()
                    enhanced_count = result['count'] if result else 0
                    
                    # Get configuration usage
                    cursor.execute("""
                        SELECT configuration_id, COUNT(*) as count
                        FROM acwr_enhanced_calculations 
                        WHERE user_id = %s
                        GROUP BY configuration_id
                    """, (user_id,))
                    config_usage = cursor.fetchall()
                    
                    return {
                        'enhanced_calculations_count': enhanced_count,
                        'configuration_usage': [dict(cu) for cu in config_usage],
                        'snapshot_timestamp': datetime.now().isoformat(),
                        'migration_id': migration_id,
                        'user_id': user_id,
                        'batch_id': batch_id
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating data snapshot: {str(e)}")
            return {}
    
    def _create_rollback_data(self, migration_id: str, user_id: int, batch_id: Optional[int] = None) -> Dict[str, Any]:
        """Create rollback data for potential restoration"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get enhanced calculations to rollback
                    if batch_id:
                        # For batch rollback, we need to identify which records belong to this batch
                        # This is a simplified approach - in practice, you'd track batch membership
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                            ORDER BY calculation_date DESC
                            LIMIT 1000
                        """, (user_id,))
                    else:
                        cursor.execute("""
                            SELECT * FROM acwr_enhanced_calculations 
                            WHERE user_id = %s
                        """, (user_id,))
                    
                    records = cursor.fetchall()
                    
                    return {
                        'records_to_rollback': [dict(record) for record in records],
                        'rollback_timestamp': datetime.now().isoformat(),
                        'migration_id': migration_id,
                        'user_id': user_id,
                        'batch_id': batch_id
                    }
                    
        except Exception as e:
            self.logger.error(f"Error creating rollback data: {str(e)}")
            return {}
    
    def _store_checkpoint(self, checkpoint: IntegrityCheckpoint):
        """Store integrity checkpoint in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_integrity_checkpoints 
                        (checkpoint_id, migration_id, user_id, batch_id, timestamp, 
                         validation_result, data_snapshot, checksum, rollback_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        checkpoint.checkpoint_id,
                        checkpoint.migration_id,
                        checkpoint.user_id,
                        checkpoint.batch_id,
                        checkpoint.timestamp,
                        json.dumps(asdict(checkpoint.validation_result)),
                        json.dumps(checkpoint.data_snapshot),
                        checkpoint.checksum,
                        json.dumps(checkpoint.rollback_data)
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing checkpoint: {str(e)}")
            raise
