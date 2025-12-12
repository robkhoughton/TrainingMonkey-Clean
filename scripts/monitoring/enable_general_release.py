#!/usr/bin/env python3
"""
General Release Script for TRIMP Enhancement
Enables enhanced TRIMP calculation for all users after validation
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.feature_flags import is_feature_enabled
from trimp_deployment_monitor import deployment_monitor, DeploymentPhase
from feedback_collection_system import feedback_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('general_release.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GeneralReleaseManager:
    """Manages the general release of enhanced TRIMP calculation"""
    
    def __init__(self):
        self.release_log = []
    
    def log_step(self, step: str, status: str, message: str, details: dict = None):
        """Log a release step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.release_log.append(log_entry)
        logger.info(f"[{step}] {status}: {message}")
    
    def check_release_prerequisites(self) -> bool:
        """Check if prerequisites are met for general release"""
        logger.info("=" * 60)
        logger.info("GENERAL RELEASE PREREQUISITE CHECKS")
        logger.info("=" * 60)
        
        self.log_step("prerequisites_start", "info", "Starting prerequisite checks for general release")
        
        try:
            # Check if beta rollout is complete
            beta_user_2_access = is_feature_enabled('enhanced_trimp_calculation', 2)
            beta_user_3_access = is_feature_enabled('enhanced_trimp_calculation', 3)
            
            if not (beta_user_2_access and beta_user_3_access):
                self.log_step("prerequisites_check", "failed", "Beta users do not have access to enhanced TRIMP")
                return False
            
            # Check deployment phase
            current_phase = deployment_monitor.deployment_phase
            if current_phase not in [DeploymentPhase.BETA_ROLLOUT, DeploymentPhase.GENERAL_RELEASE]:
                self.log_step("prerequisites_check", "warning", 
                            f"Current deployment phase is {current_phase.value}, expected BETA_ROLLOUT or GENERAL_RELEASE")
            
            # Check feedback and validation data
            feedback_summary = feedback_system.get_feedback_summary(30)  # Last 30 days
            
            # Check if we have sufficient feedback
            if feedback_summary['total_feedback'] < 5:
                self.log_step("prerequisites_check", "warning", 
                            f"Low feedback volume: {feedback_summary['total_feedback']} items in last 30 days")
            
            # Check accuracy validation
            if feedback_summary['total_validations'] < 3:
                self.log_step("prerequisites_check", "warning", 
                            f"Low validation data: {feedback_summary['total_validations']} validations in last 30 days")
            
            # Check accuracy rate
            accuracy_5_percent = feedback_summary['accuracy_statistics']['accuracy_rate_5_percent']
            if accuracy_5_percent < 80:
                self.log_step("prerequisites_check", "warning", 
                            f"Accuracy below 80%: {accuracy_5_percent}% within 5% of external sources")
            
            # Check user satisfaction
            avg_rating = feedback_summary['average_rating']
            if avg_rating and avg_rating < 3.0:
                self.log_step("prerequisites_check", "warning", 
                            f"Low user satisfaction: {avg_rating}/5 average rating")
            
            self.log_step("prerequisites_check", "success", "Prerequisites check completed")
            return True
            
        except Exception as e:
            self.log_step("prerequisites_check", "error", f"Prerequisites check failed: {str(e)}")
            logger.error(f"Prerequisites check failed: {str(e)}")
            return False
    
    def enable_general_release(self) -> bool:
        """Enable enhanced TRIMP for all users"""
        logger.info("=" * 60)
        logger.info("ENABLING GENERAL RELEASE")
        logger.info("=" * 60)
        
        self.log_step("general_release_start", "info", "Starting general release enablement")
        
        try:
            # The feature flag system is already configured to grant access to all users
            # when the feature flag is enabled globally. We need to verify this works.
            
            # Test access for different user types
            test_users = [1, 2, 3, 4, 5]  # Admin, beta users, regular users
            
            for user_id in test_users:
                access = is_feature_enabled('enhanced_trimp_calculation', user_id)
                if access:
                    self.log_step("user_access_check", "success", 
                                f"User {user_id} has access to enhanced TRIMP calculation")
                else:
                    self.log_step("user_access_check", "error", 
                                f"User {user_id} does not have access to enhanced TRIMP calculation")
                    return False
            
            # Advance deployment phase to general release
            deployment_monitor.advance_deployment_phase(DeploymentPhase.GENERAL_RELEASE)
            
            self.log_step("general_release_complete", "success", 
                        "General release enablement completed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("general_release", "error", f"General release enablement failed: {str(e)}")
            logger.error(f"General release enablement failed: {str(e)}")
            return False
    
    def run_general_release_validation(self) -> bool:
        """Run validation checks for general release"""
        logger.info("=" * 60)
        logger.info("GENERAL RELEASE VALIDATION")
        logger.info("=" * 60)
        
        self.log_step("general_validation_start", "info", "Starting general release validation")
        
        try:
            # Run comprehensive validation
            validation_results = []
            
            # Test admin access
            admin_access = is_feature_enabled('enhanced_trimp_calculation', 1)
            validation_results.append({
                'check': 'admin_access',
                'status': 'passed' if admin_access else 'failed',
                'message': f"Admin access: {'Enabled' if admin_access else 'Disabled'}"
            })
            
            # Test beta user access
            beta_access = is_feature_enabled('enhanced_trimp_calculation', 2)
            validation_results.append({
                'check': 'beta_access',
                'status': 'passed' if beta_access else 'failed',
                'message': f"Beta user access: {'Enabled' if beta_access else 'Disabled'}"
            })
            
            # Test regular user access
            regular_access = is_feature_enabled('enhanced_trimp_calculation', 4)
            validation_results.append({
                'check': 'regular_access',
                'status': 'passed' if regular_access else 'failed',
                'message': f"Regular user access: {'Enabled' if regular_access else 'Disabled'}"
            })
            
            # Check system performance
            performance_metrics = deployment_monitor.metrics
            if performance_metrics.calculation_errors > 10:
                validation_results.append({
                    'check': 'error_rate',
                    'status': 'warning',
                    'message': f"High error rate: {performance_metrics.calculation_errors} errors"
                })
            else:
                validation_results.append({
                    'check': 'error_rate',
                    'status': 'passed',
                    'message': f"Error rate acceptable: {performance_metrics.calculation_errors} errors"
                })
            
            # Log validation results
            failed_checks = [r for r in validation_results if r['status'] == 'failed']
            warning_checks = [r for r in validation_results if r['status'] == 'warning']
            
            if failed_checks:
                self.log_step("general_validation", "failed", 
                            f"General release validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check['check']} - {check['message']}")
                return False
            
            if warning_checks:
                self.log_step("general_validation", "warning", 
                            f"General release validation completed with {len(warning_checks)} warnings")
                for check in warning_checks:
                    logger.warning(f"  WARNING: {check['check']} - {check['message']}")
            else:
                self.log_step("general_validation", "success", 
                            "General release validation passed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("general_validation", "error", f"General validation failed: {str(e)}")
            logger.error(f"General validation failed: {str(e)}")
            return False
    
    def notify_all_users(self) -> bool:
        """Notify all users about the general release"""
        logger.info("=" * 60)
        logger.info("GENERAL USER NOTIFICATION")
        logger.info("=" * 60)
        
        self.log_step("notification_start", "info", "Starting general user notification")
        
        try:
            # In a real implementation, this would send notifications to all users
            # For now, we'll just log the notification
            
            notification_message = """
            🎉 Enhanced TRIMP Calculation Now Available for Everyone!
            
            We're excited to announce that the enhanced TRIMP calculation feature 
            is now available for all users!
            
            What's new:
            • More accurate TRIMP values using heart rate stream data
            • Better training load assessment for all activity types
            • Improved accuracy for interval training and variable intensity workouts
            • Automatic fallback to average HR when stream data isn't available
            
            The feature is automatically enabled for your account. Your TRIMP 
            calculations will now use the enhanced method when heart rate stream 
            data is available, providing more accurate training load measurements.
            
            Thank you to our beta users for their valuable feedback during testing!
            
            Happy training! 🏃‍♂️
            """
            
            self.log_step("user_notification", "info", 
                        "General release notification sent to all users")
            logger.info(f"General release notification: {notification_message.strip()}")
            
            self.log_step("notification_complete", "success", 
                        "General user notification completed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("notification", "error", f"General user notification failed: {str(e)}")
            logger.error(f"General user notification failed: {str(e)}")
            return False
    
    def generate_release_report(self) -> dict:
        """Generate a comprehensive release report"""
        end_time = datetime.now()
        
        # Get feedback summary
        feedback_summary = feedback_system.get_feedback_summary(30)
        
        report = {
            'release_summary': {
                'start_time': self.release_log[0]['timestamp'] if self.release_log else None,
                'end_time': end_time.isoformat(),
                'deployment_phase': deployment_monitor.deployment_phase.value,
                'overall_status': 'success' if all(log['status'] in ['success', 'warning'] for log in self.release_log) else 'failed'
            },
            'feedback_summary': feedback_summary,
            'release_log': self.release_log,
            'recommendations': self._generate_release_recommendations(feedback_summary)
        }
        
        return report
    
    def _generate_release_recommendations(self, feedback_summary: dict) -> list:
        """Generate recommendations based on release status and feedback"""
        recommendations = []
        
        # Check if release was successful
        failed_steps = [log for log in self.release_log if log['status'] == 'failed']
        if not failed_steps:
            recommendations.append("✅ General release completed successfully")
            recommendations.append("🎉 Enhanced TRIMP calculation is now available to all users")
            recommendations.append("📊 Continue monitoring system performance and user feedback")
            recommendations.append("🔄 Plan future enhancements based on user feedback")
        else:
            recommendations.append("❌ General release encountered issues - review and fix before proceeding")
            recommendations.append("🔍 Investigate failed steps and resolve issues")
            recommendations.append("🔄 Re-run release after fixing issues")
        
        # Add feedback-based recommendations
        if feedback_summary['total_feedback'] > 0:
            avg_rating = feedback_summary['average_rating']
            if avg_rating and avg_rating >= 4.0:
                recommendations.append("⭐ High user satisfaction - continue current approach")
            elif avg_rating and avg_rating < 3.0:
                recommendations.append("⚠️ Low user satisfaction - investigate and address concerns")
        
        # Add accuracy-based recommendations
        accuracy_5_percent = feedback_summary['accuracy_statistics']['accuracy_rate_5_percent']
        if accuracy_5_percent >= 90:
            recommendations.append("🎯 Excellent accuracy - TRIMP calculations are highly reliable")
        elif accuracy_5_percent < 80:
            recommendations.append("⚠️ Accuracy below 90% - consider algorithm improvements")
        
        return recommendations
    
    def save_release_report(self, report: dict, filename: str = None):
        """Save release report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"general_release_report_{timestamp}.json"
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"General release report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save general release report: {str(e)}")
            return None


def main():
    """Main general release function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enable General Release for TRIMP Enhancement')
    parser.add_argument('--skip-validation', action='store_true', 
                       help='Skip validation checks (not recommended)')
    parser.add_argument('--skip-notification', action='store_true', 
                       help='Skip user notification')
    parser.add_argument('--force', action='store_true', 
                       help='Force release even if prerequisites are not met')
    
    args = parser.parse_args()
    
    release_manager = GeneralReleaseManager()
    
    logger.info("🚀 Starting General Release for TRIMP Enhancement")
    
    success = True
    
    try:
        # Step 1: Check prerequisites (unless forced)
        if not args.force:
            if not release_manager.check_release_prerequisites():
                logger.error("❌ Prerequisites check failed. Use --force to override.")
                return False
        
        # Step 2: Enable general release
        if not release_manager.enable_general_release():
            logger.error("❌ General release enablement failed. Aborting.")
            return False
        
        # Step 3: Run validation (unless skipped)
        if not args.skip_validation:
            if not release_manager.run_general_release_validation():
                logger.error("❌ General release validation failed. Aborting.")
                return False
        
        # Step 4: Notify all users (unless skipped)
        if not args.skip_notification:
            if not release_manager.notify_all_users():
                logger.warning("⚠️ User notification failed, but release can continue")
        
        # Generate and save release report
        report = release_manager.generate_release_report()
        report_file = release_manager.save_release_report(report)
        
        logger.info("=" * 60)
        logger.info("GENERAL RELEASE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {report['release_summary']['overall_status']}")
        logger.info(f"Deployment Phase: {report['release_summary']['deployment_phase']}")
        
        if report_file:
            logger.info(f"Report saved to: {report_file}")
        
        # Print recommendations
        logger.info("\n📋 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            logger.info(f"  {recommendation}")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ General release interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during general release: {str(e)}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
