"""
Email Verification Routes - Flask Blueprint

Provides HTTP endpoints for email verification functionality.
Follows TrainingMonkey's blueprint pattern (similar to chat/routes.py).
"""

import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user, login_user
from .service import EmailVerificationService
from auth import User

logger = logging.getLogger(__name__)

# Create blueprint (follows chat blueprint pattern)
email_verification_blueprint = Blueprint('email_verification', __name__)


@email_verification_blueprint.route('/email-verification-pending', methods=['GET'])
@login_required
def verification_pending():
    """
    Blocking page for users awaiting email verification.
    Shows email address and provides resend button.
    Auto-polls for verification status every 5 seconds.
    """
    service = EmailVerificationService()

    try:
        user_id = current_user.id

        # If already verified, redirect to onboarding
        if service.is_verified(user_id):
            logger.info(f"User {user_id} already verified, redirecting to onboarding")
            return redirect(url_for('welcome_post_strava'))

        # Get user's email to display
        user_email = service.get_user_email(user_id)
        if not user_email:
            flash('Error loading account. Please contact support.', 'danger')
            return redirect(url_for('logout'))

        # Synthetic email check (shouldn't reach here, but defensive programming)
        if '@training-monkey.com' in user_email:
            logger.warning(f"User {user_id} with synthetic email reached verification page")
            return redirect(url_for('welcome_post_strava'))

        return render_template('email_verification_pending.html', user_email=user_email)

    except Exception as e:
        logger.error(f"Error in verification_pending for user {current_user.id}: {e}")
        flash('Error loading verification page. Please try again.', 'danger')
        return redirect(url_for('dashboard'))


@email_verification_blueprint.route('/verify-email', methods=['GET'])
def verify_email():
    """
    Handle email verification link clicks.
    No authentication required - token IS the authentication.
    Marks email as verified and logs user in if needed.
    """
    service = EmailVerificationService()

    try:
        token = request.args.get('token')
        if not token:
            flash('Invalid verification link. Please check your email for the correct link.', 'warning')
            return redirect(url_for('login'))

        # Verify token (handles expiry check, DB update)
        success, user_id, error = service.verify_email_token(token)

        if not success:
            # Handle specific error types
            if 'expired' in error.lower():
                flash('Verification link has expired. Please request a new one.', 'warning')
            elif 'invalid' in error.lower():
                flash('Invalid verification link. Please check your email.', 'warning')
            else:
                flash('Unable to verify your email. Please try again or contact support.', 'danger')
            return redirect(url_for('login'))

        # Verification successful - log user in if needed
        user = User.get(user_id)
        if not user:
            logger.error(f"User {user_id} not found after successful email verification")
            flash('Error loading your account. Please try logging in.', 'danger')
            return redirect(url_for('login'))

        # Log user in if not already authenticated
        if not current_user.is_authenticated or current_user.id != user_id:
            login_user(user)
            logger.info(f"User {user_id} logged in after email verification")

        flash('Email verified successfully! Please complete your profile setup.', 'success')
        return redirect(url_for('welcome_post_strava'))

    except Exception as e:
        logger.error(f"Error in verify_email: {e}")
        flash('Error verifying your email. Please try again or contact support.', 'danger')
        return redirect(url_for('login'))


@email_verification_blueprint.route('/api/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    """
    API endpoint to resend verification email.
    Called by AJAX from email_verification_pending.html.
    Returns JSON response with success/error message.
    """
    service = EmailVerificationService()

    try:
        user_id = current_user.id

        # Get user's email
        email = service.get_user_email(user_id)
        if not email:
            logger.error(f"User {user_id} not found when resending verification")
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Don't send to synthetic emails
        if '@training-monkey.com' in email:
            logger.warning(f"User {user_id} attempted to resend verification for synthetic email")
            return jsonify({'success': False, 'error': 'Email verification not required for this account'}), 400

        # Check if already verified
        if service.is_verified(user_id):
            logger.info(f"User {user_id} already verified, no need to resend")
            return jsonify({'success': True, 'message': 'Email already verified'})

        # Send verification email
        base_url = os.environ.get('APP_BASE_URL', 'https://yourtrainingmonkey.com')
        success, error = service.send_verification(user_id, email, base_url)

        if success:
            return jsonify({'success': True, 'message': 'Verification email sent. Please check your inbox.'})
        else:
            logger.error(f"Failed to resend verification email to user {user_id}: {error}")
            return jsonify({'success': False, 'error': 'Failed to send email. Please try again later.'}), 500

    except Exception as e:
        logger.error(f"Error in resend_verification for user {current_user.id}: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@email_verification_blueprint.route('/api/check-verification-status', methods=['GET'])
@login_required
def check_verification_status():
    """
    Auto-polling endpoint for verification status.
    Called every 5 seconds by email_verification_pending.html.
    Returns JSON with verified status.
    """
    service = EmailVerificationService()

    try:
        verified = service.is_verified(current_user.id)
        return jsonify({
            'success': True,
            'verified': verified,
            'user_id': current_user.id
        })
    except Exception as e:
        logger.error(f"Error checking verification status for user {current_user.id}: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
