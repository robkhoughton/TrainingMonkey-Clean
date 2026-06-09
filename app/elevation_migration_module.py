"""
Elevation Migration Module
Your Training Monkey - Integrated with existing app infrastructure

Migrates from 1000ft = 1 mile to 750ft = 1 mile conversion factor
Uses existing db_utils connection for reliability.
"""

import db_utils
from datetime import datetime, timedelta
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# Configuration
OLD_CONVERSION_FACTOR = 850.0  # Current factor
NEW_CONVERSION_FACTOR = 750.0  # Research-optimized factor


class ElevationMigrationService:
    """Service for elevation factor migration"""

    def __init__(self):
        self.results = {
            'total_activities': 0,
            'elevation_activities': 0,
            'updated_activities': 0,
            'updated_users': 0,
            'validation_passed': False,
            'errors': [],
            'warnings': [],
            'sample_calculations': []
        }

    def calculate_new_elevation_load(self, elevation_feet):
        """Calculate elevation load using new 750ft factor"""
        if elevation_feet is None or elevation_feet == 0:
            return 0.0
        return float(Decimal(str(elevation_feet)) / Decimal(str(NEW_CONVERSION_FACTOR)))

    def validate_current_data(self):
        """Validate current data state before migration"""
        try:
            logger.info("Starting pre-migration validation")

            # Database is PostgreSQL only

            # Check activities with elevation data by user
            result = db_utils.execute_query("""
                SELECT 
                    user_id,
                    COUNT(*) as total_activities,
                    COUNT(CASE WHEN elevation_gain_feet > 0 THEN 1 END) as elevation_activities,
                    AVG(elevation_gain_feet) as avg_elevation,
                    MAX(elevation_gain_feet) as max_elevation
                FROM activities 
                WHERE user_id IS NOT NULL
                GROUP BY user_id
                ORDER BY user_id
            """, fetch=True)

            if not result:
                self.results['errors'].append("No activities found in database")
                return False

            # Summarize data
            total_activities = 0
            total_elevation_activities = 0

            for row in result:
                user_summary = {
                    'user_id': row['user_id'],
                    'total_activities': row['total_activities'],
                    'elevation_activities': row['elevation_activities'],
                    'avg_elevation': float(row['avg_elevation']) if row['avg_elevation'] else 0,
                    'max_elevation': float(row['max_elevation']) if row['max_elevation'] else 0
                }
                self.results['sample_calculations'].append(user_summary)

                total_activities += row['total_activities']
                total_elevation_activities += row['elevation_activities']

            self.results['total_activities'] = total_activities
            self.results['elevation_activities'] = total_elevation_activities

            # Get sample calculations
            sample_result = db_utils.execute_query("""
                SELECT 
                    user_id,
                    activity_id,
                    elevation_gain_feet,
                    elevation_load_miles,
                    total_load_miles,
                    distance_miles
                FROM activities 
                WHERE elevation_gain_feet > 0 
                AND elevation_load_miles IS NOT NULL
                ORDER BY elevation_gain_feet DESC
                LIMIT 5
            """, fetch=True)

            # Calculate before/after examples
            for row in sample_result:
                current_elevation_load = row['elevation_load_miles']
                new_elevation_load = self.calculate_new_elevation_load(row['elevation_gain_feet'])

                sample = {
                    'user_id': row['user_id'],
                    'activity_id': row['activity_id'],
                    'elevation_feet': row['elevation_gain_feet'],
                    'current_load': current_elevation_load,
                    'new_load': new_elevation_load,
                    'percent_increase': ((
                                                     new_elevation_load / current_elevation_load - 1) * 100) if current_elevation_load > 0 else 0,
                    'distance_miles': row['distance_miles']
                }
                self.results['sample_calculations'].append(sample)

            logger.info(f"Validation complete: {total_activities} total, {total_elevation_activities} with elevation")
            return True

        except Exception as e:
            error_msg = f"Data validation failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False

    def update_activities_elevation_loads(self, dry_run=True):
        """Update all activities with new elevation load calculations"""
        try:
            logger.info(f"Starting elevation load update (dry_run={dry_run})")

            # Get all activities with elevation data
            activities = db_utils.execute_query("""
                SELECT activity_id, user_id, elevation_gain_feet, distance_miles
                FROM activities 
                WHERE elevation_gain_feet IS NOT NULL
                ORDER BY user_id, activity_id
            """, fetch=True)

            total_updates = len(activities)
            logger.info(f"Found {total_updates} activities to update")

            if total_updates == 0:
                self.results['warnings'].append("No activities found to update")
                return True

            updated_count = 0

            for activity in activities:
                try:
                    # Calculate new elevation load and total load
                    new_elevation_load = self.calculate_new_elevation_load(activity['elevation_gain_feet'])
                    new_total_load = (activity['distance_miles'] or 0.0) + new_elevation_load

                    if not dry_run:
                        # Update the activity record
                        db_utils.execute_query("""
                            UPDATE activities 
                            SET 
                                elevation_load_miles = %s,
                                total_load_miles = %s
                            WHERE activity_id = %s AND user_id = %s
                        """, (new_elevation_load, new_total_load, activity['activity_id'], activity['user_id']))

                    updated_count += 1

                except Exception as e:
                    error_msg = f"Failed to update activity {activity['activity_id']}: {str(e)}"
                    logger.error(error_msg)
                    self.results['errors'].append(error_msg)
                    continue

            self.results['updated_activities'] = updated_count
            logger.info(f"Elevation load update complete: {updated_count}/{total_updates} activities")
            return updated_count == total_updates

        except Exception as e:
            error_msg = f"Failed to update elevation loads: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False

    def recalculate_acwr_values(self, dry_run=True):
        """Recalculate ACWR values for all users with updated elevation loads"""
        try:
            logger.info(f"Starting ACWR recalculation (dry_run={dry_run})")

            # Get all users with activities
            users = db_utils.execute_query("""
                SELECT DISTINCT user_id 
                FROM activities 
                WHERE user_id IS NOT NULL
                ORDER BY user_id
            """, fetch=True)

            user_ids = [row['user_id'] for row in users]
            logger.info(f"Recalculating ACWR for {len(user_ids)} users")

            updated_users = 0
            for user_id in user_ids:
                success = self.recalculate_user_acwr(user_id, dry_run)
                if success:
                    updated_users += 1
                else:
                    self.results['warnings'].append(f"ACWR recalculation failed for user {user_id}")

            self.results['updated_users'] = updated_users
            logger.info(f"ACWR recalculation complete: {updated_users}/{len(user_ids)} users")
            return updated_users == len(user_ids)

        except Exception as e:
            error_msg = f"ACWR recalculation failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False

    def recalculate_user_acwr(self, user_id, dry_run=True):
        """Recalculate ACWR values for a specific user"""
        try:
            # Get all activities for user in chronological order
            activities = db_utils.execute_query("""
                SELECT activity_id, date, total_load_miles, trimp
                FROM activities 
                WHERE user_id = %s
                ORDER BY date ASC
            """, (user_id,), fetch=True)

            if len(activities) == 0:
                return True

            # Process each activity to calculate rolling windows
            for i, activity in enumerate(activities):
                activity_date = datetime.strptime(activity['date'], '%Y-%m-%d').date() if isinstance(activity['date'],
                                                                                                     str) else activity[
                    'date']

                # Calculate 7-day acute window (current day + 6 previous days)
                acute_start = activity_date - timedelta(days=6)
                acute_activities = [a for a in activities[:i + 1]
                                    if (datetime.strptime(a['date'], '%Y-%m-%d').date() if isinstance(a['date'],
                                                                                                      str) else a[
                        'date']) >= acute_start]

                # Calculate 28-day chronic window (days -27 to -7 before current)
                chronic_start = activity_date - timedelta(days=27)
                chronic_end = activity_date - timedelta(days=7)
                chronic_activities = [a for a in activities[:i + 1]
                                      if chronic_start <= (
                                          datetime.strptime(a['date'], '%Y-%m-%d').date() if isinstance(a['date'],
                                                                                                        str) else a[
                                              'date']) <= chronic_end]

                # Calculate averages
                acute_external_load = sum(a['total_load_miles'] or 0 for a in acute_activities) / 7.0
                acute_internal_load = sum(a['trimp'] or 0 for a in acute_activities) / 7.0

                chronic_external_load = (sum(a['total_load_miles'] or 0 for a in chronic_activities) / 21.0
                                         if len(chronic_activities) > 0 else acute_external_load)
                chronic_internal_load = (sum(a['trimp'] or 0 for a in chronic_activities) / 21.0
                                         if len(chronic_activities) > 0 else acute_internal_load)

                # Calculate ACWR ratios
                external_acwr = acute_external_load / chronic_external_load if chronic_external_load > 0 else 0
                internal_acwr = acute_internal_load / chronic_internal_load if chronic_internal_load > 0 else 0

                # Calculate normalized divergence
                normalized_divergence = self.calculate_normalized_divergence(external_acwr, internal_acwr)

                if not dry_run:
                    # Update activity with new calculations
                    db_utils.execute_query("""
                        UPDATE activities 
                        SET 
                            seven_day_avg_load = %s,
                            twentyeight_day_avg_load = %s,
                            seven_day_avg_trimp = %s,
                            twentyeight_day_avg_trimp = %s,
                            acute_chronic_ratio = %s,
                            trimp_acute_chronic_ratio = %s,
                            normalized_divergence = %s
                        WHERE activity_id = %s AND user_id = %s
                    """, (
                        acute_external_load, chronic_external_load,
                        acute_internal_load, chronic_internal_load,
                        external_acwr, internal_acwr, normalized_divergence,
                        activity['activity_id'], user_id
                    ))

            return True

        except Exception as e:
            logger.error(f"Failed to recalculate ACWR for user {user_id}: {str(e)}")
            return False

    def calculate_normalized_divergence(self, external_acwr, internal_acwr):
        """Calculate normalized divergence using established formula"""
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

        except Exception:
            return None

    def validate_migration_results(self):
        """Validate migration results"""
        try:
            logger.info("Validating migration results")

            # Check sample calculations with new factor
            result = db_utils.execute_query("""
                SELECT 
                    user_id,
                    activity_id,
                    elevation_gain_feet,
                    elevation_load_miles,
                    total_load_miles,
                    distance_miles
                FROM activities 
                WHERE elevation_gain_feet > 0 
                AND elevation_load_miles IS NOT NULL
                ORDER BY elevation_gain_feet DESC
                LIMIT 5
            """, fetch=True)

            validation_passed = True

            for row in result:
                expected_elevation_load = row['elevation_gain_feet'] / NEW_CONVERSION_FACTOR
                expected_total_load = (row['distance_miles'] or 0) + expected_elevation_load

                elevation_match = abs(row['elevation_load_miles'] - expected_elevation_load) < 0.001
                total_match = abs(row['total_load_miles'] - expected_total_load) < 0.001

                if not (elevation_match and total_match):
                    validation_passed = False
                    self.results['errors'].append(f"Validation failed for activity {row['activity_id']}")

            self.results['validation_passed'] = validation_passed
            return validation_passed

        except Exception as e:
            error_msg = f"Migration validation failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False

    def run_migration(self, dry_run=True):
        """Execute complete migration process"""
        logger.info(f"Starting elevation factor migration (dry_run={dry_run})")

        try:
            # Step 1: Validate current data
            if not self.validate_current_data():
                self.results['errors'].append("Data validation failed")
                return False

            # Step 2: Update elevation loads
            if not self.update_activities_elevation_loads(dry_run):
                self.results['errors'].append("Elevation load update failed")
                return False

            # Step 3: Recalculate ACWR values
            if not self.recalculate_acwr_values(dry_run):
                self.results['errors'].append("ACWR recalculation failed")
                return False

            # Step 4: Validate results (only for live migration)
            if not dry_run:
                if not self.validate_migration_results():
                    self.results['errors'].append("Migration validation failed")
                    return False

            logger.info("Migration completed successfully")
            return True

        except Exception as e:
            error_msg = f"Migration failed: {str(e)}"
            logger.error(error_msg)
            self.results['errors'].append(error_msg)
            return False

    def get_results(self):
        """Get migration results"""
        return self.results


def run_elevation_migration(dry_run=True):
    """Main function to run elevation migration"""
    migration_service = ElevationMigrationService()
    success = migration_service.run_migration(dry_run)
    return success, migration_service.get_results()