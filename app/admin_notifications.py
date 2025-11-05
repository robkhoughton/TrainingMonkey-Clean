#!/usr/bin/env python3
"""
Admin Notification Helpers

Simple notification functions for admin alerts.
"""

import logging
from datetime import datetime
from typing import Optional
from db_utils import execute_query

logger = logging.getLogger(__name__)

def notify_admin_of_new_user(user_id: int, user_email: str) -> bool:
    """
    Send email notification to admin (user 1) about new user registration
    
    Args:
        user_id: New user's ID
        user_email: New user's email
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        # Get admin email (user_id=1 or first is_admin user)
        admin_query = """
            SELECT email 
            FROM user_settings 
            WHERE id = 1 OR is_admin = TRUE
            ORDER BY id
            LIMIT 1
        """
        admin_result = execute_query(admin_query, fetch=True)
        
        if not admin_result:
            logger.warning("No admin user found for new user notification")
            return False
        
        admin_email = admin_result[0]['email']
        
        # Import email service (reuse existing infrastructure)
        from migration_notification_system import MigrationNotificationSystem
        
        email_service = MigrationNotificationSystem()
        
        # Prepare email
        subject = f"New User Registration - {user_email}"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #4CAF50;">New User Registration</h2>
            <table style="border-collapse: collapse; margin: 20px 0;">
                <tr>
                    <td style="padding: 8px; font-weight: bold;">User ID:</td>
                    <td style="padding: 8px;">{user_id}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Email:</td>
                    <td style="padding: 8px;">{user_email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Registration Time:</td>
                    <td style="padding: 8px;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
                </tr>
            </table>
            <hr style="border: 1px solid #eee; margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                This is an automated notification from TrainingMonkey.
            </p>
        </body>
        </html>
        """
        
        # Send email
        success = email_service._send_email(admin_email, subject, body)
        
        if success:
            logger.info(f"Admin notified of new user: {user_id} ({user_email})")
        else:
            logger.warning(f"Failed to notify admin of new user: {user_id} ({user_email})")
        
        return success
        
    except Exception as e:
        logger.error(f"Error notifying admin of new user {user_id}: {str(e)}")
        return False













