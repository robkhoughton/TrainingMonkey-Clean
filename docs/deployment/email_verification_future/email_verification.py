"""
Email Verification Module
Handles sending verification emails and validating verification tokens for new users.
Hard verification enforced during onboarding - users cannot proceed until verified.
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


def generate_verification_token():
    """
    Generate a secure verification token (32 bytes = 64 hex chars)

    Returns:
        str: Secure random token
    """
    return secrets.token_hex(32)


def hash_token(token):
    """
    Hash token for secure storage (SHA-256)

    Args:
        token: Raw token string

    Returns:
        str: Hashed token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_verification_token(user_id, email):
    """
    Create verification token and store in database

    Args:
        user_id: User ID
        email: Email address to verify

    Returns:
        tuple: (success: bool, token: str or None, error: str or None)
    """
    try:
        from db_utils import execute_query

        # Generate token
        raw_token = generate_verification_token()
        hashed_token = hash_token(raw_token)

        # Token expires in 48 hours
        expires_at = datetime.now() + timedelta(hours=48)

        # Store hashed token in database
        execute_query(
            """UPDATE user_settings
               SET email_verification_token = %s,
                   email_verification_expires_at = %s,
                   email_verified = false
               WHERE id = %s""",
            (hashed_token, expires_at, user_id),
            fetch=False
        )

        logger.info(f"Created verification token for user {user_id}, expires at {expires_at}")
        return True, raw_token, None

    except Exception as e:
        logger.error(f"Error creating verification token for user {user_id}: {str(e)}")
        return False, None, str(e)


def verify_token(token):
    """
    Verify token and mark email as verified

    Args:
        token: Raw token from verification link

    Returns:
        tuple: (success: bool, user_id: int or None, error: str or None)
    """
    try:
        from db_utils import execute_query

        # Hash the incoming token
        hashed_token = hash_token(token)

        # Look up user with this token
        result = execute_query(
            """SELECT id, email, email_verification_expires_at
               FROM user_settings
               WHERE email_verification_token = %s
               AND email_verified = false""",
            (hashed_token,),
            fetch=True
        )

        if not result or len(result) == 0:
            logger.warning(f"Invalid verification token attempted")
            return False, None, "Invalid verification token"

        user = result[0]
        user_id = user['id']
        expires_at = user['email_verification_expires_at']

        # Check if token expired
        if expires_at and datetime.now() > expires_at:
            logger.warning(f"Expired verification token for user {user_id}")
            return False, None, "Verification link has expired"

        # Mark email as verified
        execute_query(
            """UPDATE user_settings
               SET email_verified = true,
                   email_verification_token = NULL,
                   email_verification_expires_at = NULL
               WHERE id = %s""",
            (user_id,),
            fetch=False
        )

        logger.info(f"Email verified successfully for user {user_id}")
        return True, user_id, None

    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return False, None, str(e)


