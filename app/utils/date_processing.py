#!/usr/bin/env python3
"""
Date processing utilities for Training Monkey™
Handles date serialization and processing for API responses
"""

from datetime import datetime, date


def ensure_date_serialization(data):
    """
    Ensure all date objects in data are properly serialized for JSON
    Handles the conversion from PostgreSQL DATE type to frontend-compatible strings
    CRITICAL FIX: After database DATE standardization, PostgreSQL returns date objects
    that need to be converted to ISO strings for React compatibility
    """

    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['date', 'created_at', 'updated_at', 'generation_date', 'latest_activity_date', 'lastActivity']:
                if isinstance(value, date):
                    # PostgreSQL DATE type → ISO string
                    data[key] = value.isoformat()
                elif isinstance(value, datetime):
                    # PostgreSQL TIMESTAMP type → ISO string
                    data[key] = value.isoformat()
                elif isinstance(value, str) and value:
                    # Validate and normalize string dates
                    try:
                        # Try parsing as date first
                        parsed = datetime.strptime(value, '%Y-%m-%d')
                        data[key] = parsed.strftime('%Y-%m-%d')
                    except:
                        try:
                            # Try parsing as datetime
                            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            data[key] = parsed.isoformat()
                        except:
                            # Leave as-is if can't parse
                            pass
            else:
                # Recursively handle nested objects
                data[key] = ensure_date_serialization(value)
    elif isinstance(data, list):
        return [ensure_date_serialization(item) for item in data]

    return data
