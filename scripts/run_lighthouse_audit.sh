#!/bin/bash
# ============================================================================
# Lighthouse Performance Audit Script (Linux/Mac)
# ============================================================================
# This script runs a Lighthouse audit on the deployed TrainingMonkey app
# and generates a detailed performance report
#
# Prerequisites:
#   1. Node.js and npm installed
#   2. App deployed to cloud (get URL from deployment)
#   3. Lighthouse CLI installed (npm install -g lighthouse)
# ============================================================================

echo ""
echo "===================================="
echo "TrainingMonkey Lighthouse Audit"
echo "===================================="
echo ""

# Check if Lighthouse is installed
if ! command -v lighthouse &> /dev/null; then
    echo "[ERROR] Lighthouse not found. Installing..."
    npm install -g lighthouse
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Lighthouse. Install manually with: npm install -g lighthouse"
        exit 1
    fi
fi

# Get app URL from user or use default
read -p "Enter your app URL (or press Enter for default): " APP_URL
if [ -z "$APP_URL" ]; then
    # Default to common Google Cloud App Engine URL pattern
    echo "[INFO] Using default URL pattern - update this script with your actual URL"
    APP_URL="https://your-project-id.uc.r.appspot.com"
fi

echo ""
echo "[INFO] Running Lighthouse audit on: $APP_URL"
echo "[INFO] This may take 30-60 seconds..."
echo ""

# Create reports directory if it doesn't exist
mkdir -p reports

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Run Lighthouse audit
# - Only audit performance category (faster)
# - Save as HTML and JSON
# - Simulate mobile device
# - Include detailed breakdown
lighthouse "$APP_URL" \
    --only-categories=performance \
    --output=html \
    --output=json \
    --output-path=reports/lighthouse_$TIMESTAMP \
    --view \
    --chrome-flags="--headless --no-sandbox" \
    --emulated-form-factor=mobile \
    --throttling-method=simulate

if [ $? -eq 0 ]; then
    echo ""
    echo "===================================="
    echo "[SUCCESS] Lighthouse Audit Complete!"
    echo "===================================="
    echo ""
    echo "Reports saved to:"
    echo "  - reports/lighthouse_${TIMESTAMP}.html"
    echo "  - reports/lighthouse_${TIMESTAMP}.json"
    echo ""
    echo "The HTML report should open in your browser automatically."
    echo ""
    echo "Key Metrics to Review:"
    echo "  - Performance Score (target: 90+)"
    echo "  - First Contentful Paint (target: < 1.8s)"
    echo "  - Largest Contentful Paint (target: < 2.5s)"
    echo "  - Total Blocking Time (target: < 200ms)"
    echo "  - Cumulative Layout Shift (target: < 0.1)"
    echo "  - Speed Index (target: < 3.4s)"
    echo ""
    
    # Also run desktop audit
    echo "[INFO] Running desktop audit for comparison..."
    lighthouse "$APP_URL" \
        --only-categories=performance \
        --output=html \
        --output-path=reports/lighthouse_desktop_$TIMESTAMP \
        --chrome-flags="--headless --no-sandbox" \
        --emulated-form-factor=desktop \
        --throttling-method=simulate
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "[SUCCESS] Desktop audit also complete!"
        echo "  - reports/lighthouse_desktop_${TIMESTAMP}.html"
        echo ""
    fi
else
    echo ""
    echo "[ERROR] Lighthouse audit failed!"
    echo ""
    echo "Common issues:"
    echo "  1. App URL is incorrect or not accessible"
    echo "  2. App requires authentication (Lighthouse can't login)"
    echo "  3. Network connectivity issues"
    echo "  4. Chrome/Chromium not installed"
    echo ""
    echo "Try running manually:"
    echo "  lighthouse $APP_URL --view --only-categories=performance"
    echo ""
    exit 1
fi

echo ""




