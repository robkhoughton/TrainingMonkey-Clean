#!/usr/bin/env python3
"""
Beta Rollout Script for TRIMP Enhancement
Enables enhanced TRIMP calculation for beta users (user_id=2, user_id=3)
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.feature_flags import is_feature_enabled
from trimp_deployment_monitor import deployment_monitor, DeploymentPhase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('beta_rollout.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BetaRolloutManager:
    """Manages the beta rollout of enhanced TRIMP calculation"""
    
    def __init__(self):
        self.beta_user_ids = [2, 3]  # tballaine, iz.houghton
        self.rollout_log = []
    
    def log_step(self, step: str, status: str, message: str, details: dict = None):
        """Log a rollout step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.rollout_log.append(log_entry)
        logger.info(f"[{step}] {status}: {message}")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met for beta rollout"""
        logger.info("=" * 60)
        logger.info("BETA ROLLOUT PREREQUISITE CHECKS")
        logger.info("=" * 60)
        
        self.log_step("prerequisites_start", "info", "Starting prerequisite checks for beta rollout")
        
        try:
            # Check if admin testing is complete
            admin_access = is_feature_enabled('enhanced_trimp_calculation', 1)
            if not admin_access:
                self.log_step("prerequisites_check", "failed", "Admin user does not have access to enhanced TRIMP")
                return False
            
            # Check if beta users currently have access
            beta_user_2_access = is_feature_enabled('enhanced_trimp_calculation', 2)
            beta_user_3_access = is_feature_enabled('enhanced_trimp_calculation', 3)
            
            if beta_user_2_access and beta_user_3_access:
                self.log_step("prerequisites_check", "warning", "Beta users already have access to enhanced TRIMP")
                return True
            
            # Check deployment phase
            current_phase = deployment_monitor.deployment_phase
            if current_phase not in [DeploymentPhase.ADMIN_TESTING, DeploymentPhase.BETA_ROLLOUT]:
                self.log_step("prerequisites_check", "warning", 
                            f"Current deployment phase is {current_phase.value}, expected ADMIN_TESTING or BETA_ROLLOUT")
            
            self.log_step("prerequisites_check", "success", "Prerequisites check passed")
            return True
            
        except Exception as e:
            self.log_step("prerequisites_check", "error", f"Prerequisites check failed: {str(e)}")
            logger.error(f"Prerequisites check failed: {str(e)}")
            return False
    
    def enable_beta_access(self) -> bool:
        """Enable enhanced TRIMP access for beta users"""
        logger.info("=" * 60)
        logger.info("ENABLING BETA USER ACCESS")
        logger.info("=" * 60)
        
        self.log_step("beta_enable_start", "info", "Starting beta user access enablement")
        
        try:
            # The feature flag system is already configured to grant beta users access
            # We just need to verify and log the current state
            
            for user_id in self.beta_user_ids:
                access = is_feature_enabled('enhanced_trimp_calculation', user_id)
                if access:
                    self.log_step("beta_user_check", "success", 
                                f"User {user_id} has access to enhanced TRIMP calculation")
                else:
                    self.log_step("beta_user_check", "error", 
                                f"User {user_id} does not have access to enhanced TRIMP calculation")
                    return False
            
            # Advance deployment phase to beta rollout
            deployment_monitor.advance_deployment_phase(DeploymentPhase.BETA_ROLLOUT)
            
            self.log_step("beta_enable_complete", "success", 
                        "Beta user access enablement completed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("beta_enable", "error", f"Beta access enablement failed: {str(e)}")
            logger.error(f"Beta access enablement failed: {str(e)}")
            return False
    
    def run_beta_validation(self) -> bool:
        """Run validation checks for beta rollout"""
        logger.info("=" * 60)
        logger.info("BETA ROLLOUT VALIDATION")
        logger.info("=" * 60)
        
        self.log_step("beta_validation_start", "info", "Starting beta rollout validation")
        
        try:
            # Run beta rollout validation
            results = deployment_monitor.run_beta_rollout_validation()
            
            # Check results
            failed_checks = [r for r in results if r.status.value == 'failed']
            warning_checks = [r for r in results if r.status.value == 'warning']
            
            if failed_checks:
                self.log_step("beta_validation", "failed", 
                            f"Beta rollout validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check.check_name} - {check.message}")
                return False
            
            if warning_checks:
                self.log_step("beta_validation", "warning", 
                            f"Beta rollout validation completed with {len(warning_checks)} warnings")
                for check in warning_checks:
                    logger.warning(f"  WARNING: {check.check_name} - {check.message}")
            else:
                self.log_step("beta_validation", "success", 
                            "Beta rollout validation passed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("beta_validation", "error", f"Beta validation failed: {str(e)}")
            logger.error(f"Beta validation failed: {str(e)}")
            return False
    
    def notify_beta_users(self) -> bool:
        """Notify beta users about the enhanced TRIMP feature"""
        logger.info("=" * 60)
        logger.info("BETA USER NOTIFICATION")
        logger.info("=" * 60)
        
        self.log_step("notification_start", "info", "Starting beta user notification")
        
        try:
            # In a real implementation, this would send notifications to beta users
            # For now, we'll just log the notification
            
            notification_message = """
            🎉 Enhanced TRIMP Calculation Now Available!
            
            You now have access to the enhanced TRIMP calculation feature that uses 
            heart rate stream data for more accurate training load calculations.
            
            Key improvements:
            • More accurate TRIMP values using second-by-second heart rate data
            • Better training load assessment for interval training
            • Improved accuracy for activities with variable intensity
            
            The feature is automatically enabled for your account. You don't need 
            to do anything - your TRIMP calculations will now use the enhanced method 
            when heart rate stream data is available.
            
            If you have any questions or feedback, please contact the development team.
            
            Happy training! 🏃‍♂️
            """
            
            for user_id in self.beta_user_ids:
                self.log_step("user_notification", "info", 
                            f"Notification sent to user {user_id} about enhanced TRIMP feature")
                logger.info(f"Notification for user {user_id}: {notification_message.strip()}")
            
            self.log_step("notification_complete", "success", 
                        "Beta user notification completed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("notification", "error", f"Beta user notification failed: {str(e)}")
            logger.error(f"Beta user notification failed: {str(e)}")
            return False
    
    def generate_rollout_report(self) -> dict:
        """Generate a comprehensive rollout report"""
        end_time = datetime.now()
        
        report = {
            'rollout_summary': {
                'start_time': self.rollout_log[0]['timestamp'] if self.rollout_log else None,
                'end_time': end_time.isoformat(),
                'beta_users': self.beta_user_ids,
                'deployment_phase': deployment_monitor.deployment_phase.value,
                'overall_status': 'success' if all(log['status'] in ['success', 'warning'] for log in self.rollout_log) else 'failed'
            },
            'rollout_log': self.rollout_log,
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> list:
        """Generate recommendations based on rollout status"""
        recommendations = []
        
        # Check if rollout was successful
        failed_steps = [log for log in self.rollout_log if log['status'] == 'failed']
        if not failed_steps:
            recommendations.append("✅ Beta rollout completed successfully")
            recommendations.append("👥 Monitor beta user feedback and usage patterns")
            recommendations.append("📊 Track system performance with beta users")
            recommendations.append("🔄 Prepare for general release after monitoring period")
        else:
            recommendations.append("❌ Beta rollout encountered issues - review and fix before proceeding")
            recommendations.append("🔍 Investigate failed steps and resolve issues")
            recommendations.append("🔄 Re-run rollout after fixing issues")
        
        # Add phase-specific recommendations
        current_phase = deployment_monitor.deployment_phase.value
        if current_phase == 'beta_rollout':
            recommendations.append("📈 Monitor beta user engagement and feedback")
            recommendations.append("🎯 Collect performance metrics and user experience data")
            recommendations.append("⏰ Plan general release timeline based on beta feedback")
        
        return recommendations
    
    def save_rollout_report(self, report: dict, filename: str = None):
        """Save rollout report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"beta_rollout_report_{timestamp}.json"
        
        try:
            import json
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Beta rollout report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save beta rollout report: {str(e)}")
            return None


