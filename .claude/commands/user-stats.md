---
allowed-tools: Bash
description: Report overall YTM user stats — totals, email types, activity, and journal engagement
---

Query the production database and display a platform-wide user stats report.

## Instructions

Run the following Python script from the project root (`C:\Users\robho\Documents\VAULT\TrainingMonkey-Clean`) via Bash:

```python
import sys
sys.path.insert(0, 'app')
from db_credentials_loader import set_database_url
set_database_url()

import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute('''
    SELECT
        COUNT(*)                                                          AS total_users,
        COUNT(*) FILTER (WHERE email NOT LIKE '%training-monkey.com%')   AS real_email,
        COUNT(*) FILTER (WHERE email LIKE '%training-monkey.com%')       AS strava_only_email
    FROM user_settings;
''')
total, real_email, strava_email = cur.fetchone()

cur.execute('''
    SELECT COUNT(DISTINCT user_id)
    FROM activities
    WHERE date >= CURRENT_DATE - INTERVAL '7 days';
''')
active_7d = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(DISTINCT user_id)
    FROM journal_entries;
''')
journaled_ever = cur.fetchone()[0]

cur.execute('''
    SELECT COUNT(DISTINCT user_id)
    FROM journal_entries
    WHERE date >= CURRENT_DATE - INTERVAL '7 days';
''')
journaled_7d = cur.fetchone()[0]

print('YTM User Stats')
print('=' * 45)
print(f'Total users:                    {total}')
print(f'  Real email address:           {real_email} ({real_email*100//total}%)')
print(f'  Strava-only email:            {strava_email} ({strava_email*100//total}%)')
print()
print(f'Active last 7 days (activity):  {active_7d} ({active_7d*100//total}%)')
print()
print(f'Ever journaled:                 {journaled_ever} ({journaled_ever*100//total}%)')
print(f'Journaled last 7 days:          {journaled_7d} ({journaled_7d*100//total}%)')

cur.close()
conn.close()
```

Present the results in a clean markdown table with a brief commentary on notable patterns.
