#!/usr/bin/env python3
"""
Migration Notification System

This module handles notifications for existing user migration, including:
- Email notifications for migration status
- In-app notifications
- Notification tracking and delivery status
- Notification templates and personalization
- Notification scheduling and retry logic

Usage:
    from migration_notification_system import MigrationNotificationSystem
    
    notifier = MigrationNotificationSystem()
    notifier.send_migration_notification(user_id, 'completed')
"""

import os
import sys
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_utils import execute_query, get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NotificationTemplate:
    """Notification template configuration"""
    template_id: str
    subject: str
    body_template: str
    notification_type: str
    priority: str = 'normal'  # 'low', 'normal', 'high', 'urgent'

@dataclass
class NotificationConfig:
    """Notification system configuration"""
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    from_email: str
    from_name: str
    retry_attempts: int = 3
    retry_delay_minutes: int = 5

class MigrationNotificationSystem:
    """Handles migration notifications for existing users"""
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or self._load_config()
        self.templates = self._load_templates()
        
    def _load_config(self) -> NotificationConfig:
        """Load notification configuration from environment or defaults"""
        return NotificationConfig(
            smtp_server=os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            from_email=os.getenv('FROM_EMAIL', 'noreply@trainingmonkey.com'),
            from_name=os.getenv('FROM_NAME', 'TrainingMonkey Support'),
            retry_attempts=int(os.getenv('NOTIFICATION_RETRY_ATTEMPTS', '3')),
            retry_delay_minutes=int(os.getenv('NOTIFICATION_RETRY_DELAY', '5'))
        )
    
    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Load notification templates"""
        return {
            'migration_started': NotificationTemplate(
                template_id='migration_started',
                subject='Your TrainingMonkey Account Migration Has Started',
                body_template="""
                <html>
                <body>
                    <h2>Migration in Progress</h2>
                    <p>Hello {user_name},</p>
                    <p>We're currently migrating your TrainingMonkey account to our new OAuth system. This process will:</p>
                    <ul>
                        <li>Preserve all your existing data and Strava connection</li>
                        <li>Update your account to use our new secure system</li>
                        <li>Maintain all your training history and goals</li>
                    </ul>
                    <p>You may experience brief interruptions during this process. We'll notify you once the migration is complete.</p>
                    <p>If you have any questions, please don't hesitate to contact our support team.</p>
                    <p>Best regards,<br>The TrainingMonkey Team</p>
                </body>
                </html>
                """,
                notification_type='migration_status',
                priority='normal'
            ),
            
            'migration_completed': NotificationTemplate(
                template_id='migration_completed',
                subject='Your TrainingMonkey Account Migration is Complete!',
                body_template="""
                <html>
                <body>
                    <h2>Migration Completed Successfully</h2>
                    <p>Hello {user_name},</p>
                    <p>Great news! Your TrainingMonkey account has been successfully migrated to our new OAuth system.</p>
                    <p>✅ Your Strava connection has been preserved<br>
                    ✅ All your training data is intact<br>
                    ✅ Your goals and preferences are maintained<br>
                    ✅ Your account is now using our enhanced security system</p>
                    <p>You can continue using TrainingMonkey as usual. The migration was seamless and your experience should remain exactly the same.</p>
                    <p>Thank you for your patience during this upgrade!</p>
                    <p>Best regards,<br>The TrainingMonkey Team</p>
                </body>
                </html>
                """,
                notification_type='migration_status',
                priority='normal'
            ),
            
            'migration_failed': NotificationTemplate(
                template_id='migration_failed',
                subject='Action Required: TrainingMonkey Migration Issue',
                body_template="""
                <html>
                <body>
                    <h2>Migration Issue Detected</h2>
                    <p>Hello {user_name},</p>
                    <p>We encountered an issue while migrating your TrainingMonkey account to our new OAuth system.</p>
                    <p><strong>Error Details:</strong> {error_message}</p>
                    <p>Your account is still fully functional with the current system. We're working to resolve this issue and will retry the migration automatically.</p>
                    <p>If this issue persists, please contact our support team for assistance.</p>
                    <p>We apologize for any inconvenience.</p>
                    <p>Best regards,<br>The TrainingMonkey Team</p>
                </body>
                </html>
                """,
                notification_type='migration_status',
                priority='high'
            ),
            
            'rollback_available': NotificationTemplate(
                template_id='rollback_available',
                subject='Migration Rollback Available - TrainingMonkey',
                body_template="""
                <html>
                <body>
                    <h2>Migration Rollback Option</h2>
                    <p>Hello {user_name},</p>
                    <p>Your TrainingMonkey account has been migrated to our new OAuth system. If you experience any issues, we can rollback your account to the previous system.</p>
                    <p>To request a rollback, please contact our support team within the next 7 days.</p>
                    <p>Your data is safe and we have complete backups of your account before the migration.</p>
                    <p>Best regards,<br>The TrainingMonkey Team</p>
                </body>
                </html>
                """,
                notification_type='rollback_available',
                priority='low'
            ),
            
            'migration_reminder': NotificationTemplate(
                template_id='migration_reminder',
                subject='Reminder: Complete Your TrainingMonkey Migration',
                body_template="""
                <html>
                <body>
                    <h2>Migration Reminder</h2>
                    <p>Hello {user_name},</p>
                    <p>We noticed that your TrainingMonkey account migration hasn't been completed yet. To ensure continued access to all features, please complete the migration process.</p>
                    <p>The migration will:</p>
                    <ul>
                        <li>Preserve all your existing data</li>
                        <li>Maintain your Strava connection</li>
                        <li>Enhance your account security</li>
                    </ul>
                    <p>Please log in to your account to complete the migration, or contact support if you need assistance.</p>
                    <p>Best regards,<br>The TrainingMonkey Team</p>
                </body>
                </html>
                """,
                notification_type='migration_reminder',
                priority='normal'
            )
        }
    
    def send_migration_notification(self, user_id: int, notification_type: str, 
                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send migration notification to user
        
        Args:
            user_id: User ID
            notification_type: Type of notification ('started', 'completed', 'failed', 'rollback_available', 'reminder')
            context: Additional context data for template
            
        Returns:
            Notification result dictionary
        """
        try:
            # Get user information
            user_info = self._get_user_info(user_id)
            if not user_info:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Get template
            template_key = f'migration_{notification_type}'
            if template_key not in self.templates:
                return {
                    'success': False,
                    'error': f'Template not found: {template_key}'
                }
            
            template = self.templates[template_key]
            
            # Prepare context
            context = context or {}
            context.update({
                'user_name': user_info.get('first_name', user_info.get('email', 'User')),
                'user_email': user_info.get('email'),
                'user_id': user_id,
                'migration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Generate notification content
            subject = template.subject
            body = template.body_template.format(**context)
            
            # Send notification
            notification_id = self._create_notification_record(
                user_id, user_info['email'], template.notification_type, 
                notification_type, subject, body
            )
            
            # Send email
            email_sent = self._send_email(user_info['email'], subject, body)
            
            # Update notification status
            self._update_notification_status(notification_id, 'delivered' if email_sent else 'failed')
            
            # Send in-app notification
            in_app_sent = self._send_in_app_notification(user_id, notification_type, context)
            
            return {
                'success': email_sent or in_app_sent,
                'notification_id': notification_id,
                'email_sent': email_sent,
                'in_app_sent': in_app_sent,
                'user_email': user_info['email']
            }
            
        except Exception as e:
            logger.error(f"Error sending migration notification to user {user_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information for notifications"""
        try:
            query = """
                SELECT u.id, u.email, u.first_name, u.last_name, us.migration_status, us.oauth_type
                FROM users u
                LEFT JOIN user_settings us ON u.id = us.user_id
                WHERE u.id = %s
            """
            result = execute_query(query, (user_id,))
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info for user {user_id}: {str(e)}")
            return None
    
    def _create_notification_record(self, user_id: int, email: str, notification_type: str,
                                  status: str, subject: str, message: str) -> str:
        """Create notification record in database"""
        try:
            notification_id = f"notif_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            query = """
                INSERT INTO migration_notifications
                (user_id, email, notification_type, status, message, sent_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            execute_query(query, (
                user_id, email, notification_type, status, message, datetime.now()
            ))
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Error creating notification record: {str(e)}")
            return f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _update_notification_status(self, notification_id: str, status: str) -> bool:
        """Update notification delivery status"""
        try:
            query = """
                UPDATE migration_notifications
                SET status = %s, delivered_at = %s
                WHERE id = %s
            """
            
            delivered_at = datetime.now() if status == 'delivered' else None
            execute_query(query, (status, delivered_at, notification_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating notification status: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email notification"""
        try:
            if not self.config.smtp_username or not self.config.smtp_password:
                logger.warning("SMTP credentials not configured, skipping email send")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def _send_in_app_notification(self, user_id: int, notification_type: str, 
                                 context: Dict[str, Any]) -> bool:
        """Send in-app notification"""
        try:
            # Create in-app notification record
            notification_data = {
                'user_id': user_id,
                'type': f'migration_{notification_type}',
                'title': self._get_in_app_title(notification_type),
                'message': self._get_in_app_message(notification_type, context),
                'priority': self._get_notification_priority(notification_type),
                'created_at': datetime.now(),
                'read': False
            }
            
            # Store in-app notification (you can implement this based on your app's notification system)
            # For now, we'll just log it
            logger.info(f"In-app notification created for user {user_id}: {notification_data}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending in-app notification to user {user_id}: {str(e)}")
            return False
    
    def _get_in_app_title(self, notification_type: str) -> str:
        """Get in-app notification title"""
        titles = {
            'started': 'Migration Started',
            'completed': 'Migration Complete',
            'failed': 'Migration Issue',
            'rollback_available': 'Rollback Available',
            'reminder': 'Migration Reminder'
        }
        return titles.get(notification_type, 'Migration Update')
    
    def _get_in_app_message(self, notification_type: str, context: Dict[str, Any]) -> str:
        """Get in-app notification message"""
        messages = {
            'started': 'Your account migration is in progress. You may experience brief interruptions.',
            'completed': 'Your account has been successfully migrated to the new OAuth system.',
            'failed': f'Migration failed: {context.get("error_message", "Unknown error")}. Contact support for assistance.',
            'rollback_available': 'If you experience issues, we can rollback your migration. Contact support within 7 days.',
            'reminder': 'Please complete your account migration to ensure continued access to all features.'
        }
        return messages.get(notification_type, 'Migration status update available.')
    
    def _get_notification_priority(self, notification_type: str) -> str:
        """Get notification priority"""
        priorities = {
            'started': 'normal',
            'completed': 'normal',
            'failed': 'high',
            'rollback_available': 'low',
            'reminder': 'normal'
        }
        return priorities.get(notification_type, 'normal')
    
    def send_bulk_migration_notifications(self, user_ids: List[int], notification_type: str,
                                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Send bulk migration notifications to multiple users
        
        Args:
            user_ids: List of user IDs
            notification_type: Type of notification
            context: Additional context data
            
        Returns:
            Bulk notification results
        """
        results = {
            'total_users': len(user_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for user_id in user_ids:
            try:
                result = self.send_migration_notification(user_id, notification_type, context)
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'user_id': user_id,
                        'error': result.get('error', 'Unknown error')
                    })
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'user_id': user_id,
                    'error': str(e)
                })
        
        logger.info(f"Bulk notification completed: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def get_notification_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            # Get notification counts by type
            type_query = """
                SELECT notification_type, COUNT(*) as count
                FROM migration_notifications
                GROUP BY notification_type
            """
            type_result = execute_query(type_query)
            
            # Get notification counts by status
            status_query = """
                SELECT status, COUNT(*) as count
                FROM migration_notifications
                GROUP BY status
            """
            status_result = execute_query(status_query)
            
            # Get recent notifications
            recent_query = """
                SELECT COUNT(*) as count
                FROM migration_notifications
                WHERE sent_at >= NOW() - INTERVAL '24 hours'
            """
            recent_result = execute_query(recent_query)
            
            return {
                'by_type': {row['notification_type']: row['count'] for row in type_result},
                'by_status': {row['status']: row['count'] for row in status_result},
                'recent_24h': recent_result[0]['count'] if recent_result else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting notification statistics: {str(e)}")
            return {}
    
    def retry_failed_notifications(self) -> Dict[str, Any]:
        """Retry sending failed notifications"""
        try:
            # Get failed notifications
            query = """
                SELECT id, user_id, email, notification_type, status, message, sent_at
                FROM migration_notifications
                WHERE status = 'failed'
                AND sent_at >= NOW() - INTERVAL '24 hours'
            """
            failed_notifications = execute_query(query)
            
            results = {
                'total_failed': len(failed_notifications),
                'retried': 0,
                'successful': 0,
                'still_failed': 0
            }
            
            for notification in failed_notifications:
                try:
                    # Extract notification type from the stored message or type
                    notification_type = notification['notification_type'].replace('migration_', '')
                    
                    # Retry sending
                    result = self.send_migration_notification(
                        notification['user_id'], 
                        notification_type
                    )
                    
                    results['retried'] += 1
                    if result['success']:
                        results['successful'] += 1
                    else:
                        results['still_failed'] += 1
                        
                except Exception as e:
                    results['still_failed'] += 1
                    logger.error(f"Error retrying notification {notification['id']}: {str(e)}")
            
            logger.info(f"Retry completed: {results['successful']} successful, {results['still_failed']} still failed")
            return results
            
        except Exception as e:
            logger.error(f"Error retrying failed notifications: {str(e)}")
            return {'error': str(e)}

def main():
    """Main function for testing"""
    notifier = MigrationNotificationSystem()
    
    # Test notification sending (commented out for safety)
    # result = notifier.send_migration_notification(1, 'completed')
    # print(f"Notification result: {result}")
    
    # Get notification statistics
    stats = notifier.get_notification_statistics()
    print(f"Notification statistics: {stats}")

if __name__ == '__main__':
    main()