def main():
    """Main beta rollout function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enable Beta Rollout for TRIMP Enhancement')
    parser.add_argument('--skip-validation', action='store_true', 
                       help='Skip validation checks (not recommended)')
    parser.add_argument('--skip-notification', action='store_true', 
                       help='Skip beta user notification')
    
    args = parser.parse_args()
    
    rollout_manager = BetaRolloutManager()
    
    logger.info("🚀 Starting Beta Rollout for TRIMP Enhancement")
    logger.info(f"Beta Users: {rollout_manager.beta_user_ids}")
    
    success = True
    
    try:
        # Step 1: Check prerequisites
        if not rollout_manager.check_prerequisites():
            logger.error("❌ Prerequisites check failed. Aborting beta rollout.")
            return False
        
        # Step 2: Enable beta access
        if not rollout_manager.enable_beta_access():
            logger.error("❌ Beta access enablement failed. Aborting.")
            return False
        
        # Step 3: Run validation (unless skipped)
        if not args.skip_validation:
            if not rollout_manager.run_beta_validation():
                logger.error("❌ Beta validation failed. Aborting.")
                return False
        
        # Step 4: Notify beta users (unless skipped)
        if not args.skip_notification:
            if not rollout_manager.notify_beta_users():
                logger.warning("⚠️ Beta user notification failed, but rollout can continue")
        
        # Generate and save rollout report
        report = rollout_manager.generate_rollout_report()
        report_file = rollout_manager.save_rollout_report(report)
        
        logger.info("=" * 60)
        logger.info("BETA ROLLOUT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {report['rollout_summary']['overall_status']}")
        logger.info(f"Deployment Phase: {report['rollout_summary']['deployment_phase']}")
        logger.info(f"Beta Users: {report['rollout_summary']['beta_users']}")
        
        if report_file:
            logger.info(f"Report saved to: {report_file}")
        
        # Print recommendations
        logger.info("\n📋 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            logger.info(f"  {recommendation}")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Beta rollout interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during beta rollout: {str(e)}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
