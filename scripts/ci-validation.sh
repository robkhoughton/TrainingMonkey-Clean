#!/bin/bash
# CI/CD Validation Script
# Run this in your CI/CD pipeline to enforce project rules

set -e  # Exit on any error

echo "🚀 Starting CI/CD validation..."

# Check if we're in the right directory
if [ ! -f "app/strava_app.py" ]; then
    echo "❌ Error: Not in project root directory"
    exit 1
fi

# Run SQL syntax validation
echo "🔍 Validating SQL syntax..."
python scripts/validate_sql_syntax.py
if [ $? -ne 0 ]; then
    echo "❌ SQL validation failed!"
    exit 1
fi

# Run database rules check
echo "🔍 Checking database rules..."
python scripts/pre-commit-hooks.py
if [ $? -ne 0 ]; then
    echo "❌ Database rules check failed!"
    exit 1
fi

# Check for forbidden imports
echo "🔍 Checking for forbidden imports..."
if grep -r "import sqlite3" app/; then
    echo "❌ Found forbidden sqlite3 imports!"
    exit 1
fi

if grep -r "from sqlite3" app/; then
    echo "❌ Found forbidden sqlite3 imports!"
    exit 1
fi

# Check for SQLite placeholders
echo "🔍 Checking for SQLite placeholders..."
if grep -r "WHERE.*= ?" app/; then
    echo "❌ Found SQLite placeholders (?) in SQL queries!"
    exit 1
fi

# Check for proper date handling
echo "🔍 Checking date handling..."
if grep -r "datetime.now()" app/ | grep -v "datetime.now().date()"; then
    echo "⚠️  Warning: Found datetime.now() without .date() - review for date-only operations"
fi

echo "✅ All CI/CD validation checks passed!"
echo "🎉 Ready for deployment!"
