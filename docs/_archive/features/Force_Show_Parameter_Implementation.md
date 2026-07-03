# Force Show Parameter Implementation

## Overview
A debugging technique to bypass normal application logic and force a specific behavior using URL parameters.

## Implementation

### Route Handler Modification
```python
@app.route('/welcome-post-strava')
@login_required
def welcome_post_strava():
    user_id = current_user.id
    
    # Check for force_show parameter to bypass onboarding check
    force_show = request.args.get('force_show', 'false').lower() == 'true'
    
    # Check if user needs onboarding
    if needs_onboarding(user_id) or force_show:
        return render_template('welcome_post_strava.html', 
                             show_onboarding=True, 
                             user_id=user_id)
    else:
        return redirect(url_for('dashboard'))
```

### Usage
**Normal URL:** `http://localhost:5001/welcome-post-strava`
**Force Show URL:** `http://localhost:5001/welcome-post-strava?force_show=true`

### Logic Breakdown
1. `request.args.get('force_show', 'false')` - Gets URL parameter, defaults to 'false'
2. `.lower() == 'true'` - Converts to boolean (case-insensitive)
3. `needs_onboarding(user_id) or force_show` - OR logic bypasses normal check

### When to Use
- **Debugging**: Bypass conditional logic to test specific code paths
- **Testing**: Force specific UI states for manual testing
- **Troubleshooting**: Isolate issues by eliminating variables

### When NOT to Use
- **Production**: Remove debugging parameters before deployment
- **Security**: Never bypass authentication or authorization checks
- **Permanent Features**: Use proper configuration instead of URL parameters

### Cleanup
Always remove debugging parameters after resolving issues:
```python
# Remove this line after debugging
force_show = request.args.get('force_show', 'false').lower() == 'true'

# Remove from condition
if needs_onboarding(user_id):  # Remove 'or force_show'
```

## Pattern Summary
**URL Parameter → Boolean → Conditional Logic Bypass**

This pattern can be applied to any conditional logic that needs temporary bypassing for debugging purposes.
