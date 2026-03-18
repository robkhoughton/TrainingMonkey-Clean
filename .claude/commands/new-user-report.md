---
allowed-tools: Bash
description: Report new YTM users for a given year with email, primary sport, and activity count
---

Query the production database and display a new user report.

## Instructions

1. Determine the year to report on:
   - If the user specified a year (e.g. `/new-user-report 2025`), use that year
   - Otherwise default to the current year

2. Run the following Python script via Bash:

```python
import sys
sys.path.insert(0, 'app')
from db_credentials_loader import set_database_url
set_database_url()

import psycopg2, os

YEAR = "$YEAR"  # substituted below

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute('''
    SELECT
        us.email,
        us.primary_sport,
        COUNT(a.activity_id) AS activity_count,
        us.created_at::date AS joined
    FROM user_settings us
    LEFT JOIN activities a ON a.user_id = us.id
    WHERE us.created_at >= %s AND us.created_at < %s
    GROUP BY us.id, us.email, us.primary_sport, us.created_at
    ORDER BY us.created_at DESC;
''', (f'{YEAR}-01-01', f'{int(YEAR)+1}-01-01'))

rows = cur.fetchall()
print(f'New users in {YEAR}: {len(rows)}')
print()
print(f'{"Email":<45} {"Primary Sport":<20} {"Activities":>10}  Joined')
print('-' * 95)
for email, sport, count, joined in rows:
    print(f'{str(email or "(no email)"):<45} {str(sport or "not set"):<20} {count:>10}  {joined}')

# Summary breakdown
from collections import Counter
sports = Counter(sport or 'not set' for _, sport, _, _ in rows)
print()
print('Sport breakdown:')
for sport, n in sports.most_common():
    print(f'  {sport:<20} {n}')

strava_only = sum(1 for email, _, _, _ in rows if email and 'training-monkey.com' in str(email))
no_activity = sum(1 for _, _, count, _ in rows if count == 0)
print()
print(f'  Strava-only accounts (no real email): {strava_only}')
print(f'  Users with 0 activities:              {no_activity}')

cur.close()
conn.close()
```

3. Run the script from the project root (`C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean`) substituting the actual year value — do not leave `$YEAR` as a literal string.

4. Present the results in a clean markdown table.
