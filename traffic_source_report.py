#!/usr/bin/env python3
"""
Traffic Source Report for TrainingMonkey
Analyzes where users are coming from based on referrer data
"""

import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse

# Connect to database
conn = psycopg2.connect('postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d')
cur = conn.cursor()

print("=" * 80)
print("TRAININGMONKEY TRAFFIC SOURCE REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Check if analytics_events table exists
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'analytics_events'
    );
""")
has_analytics = cur.fetchone()[0]

if not has_analytics:
    print("\n[WARNING] analytics_events table not found.")
    print("Checking for alternative analytics tables...")
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE '%analytic%'
        ORDER BY table_name;
    """)
    analytics_tables = cur.fetchall()
    if analytics_tables:
        print("\nFound analytics-related tables:")
        for table in analytics_tables:
            print(f"  - {table[0]}")
    else:
        print("\nNo analytics tables found in database.")
    
    cur.close()
    conn.close()
    exit(1)

# Get table schema
print("\n" + "=" * 80)
print("ANALYTICS TABLE SCHEMA")
print("=" * 80)
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'analytics_events'
    ORDER BY ordinal_position;
""")
columns = cur.fetchall()
for col in columns:
    print(f"  {col[0]}: {col[1]}")

# Check if referrer column exists
has_referrer = any(col[0] == 'referrer' for col in columns)

if not has_referrer:
    print("\n[WARNING] 'referrer' column not found in analytics_events table")
    print("Traffic source tracking may not be configured.")
    cur.close()
    conn.close()
    exit(1)

print("\n" + "=" * 80)
print("SECTION 1: OVERALL TRAFFIC SOURCES")
print("=" * 80)

# Total events with referrer data
cur.execute("""
    SELECT 
        COUNT(*) as total_events,
        COUNT(CASE WHEN referrer IS NOT NULL AND referrer != '' THEN 1 END) as with_referrer,
        COUNT(CASE WHEN referrer IS NULL OR referrer = '' THEN 1 END) as no_referrer
    FROM analytics_events;
""")
result = cur.fetchone()
print(f"\nTotal analytics events: {result[0]}")
print(f"  Events with referrer: {result[1]} ({100.0*result[1]/result[0]:.1f}%)")
print(f"  Events without referrer (direct traffic): {result[2]} ({100.0*result[2]/result[0]:.1f}%)")

# Top referrers (raw URLs)
print("\n--- Top 20 Referrer URLs ---")
cur.execute("""
    SELECT 
        referrer,
        COUNT(*) as visits,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(DISTINCT session_id) as unique_sessions,
        MIN(timestamp) as first_seen,
        MAX(timestamp) as last_seen
    FROM analytics_events
    WHERE referrer IS NOT NULL AND referrer != ''
    GROUP BY referrer
    ORDER BY visits DESC
    LIMIT 20;
""")
referrers = cur.fetchall()
if referrers:
    for i, ref in enumerate(referrers, 1):
        print(f"\n  {i}. {ref[0]}")
        print(f"      Visits: {ref[1]}, Unique users: {ref[2]}, Unique sessions: {ref[3]}")
        print(f"      First seen: {ref[4]}, Last seen: {ref[5]}")
else:
    print("  No referrer data found")

print("\n" + "=" * 80)
print("SECTION 2: TRAFFIC SOURCES BY DOMAIN")
print("=" * 80)

# Get all referrers and parse domains
cur.execute("""
    SELECT referrer, COUNT(*) as count
    FROM analytics_events
    WHERE referrer IS NOT NULL AND referrer != ''
    GROUP BY referrer;
