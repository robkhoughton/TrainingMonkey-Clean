# Autopsy Fix Summary - November 15, 2025

## Problem
- Autopsy showing fallback message: "Detailed comparison requires enhanced AI analysis"
- Tomorrow's Training Decision not being generated
- User concerned about being out of API tokens

## Root Causes Found

### 1. API Token Limit Too Low
**Issue:** `call_anthropic_api()` was hardcoded to 2000 tokens, not using the 3000 tokens specified in `config.json` for autopsy analysis.

**Fix:** Added `max_tokens` parameter to `call_anthropic_api()` and updated autopsy generation to use config settings.

### 2. Insufficient Error Logging
**Issue:** When API calls failed, the error details weren't logged, making it hard to diagnose issues.

**Fix:** 
- Added detailed error logging with specific messages for 401, 429, 400 status codes
- Added `exc_info=True` to log full stack traces
- Added 30-second timeout to API requests
- Log actual API parameters for debugging

### 3. Tomorrow's Recommendation Date Logic
**Issue:** `update_recommendations_with_autopsy_learning()` only worked for past dates, not today.

**Fix:** Changed date check from `<` to `<=` to allow today's date to generate tomorrow's recommendation.

## API Status Check

**Local Test Result:** ✅ API is working
- Status Code: 200
- Response: "API test successful"
- Tokens used: 18 input + 6 output

**Conclusion:** You are NOT out of tokens locally. The API key is valid and working.

## Potential Model Name Issue

**Config uses:** `claude-sonnet-4.5-20250929`
**Test used:** `claude-sonnet-4-20250514` (works)

The model name in config.json might not be a valid model identifier. This could cause API failures on the deployed version.

## Next Steps

### 1. Check Cloud Run Logs
Look for these error messages in your deployed application logs:
```
"API call failed with status code"
"Authentication failed"
"Rate limit exceeded"
"Bad request - check prompt format"
```

### 2. Update Model Name (if needed)
Edit `app/config.json`:
```json
{
    "llm_settings": {
        "model": "claude-sonnet-4-20250514",  // Use this instead
        ...
    }
}
```

### 3. Redeploy Application
The fixes won't take effect until you deploy:
```bash
# Your normal deployment process
```

### 4. Test After Deployment
1. Save a journal entry for a completed workout
2. Check that the autopsy is generated (not fallback)
3. Check that "Tomorrow's Training Decision" appears

## Diagnostic Tools

### Check API Status Locally
```bash
python check_anthropic_api.py
```

This will show:
- API key status
- Connectivity
- Credit status
- Specific error messages

### Find Unused Code
```bash
python find_unused_code.py
```

Identifies deprecated and unused functions for cleanup.

## Files Modified

1. `app/llm_recommendations_module.py`
   - Added `max_tokens` parameter to `call_anthropic_api()`
   - Updated autopsy generation to use config settings
   - Enhanced error logging
   - Fixed date logic for tomorrow's recommendations

2. `check_anthropic_api.py`
   - New diagnostic script to test API connectivity

3. `app/strava_app.py` (previous fix)
   - Fixed to call correct autopsy function
   - Fixed to call `update_recommendations_with_autopsy_learning()`

## Commits

- `73ee11c` - Fix tomorrow's training decision generation after journal save
- `57f1570` - Fix autopsy API call to use config settings and improve error logging
- `1521bb8` - Add Anthropic API diagnostic script

## Summary

The code fixes are complete and pushed. The API is working locally. To resolve the issue:

1. **Deploy the latest code** - The fixes won't work until deployed
2. **Check the model name** - May need to update to valid model identifier
3. **Monitor logs** - Check Cloud Run logs for specific error messages
4. **Test thoroughly** - Verify autopsy and tomorrow's decision generation

If issues persist after deployment, check the logs for specific error codes (401, 429, 400) to diagnose further.

