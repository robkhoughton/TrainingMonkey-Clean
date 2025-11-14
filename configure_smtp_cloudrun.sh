#!/bin/bash
# Configure SMTP for TrainingMonkey Cloud Run Service
# This will enable email notifications for new user registrations

echo "=========================================="
echo "SMTP Configuration for Cloud Run"
echo "=========================================="
echo ""
echo "BEFORE RUNNING THIS SCRIPT:"
echo "1. Generate Gmail App Password at: https://myaccount.google.com/apppasswords"
echo "2. Replace <YOUR_APP_PASSWORD> below with the generated password"
echo ""
echo "=========================================="
echo ""

# EDIT THIS: Replace with your actual Gmail app password
APP_PASSWORD="<YOUR_APP_PASSWORD>"

# Your service name (update if different)
SERVICE_NAME="training-monkey-service"

# Your Google Cloud region (update if different)
REGION="us-central1"

echo "Configuring SMTP environment variables..."
echo ""

gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --set-env-vars="SMTP_SERVER=smtp.gmail.com" \
  --set-env-vars="SMTP_PORT=587" \
  --set-env-vars="SMTP_USERNAME=rob.houghton.ca@gmail.com" \
  --set-env-vars="SMTP_PASSWORD=$APP_PASSWORD" \
  --set-env-vars="FROM_EMAIL=rob.houghton.ca@gmail.com" \
  --set-env-vars="FROM_NAME=TrainingMonkey Notifications"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "SUCCESS!"
    echo "=========================================="
    echo "SMTP has been configured for Cloud Run."
    echo ""
    echo "Future user registrations will now trigger email notifications to:"
    echo "  rob.houghton.ca@gmail.com"
    echo ""
    echo "Test it by:"
    echo "1. Creating a test Strava account"
    echo "2. Registering on yourtrainingmonkey.com"
    echo "3. Check your email for the notification"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "ERROR"
    echo "=========================================="
    echo "Failed to configure SMTP."
    echo "Check your gcloud authentication and service name."
    echo ""
fi


