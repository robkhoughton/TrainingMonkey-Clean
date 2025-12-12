# Code Quality Standards

## General Principles

- **Public APIs**: Use intended public methods; avoid calling private/internal methods
- **Error Handling**: Provide meaningful error messages; fail gracefully with user feedback
- **Clean Code**: Remove debugging artifacts (console.log, print statements) before completion
- **Minimal Changes**: Only modify what's necessary; don't refactor unrelated code

## Security

### SQL Injection Prevention

Always use parameterized queries:

```python
# CORRECT
db_utils.execute_query("SELECT * FROM users WHERE id = %s", (user_id,), fetch=True)

# WRONG - vulnerable to injection
db_utils.execute_query(f"SELECT * FROM users WHERE id = {user_id}", fetch=True)
```

### Credential Handling

- Never hardcode credentials, API keys, or DATABASE_URL
- Always load from `.env` via `db_credentials_loader`
- Never commit `.env` files to git

## Python Standards

```python
# Use explicit commits for database operations
conn = get_connection()
try:
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    cursor.close()
    conn.close()

# Or use context managers
with db_utils.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(query, params)
```

## TypeScript Standards

```typescript
// Define interfaces for API responses
interface ActivityResponse {
  id: number;
  name: string;
  date: string;  // YYYY-MM-DD format
}

// Handle async errors
try {
  const data = await fetchActivities();
} catch (error) {
  console.error('Failed to fetch activities:', error);
  setError('Unable to load activities. Please try again.');
}
```

## Testing

- **Root Cause Analysis**: Check database state before making assumptions
- **End-to-End**: Test complete user flows, not just individual components
- **Local First**: Test all changes locally before deployment

## Code Review Checklist

Before completing a task:
- [ ] No SQLite syntax (use PostgreSQL: `%s`, `SERIAL`, `NOW()`)
- [ ] No hardcoded credentials
- [ ] All queries use parameterized placeholders
- [ ] New Python files added to Dockerfile.strava
- [ ] Frontend changes built and copied to app/static/
- [ ] Debugging code removed
- [ ] Error handling provides useful messages
