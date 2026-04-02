#!/bin/bash
# TrainingMonkey Build and Copy Script (Bash version)

set -e  # Exit on any error

echo "TrainingMonkey Build and Copy Script"
echo "===================================="
echo ""

# Get the script's directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Step 1: Building React app..."
cd "$PROJECT_ROOT/frontend"

echo "Building React app..."
npm run build

echo ""
echo "Step 2: Copying build files to app/static..."
cd "$PROJECT_ROOT"

# Copy all build files to app/static
cp -r frontend/build/* app/static/

echo ""
echo "Build and copy completed successfully!"
echo "React app is now ready to serve from app/static/"