""")
all_referrers = cur.fetchall()

# Parse domains
domain_stats = defaultdict(int)
for ref, count in all_referrers:
    try:
        parsed = urlparse(ref)
        domain = parsed.netloc or 'direct'
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        domain_stats[domain] += count
    except:
        domain_stats['unknown'] += count

# Sort by count
sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)

print("\n--- Traffic by Domain ---")
total_with_referrer = sum(domain_stats.values())
for domain, count in sorted_domains[:20]:
    percentage = 100.0 * count / total_with_referrer if total_with_referrer > 0 else 0
    print(f"  {domain}: {count} visits ({percentage:.1f}%)")

print("\n" + "=" * 80)
print("SECTION 3: TRAFFIC SOURCE CATEGORIES")
print("=" * 80)

# Categorize traffic sources
categories = {
    'Search Engines': ['google', 'bing', 'yahoo', 'duckduckgo', 'baidu', 'yandex'],
    'Social Media': ['facebook', 'twitter', 'instagram', 'linkedin', 'reddit', 'tiktok', 'pinterest'],
    'Development/Tech': ['github', 'stackoverflow', 'localhost', '127.0.0.1', 'ngrok'],
    'Your Domain': ['training-monkey', 'yourtrainingmonkey', 'trainingmonkey'],
    'Strava': ['strava.com'],
    'Email': ['mail.', 'gmail.com', 'outlook.com', 'yahoo.com', 'webmail']
}

categorized = defaultdict(int)
uncategorized = []

for domain, count in sorted_domains:
    assigned = False
    for category, keywords in categories.items():
        if any(keyword in domain.lower() for keyword in keywords):
            categorized[category] += count
            assigned = True
            break
    if not assigned and domain != 'direct':
        uncategorized.append((domain, count))

print("\n--- Traffic by Category ---")
for category in ['Search Engines', 'Social Media', 'Strava', 'Your Domain', 'Development/Tech', 'Email']:
    if category in categorized:
        print(f"  {category}: {categorized[category]} visits")

if uncategorized:
    other_count = sum(count for _, count in uncategorized)
    print(f"  Other: {other_count} visits")

print("\n" + "=" * 80)
print("SECTION 4: USER SIGNUP REFERRERS")
print("=" * 80)

# Check for user signup events
cur.execute("""
    SELECT 
        event_type,
        COUNT(*) as count
    FROM analytics_events
    GROUP BY event_type
    ORDER BY count DESC;
""")
event_types = cur.fetchall()
print("\n--- Available Event Types ---")
for event_type, count in event_types[:10]:
    print(f"  {event_type}: {count}")

# Try to find signup-related events
cur.execute("""
    SELECT 
        referrer,
        COUNT(*) as signups
    FROM analytics_events
    WHERE event_type IN ('signup', 'user_signup', 'registration', 'account_created')
    AND referrer IS NOT NULL AND referrer != ''
    GROUP BY referrer
    ORDER BY signups DESC
    LIMIT 10;
""")
signup_referrers = cur.fetchall()

if signup_referrers:
    print("\n--- Top Referrers for Signups ---")
    for ref, count in signup_referrers:
        print(f"  {ref}: {count} signups")
else:
    print("\n[Note] No signup-specific events found in analytics")
    print("Consider tracking signup events with referrer data")

print("\n" + "=" * 80)
print("SECTION 5: RECENT TRAFFIC (Last 7 Days)")
print("=" * 80)

cur.execute("""
    SELECT 
        referrer,
        COUNT(*) as visits
    FROM analytics_events
    WHERE timestamp >= NOW() - INTERVAL '7 days'
    AND referrer IS NOT NULL AND referrer != ''
    GROUP BY referrer
    ORDER BY visits DESC
    LIMIT 10;
""")
recent_referrers = cur.fetchall()

if recent_referrers:
    print("\n--- Top Referrers (Last 7 Days) ---")
    for ref, count in recent_referrers:
        print(f"  {ref}: {count} visits")
else:
    print("\n[Note] No referrer data in last 7 days")

print("\n" + "=" * 80)
print("SECTION 6: RECOMMENDATIONS")
print("=" * 80)

print("\n[CURRENT STATUS]")
if result[1] > 0:
    print("  - You ARE tracking referrer data!")
    print(f"  - {result[1]} events with referrer information captured")
else:
    print("  - No referrer data captured yet")

print("\n[ADDITIONAL TRACKING OPTIONS]")
print("\n1. **Google Analytics 4 (GA4)** - Recommended")
print("   - Free, comprehensive web analytics")
print("   - Tracks: referrers, search keywords, user journeys, conversions")
print("   - Add to landing.html: Google Analytics tracking code")
print("   - Setup: analytics.google.com")

print("\n2. **UTM Parameters** - Track specific campaigns")
print("   - Add to your marketing links:")
print("   - Example: https://yourtrainingmonkey.com?utm_source=facebook&utm_medium=social&utm_campaign=launch")
print("   - Track in your analytics_tracker.py from URL parameters")

print("\n3. **Squarespace Analytics** (if using Squarespace for landing)")
print("   - Squarespace > Analytics > Traffic Sources")
print("   - Shows referrers, search terms, and geographic data")
print("   - Built-in, no setup required")

print("\n4. **First-Touch Attribution**")
print("   - Store referrer when user first visits (before signup)")
print("   - Link to user_settings table for conversion tracking")
print("   - Currently: referrer tracked per event, not per user")

print("\n" + "=" * 80)
print("END OF REPORT")
print("=" * 80)

cur.close()
conn.close()