def send_verification_email(user_id, email, base_url=None):
    """
    Send verification email to user

    Args:
        user_id: User ID
        email: Email address to send to
        base_url: Base URL for verification link (e.g., https://yourtrainingmonkey.com)

    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        # Create verification token
        success, token, error = create_verification_token(user_id, email)
        if not success:
            return False, error

        # Get base URL from environment if not provided
        if not base_url:
            base_url = os.environ.get('APP_BASE_URL', 'https://yourtrainingmonkey.com')

        # Build verification link
        verification_link = f"{base_url}/verify-email?token={token}"

        # Build email content
        subject = "Verify Your Email - Your Training Monkey"

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #1f2937;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                    border-radius: 12px;
                    border: 2px solid #16a34a;
                    padding: 30px;
                    margin: 20px 0;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #16a34a;
                    font-size: 28px;
                    margin: 0;
                }}
                .content {{
                    background: white;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 20px 0;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    color: white;
                    padding: 15px 40px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    margin: 20px 0;
                }}
                .button:hover {{
                    opacity: 0.9;
                }}
                .footer {{
                    text-align: center;
                    color: #6b7280;
                    font-size: 14px;
                    margin-top: 30px;
                }}
                .footer a {{
                    color: #16a34a;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://yourtrainingmonkey.com/static/images/YTM_Logo_byandfor.webp" alt="Your Training Monkey" style="max-width: 220px; height: auto; margin-bottom: 15px;">
                    <p style="font-size: 18px; font-weight: 600; margin: 0;">Verify Your Email Address</p>
                </div>

                <div class="content">
                    <p>Welcome to <strong>Your Training Monkey</strong>!</p>

                    <p>To complete your registration and start tracking your training, please verify your email address by clicking the button below:</p>

                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify My Email</a>
                    </div>

                    <p style="margin-top: 30px;">Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #667eea; font-size: 14px;">
                        {verification_link}
                    </p>

                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                        <strong>⚠️ Important:</strong> This verification link expires in 48 hours. You won't be able to access your dashboard until you verify your email.
                    </p>
                </div>

                <div class="footer">
                    <p>If you didn't create an account with Your Training Monkey, you can safely ignore this email.</p>
                    <p>Need help? Contact us at <a href="mailto:support@yourtrainingmonkey.com">support@yourtrainingmonkey.com</a></p>
                </div>
            </div>
        </body>
        </html>
        """

        text_body = f"""
        Your Training Monkey - Verify Your Email

        Welcome to Your Training Monkey!

        To complete your registration and start tracking your training, please verify your email address by clicking this link:

        {verification_link}

        This verification link expires in 48 hours. You won't be able to access your dashboard until you verify your email.

        If you didn't create an account with Your Training Monkey, you can safely ignore this email.

        Need help? Contact us at support@yourtrainingmonkey.com
        """

        # Send email via SMTP
        success = _send_smtp_email(email, subject, html_body, text_body)

        if success:
            logger.info(f"Verification email sent to {email} for user {user_id}")
            return True, None
        else:
            return False, "Failed to send email"

    except Exception as e:
        logger.error(f"Error sending verification email to {email}: {str(e)}")
        return False, str(e)


def _send_smtp_email(to_email, subject, html_body, text_body):
    """
    Send email via SMTP

    Args:
        to_email: Recipient email
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text email body

    Returns:
        bool: Success status
    """
    try:
        # Get SMTP configuration from environment
        smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        from_email = os.environ.get('SMTP_FROM_EMAIL', 'noreply@yourtrainingmonkey.com')

        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured (SMTP_USER and SMTP_PASSWORD required)")
            return False

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        logger.info(f"SMTP email sent successfully to {to_email}")
        return True

    except Exception as e:
        logger.error(f"SMTP error sending to {to_email}: {str(e)}")
        return False


def is_email_verified(user_id):
    """
    Check if user's email is verified

    Args:
        user_id: User ID

    Returns:
        bool: True if verified, False otherwise
    """
    try:
        from db_utils import execute_query

        result = execute_query(
            "SELECT email_verified FROM user_settings WHERE id = %s",
            (user_id,),
            fetch=True
        )

        if result and len(result) > 0:
            return result[0].get('email_verified', False) == True

        return False

    except Exception as e:
        logger.error(f"Error checking email verification for user {user_id}: {str(e)}")
        return False


def needs_verification(user_id):
    """
    Check if user needs email verification (new user with real email that isn't verified)

    Args:
        user_id: User ID

    Returns:
        bool: True if needs verification, False otherwise
    """
    try:
        from db_utils import execute_query

        result = execute_query(
            """SELECT email, email_verified, registration_date, created_at
               FROM user_settings
               WHERE id = %s""",
            (user_id,),
            fetch=True
        )

        if not result or len(result) == 0:
            return False

        user = result[0]
        email = user.get('email', '')
        email_verified = user.get('email_verified')

        # Skip verification for synthetic emails
        if '@training-monkey.com' in email:
            return False

        # Check if user is "new" (registered after this system was deployed)
        # For now, consider all users with real emails as needing verification
        # unless already verified
        if email_verified is True:
            return False

        # User has real email but not verified
        return True

    except Exception as e:
        logger.error(f"Error checking verification need for user {user_id}: {str(e)}")
        return False
