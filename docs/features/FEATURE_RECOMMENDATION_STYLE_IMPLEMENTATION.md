# Recommendation Style Feature Implementation

## Summary
Successfully implemented the **Recommendation Style** (Conservative/Balanced/Adaptive/Aggressive) feature that adjusts AI decision framework thresholds based on user preferences.

## What Was Implemented

### 1. New Functions Added to `llm_recommendations_module.py`

#### `get_user_recommendation_style(user_id)`
- Fetches user's recommendation_style preference from database
- Returns: 'conservative', 'balanced', 'adaptive', or 'aggressive'
- Defaults to 'balanced' if not set

#### `get_adjusted_thresholds(recommendation_style)`
- Returns personalized risk thresholds based on training philosophy
- Adjusts 6 key safety parameters based on user preference

### 2. Adjusted Thresholds by Style

| Threshold | Conservative | Balanced | Adaptive | Aggressive |
|-----------|--------------|----------|----------|------------|
| **ACWR High Risk** | >1.2 | >1.3 | >1.35 | >1.5 |
| **Load Spike Warning** | >140% | >150% | >155% | >170% |
| **Days Without Rest** | 6 days | 7 days | 7 days | 8 days |
| **Divergence Overtraining** | <-0.10 | <-0.15 | <-0.15 | <-0.20 |
| **Divergence Moderate Risk** | <-0.03 | <-0.05 | <-0.05 | <-0.08 |
| **ACWR Undertraining** | <0.85 | <0.8 | <0.8 | <0.75 |

### 3. Updated Functions

#### `analyze_pattern_flags(activities, current_metrics, user_id, thresholds)`
- Now accepts user_id and thresholds parameters
- Uses personalized thresholds for pattern detection
- Warnings now show actual spike percentage
- ACWR elevation warnings reference user's specific threshold

#### `create_enhanced_prompt()` and `create_enhanced_prompt_with_tone()`
- Fetch user's recommendation_style at generation time
- Apply adjusted thresholds to decision framework logic
- Pass risk tolerance context to Claude AI
- Include personalized thresholds in prompt

### 4. AI Prompt Integration

The AI now receives:
```
ATHLETE RISK TOLERANCE: CONSERVATIVE (Lower risk tolerance, earlier warnings, more recovery emphasis)
- ACWR High Risk Threshold: >1.2
- Load Spike Warning: >40% above 7-day average
- Maximum Days Without Rest: 6 days
- Divergence Overtraining Risk: <-0.10
```

And instructions to:
- Use athlete's personalized thresholds (NOT standard guide thresholds)
- Adjust recommendations to match athlete's risk tolerance
- Interpret metrics relative to athlete's specific thresholds

## How It Works

### User Flow
1. User sets "Recommendation Style" in Settings → Coaching Settings
2. Selection is saved to `user_settings.recommendation_style` in database
3. When AI generates recommendations:
   - System fetches user's recommendation_style
   - Loads corresponding adjusted thresholds
   - Applies thresholds to decision framework
   - Claude receives personalized context
   - AI provides recommendations aligned with user's risk tolerance

### Example Scenario

**Same Training Data, Different Styles:**

**Metrics:**
- External ACWR: 1.25
- Internal ACWR: 1.28
- Load spike: 60% above 7-day average
- 5 days since rest

**Conservative User:**
- ⚠️ ACWR HIGH RISK (>1.2 threshold exceeded)
- ⚠️ LOAD SPIKE WARNING (>40% threshold exceeded)
- Recommendation: "Reduce load, active recovery recommended"

**Balanced User:**
- ✅ ACWR in optimal zone (1.25 < 1.3 threshold)
- ⚠️ Load spike detected (>50% threshold)
- Recommendation: "Moderate intensity, monitor response"

**Aggressive User:**
- ✅ ACWR well within tolerance (1.25 < 1.5 threshold)
- ✅ Load spike acceptable (<70% threshold)
- Recommendation: "Maintain intensity, push for progression"

## Technical Details

### Database Integration
- Uses existing `user_settings.recommendation_style` column
- No database schema changes required
- Falls back to 'balanced' if NULL

### Logging
The system now logs:
```
User {user_id} recommendation_style: aggressive
Using aggressive thresholds: Higher risk tolerance, aggressive progression, performance-focused
Risk tolerance: aggressive (ACWR threshold: 1.5)
```

### Backwards Compatibility
- Existing users without recommendation_style set default to 'balanced'
- Standard evidence-based thresholds unchanged for balanced users
- No breaking changes to existing functionality

## Testing Recommendations

1. **Test each style setting:**
   - Set recommendation_style to 'conservative'
   - Generate recommendations
   - Verify ACWR threshold is 1.2 in logs
   - Check that warnings appear earlier

2. **Test load spike detection:**
   - Create a training day with 2x average load
   - Conservative should warn, Aggressive should not

3. **Test decision framework:**
   - With ACWR of 1.25:
     - Conservative: Should recommend caution
     - Aggressive: Should allow progression

4. **Verify logging:**
   - Check `llm_recommendations.log` for threshold logging
   - Confirm user's style is being fetched correctly

## Future Enhancements

Potential additions:
1. Allow users to customize individual thresholds
2. Add "learning mode" that adjusts thresholds based on user's actual adherence
3. Seasonal adjustment (more conservative in base phase, aggressive in build phase)
4. Injury history integration (automatic conservative mode after injury)

## Code Locations

- **Main implementation:** `app/llm_recommendations_module.py`
  - Lines 1380-1390: `get_user_recommendation_style()`
  - Lines 1402-1455: `get_adjusted_thresholds()`
  - Lines 162-245: Updated `analyze_pattern_flags()`
  - Lines 256-368: Updated `create_enhanced_prompt()`
  - Lines 779-915: Updated `create_enhanced_prompt_with_tone()`

- **UI Settings:** `app/templates/settings_coaching.html`
  - Lines 91-129: Recommendation Style selector

## Deployment Notes

- ✅ No database migrations required
- ✅ Backwards compatible
- ✅ No breaking changes
- ✅ Existing recommendations remain valid
- ⚠️ Users should regenerate recommendations after changing style

## Success Criteria

✅ User's recommendation_style preference is fetched from database  
✅ Adjusted thresholds are calculated based on preference  
✅ Pattern flag detection uses personalized thresholds  
✅ Decision framework applies personalized thresholds  
✅ AI receives risk tolerance context in prompt  
✅ Load spike warnings show actual percentage  
✅ Logging includes threshold information  
✅ No linter errors  
✅ Backwards compatible  

---

**Implementation Date:** 2025-09-30  
**Status:** ✅ Complete and Ready for Testing

























