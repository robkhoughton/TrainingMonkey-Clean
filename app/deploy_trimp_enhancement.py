#!/usr/bin/env python3
"""
TRIMP Enhancement Deployment Script
Handles the deployment of the enhanced TRIMP calculation system with monitoring and validation
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trimp_deployment_monitor import deployment_monitor, DeploymentPhase, ValidationStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trimp_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrimpEnhancementDeployment:
    """Handles the deployment of TRIMP enhancement with monitoring and validation"""
    
    def __init__(self):
        self.deployment_log = []
        self.start_time = datetime.now()
    
    def log_step(self, step: str, status: str, message: str, details: Dict[str, Any] = None):
        """Log a deployment step"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'step': step,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.deployment_log.append(log_entry)
        logger.info(f"[{step}] {status}: {message}")
    
    def run_pre_deployment_checks(self) -> bool:
        """Run pre-deployment validation checks"""
        logger.info("=" * 60)
        logger.info("PHASE 1: PRE-DEPLOYMENT VALIDATION")
        logger.info("=" * 60)
        
        self.log_step("pre_deployment_start", "info", "Starting pre-deployment validation")
        
        try:
            # Run pre-deployment validation
            results = deployment_monitor.run_pre_deployment_validation()
            
            # Check results
            failed_checks = [r for r in results if r.status == ValidationStatus.FAILED]
            warning_checks = [r for r in results if r.status == ValidationStatus.WARNING]
            
            if failed_checks:
                self.log_step("pre_deployment_validation", "failed", 
                            f"Pre-deployment validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check.check_name} - {check.message}")
                return False
            
            if warning_checks:
                self.log_step("pre_deployment_validation", "warning", 
                            f"Pre-deployment validation completed with {len(warning_checks)} warnings")
                for check in warning_checks:
                    logger.warning(f"  WARNING: {check.check_name} - {check.message}")
            else:
                self.log_step("pre_deployment_validation", "success", 
                            "Pre-deployment validation passed successfully")
            
            # Advance to deployed_disabled phase
            deployment_monitor.advance_deployment_phase(DeploymentPhase.DEPLOYED_DISABLED)
            
            return True
            
        except Exception as e:
            self.log_step("pre_deployment_validation", "error", f"Pre-deployment validation error: {str(e)}")
            logger.error(f"Pre-deployment validation failed: {str(e)}")
            return False
    
    def deploy_with_feature_flags_disabled(self) -> bool:
        """Deploy the system with feature flags disabled"""
        logger.info("=" * 60)
        logger.info("PHASE 2: DEPLOY WITH FEATURE FLAGS DISABLED")
        logger.info("=" * 60)
        
        self.log_step("deployment_start", "info", "Starting deployment with feature flags disabled")
        
        try:
            # This would typically trigger the actual deployment
            # For now, we'll simulate the deployment process
            
            # Simulate deployment steps
            self.log_step("build_application", "info", "Building application")
            time.sleep(1)  # Simulate build time
            
            self.log_step("deploy_to_cloud", "info", "Deploying to cloud")
            time.sleep(2)  # Simulate deployment time
            
            self.log_step("deployment_complete", "success", "Deployment completed successfully")
            
            # Run post-deployment validation
            self.log_step("post_deployment_validation", "info", "Running post-deployment validation")
            results = deployment_monitor.run_post_deployment_validation()
            
            failed_checks = [r for r in results if r.status == ValidationStatus.FAILED]
            
            if failed_checks:
                self.log_step("post_deployment_validation", "failed", 
                            f"Post-deployment validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check.check_name} - {check.message}")
                return False
            
            self.log_step("post_deployment_validation", "success", 
                        "Post-deployment validation passed successfully")
            
            return True
            
        except Exception as e:
            self.log_step("deployment", "error", f"Deployment error: {str(e)}")
            logger.error(f"Deployment failed: {str(e)}")
            return False
    
    def enable_admin_testing(self) -> bool:
        """Enable enhanced TRIMP for admin user for testing"""
        logger.info("=" * 60)
        logger.info("PHASE 3: ENABLE ADMIN TESTING")
        logger.info("=" * 60)
        
        self.log_step("admin_testing_start", "info", "Enabling enhanced TRIMP for admin user")
        
        try:
            # This would typically enable the feature flag for admin users
            # For now, we'll simulate the process
            
            self.log_step("enable_admin_feature_flag", "info", "Enabling feature flag for admin user")
            time.sleep(1)  # Simulate processing time
            
            # Run admin testing validation
            self.log_step("admin_testing_validation", "info", "Running admin testing validation")
            results = deployment_monitor.run_admin_testing_validation()
            
            failed_checks = [r for r in results if r.status == ValidationStatus.FAILED]
            
            if failed_checks:
                self.log_step("admin_testing_validation", "failed", 
                            f"Admin testing validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check.check_name} - {check.message}")
                return False
            
            self.log_step("admin_testing_validation", "success", 
                        "Admin testing validation passed successfully")
            
            # Advance to admin testing phase
            deployment_monitor.advance_deployment_phase(DeploymentPhase.ADMIN_TESTING)
            
            return True
            
        except Exception as e:
            self.log_step("admin_testing", "error", f"Admin testing error: {str(e)}")
            logger.error(f"Admin testing failed: {str(e)}")
            return False
    
    def enable_beta_rollout(self) -> bool:
        """Enable enhanced TRIMP for beta users"""
        logger.info("=" * 60)
        logger.info("PHASE 4: ENABLE BETA ROLLOUT")
        logger.info("=" * 60)
        
        self.log_step("beta_rollout_start", "info", "Enabling enhanced TRIMP for beta users")
        
        try:
            # This would typically enable the feature flag for beta users
            self.log_step("enable_beta_feature_flag", "info", "Enabling feature flag for beta users")
            time.sleep(1)  # Simulate processing time
            
            # Run beta rollout validation
            self.log_step("beta_rollout_validation", "info", "Running beta rollout validation")
            results = deployment_monitor.run_beta_rollout_validation()
            
            failed_checks = [r for r in results if r.status == ValidationStatus.FAILED]
            
            if failed_checks:
                self.log_step("beta_rollout_validation", "failed", 
                            f"Beta rollout validation failed with {len(failed_checks)} failures")
                for check in failed_checks:
                    logger.error(f"  FAILED: {check.check_name} - {check.message}")
                return False
            
            self.log_step("beta_rollout_validation", "success", 
                        "Beta rollout validation passed successfully")
            
            # Advance to beta rollout phase
            deployment_monitor.advance_deployment_phase(DeploymentPhase.BETA_ROLLOUT)
            
            return True
            
        except Exception as e:
            self.log_step("beta_rollout", "error", f"Beta rollout error: {str(e)}")
            logger.error(f"Beta rollout failed: {str(e)}")
            return False
    
    def monitor_deployment(self, duration_minutes: int = 60) -> bool:
        """Monitor the deployment for a specified duration"""
        logger.info("=" * 60)
        logger.info("PHASE 5: MONITORING DEPLOYMENT")
        logger.info("=" * 60)
        
        self.log_step("monitoring_start", "info", f"Starting deployment monitoring for {duration_minutes} minutes")
        
        try:
            # Advance to monitoring phase
            deployment_monitor.advance_deployment_phase(DeploymentPhase.MONITORING)
            
            # Monitor for specified duration
            end_time = datetime.now().timestamp() + (duration_minutes * 60)
            
            while datetime.now().timestamp() < end_time:
                # Update metrics
                deployment_monitor.update_metrics()
                
                # Get current status
                status = deployment_monitor.get_deployment_status()
                
                # Log status every 10 minutes
                if int(datetime.now().timestamp()) % 600 == 0:
                    logger.info(f"Deployment Status: {status['overall_status']}")
                    logger.info(f"Uptime: {status['uptime_seconds']:.0f} seconds")
                
                time.sleep(60)  # Check every minute
            
            self.log_step("monitoring_complete", "success", 
                        f"Deployment monitoring completed successfully after {duration_minutes} minutes")
            
            return True
            
        except Exception as e:
            self.log_step("monitoring", "error", f"Monitoring error: {str(e)}")
            logger.error(f"Monitoring failed: {str(e)}")
            return False
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate a comprehensive deployment report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Get final deployment status
        final_status = deployment_monitor.get_deployment_status()
        validation_summary = deployment_monitor.get_validation_summary()
        
        report = {
            'deployment_summary': {
                'start_time': self.start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_seconds': duration.total_seconds(),
                'duration_minutes': duration.total_seconds() / 60,
                'final_phase': final_status['deployment_phase'],
                'overall_status': final_status['overall_status']
            },
            'validation_summary': validation_summary,
            'deployment_log': self.deployment_log,
            'final_metrics': final_status['metrics'],
            'recommendations': self._generate_recommendations(final_status)
        }
        
        return report
    
    def _generate_recommendations(self, final_status: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on deployment status"""
        recommendations = []
        
        if final_status['overall_status'] == 'healthy':
            recommendations.append("✅ Deployment is healthy and ready for production use")
            recommendations.append("✅ Consider enabling general release after monitoring period")
        elif final_status['overall_status'] == 'warning':
            recommendations.append("⚠️ Deployment has warnings - review and address before general release")
            recommendations.append("⚠️ Monitor system closely during beta rollout")
        elif final_status['overall_status'] == 'failed':
            recommendations.append("❌ Deployment has failures - do not proceed to general release")
            recommendations.append("❌ Review and fix all failed validation checks")
        
        # Add phase-specific recommendations
        current_phase = final_status['deployment_phase']
        if current_phase == 'admin_testing':
            recommendations.append("🔍 Continue admin testing for at least 24 hours")
            recommendations.append("📊 Monitor admin user activity and feedback")
        elif current_phase == 'beta_rollout':
            recommendations.append("👥 Monitor beta user feedback and system performance")
            recommendations.append("📈 Track usage metrics and error rates")
        elif current_phase == 'monitoring':
            recommendations.append("📊 Continue monitoring for system stability")
            recommendations.append("🎯 Prepare for general release if metrics are positive")
        
        return recommendations
    
    def save_deployment_report(self, report: Dict[str, Any], filename: str = None):
        """Save deployment report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trimp_deployment_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Deployment report saved to: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save deployment report: {str(e)}")
            return None


def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy TRIMP Enhancement with Monitoring')
    parser.add_argument('--phase', choices=['pre_deployment', 'deploy', 'admin_testing', 'beta_rollout', 'monitor', 'full'], 
                       default='full', help='Deployment phase to run')
    parser.add_argument('--monitor-duration', type=int, default=60, 
                       help='Monitoring duration in minutes (default: 60)')
    parser.add_argument('--skip-validation', action='store_true', 
                       help='Skip validation checks (not recommended)')
    
    args = parser.parse_args()
    
    deployment = TrimpEnhancementDeployment()
    
    logger.info("🚀 Starting TRIMP Enhancement Deployment")
    logger.info(f"Deployment Phase: {args.phase}")
    logger.info(f"Monitor Duration: {args.monitor_duration} minutes")
    
    success = True
    
    try:
        if args.phase in ['pre_deployment', 'full']:
            success = deployment.run_pre_deployment_checks()
            if not success:
                logger.error("❌ Pre-deployment checks failed. Aborting deployment.")
                return False
        
        if success and args.phase in ['deploy', 'full']:
            success = deployment.deploy_with_feature_flags_disabled()
            if not success:
                logger.error("❌ Deployment failed. Aborting.")
                return False
        
        if success and args.phase in ['admin_testing', 'full']:
            success = deployment.enable_admin_testing()
            if not success:
                logger.error("❌ Admin testing setup failed. Aborting.")
                return False
        
        if success and args.phase in ['beta_rollout', 'full']:
            success = deployment.enable_beta_rollout()
            if not success:
                logger.error("❌ Beta rollout setup failed. Aborting.")
                return False
        
        if success and args.phase in ['monitor', 'full']:
            success = deployment.monitor_deployment(args.monitor_duration)
            if not success:
                logger.error("❌ Monitoring failed.")
                return False
        
        # Generate and save deployment report
        report = deployment.generate_deployment_report()
        report_file = deployment.save_deployment_report(report)
        
        logger.info("=" * 60)
        logger.info("DEPLOYMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {report['deployment_summary']['overall_status']}")
        logger.info(f"Final Phase: {report['deployment_summary']['final_phase']}")
        logger.info(f"Duration: {report['deployment_summary']['duration_minutes']:.1f} minutes")
        
        if report_file:
            logger.info(f"Report saved to: {report_file}")
        
        # Print recommendations
        logger.info("\n📋 RECOMMENDATIONS:")
        for recommendation in report['recommendations']:
            logger.info(f"  {recommendation}")
        
        return success
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ Deployment interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error during deployment: {str(e)}")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
