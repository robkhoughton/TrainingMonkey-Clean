# Autopsy-Informed Training Decision Fix
**Date**: November 3, 2025  
**Issue**: Training decisions not using autopsy analysis  
**Status**: FIXED

## Problem Identified

### **FACTS:**

The user reported contradictory recommendations:
- **AI Autopsy (Sunday, Nov 2)**: Recommended easy recovery run (4-6 miles, TRIMP 30-50)
- **Training Decision (Monday, Nov 3)**: Recommended build session with double the TRIMP (83.1)

Despite restructuring the workflow to generate training decisions AFTER autopsy completion, the decisions were not incorporating autopsy learnings.

### **ROOT CAUSE:**

In `llm_recommendations_module.py`, function `generate_recommendations()` (lines 755-770):

**BEFORE FIX:**
```python
# Line 755: Create prompt WITHOUT autopsy insights
prompt = create_enhanced_prompt_with_tone(current_metrics, activities, ...)

# Line 758: Call API
llm_response = call_anthropic_api(prompt)

# Line 761: Parse response
sections = parse_llm_response(llm_response)

# Line 764: Get autopsy insights (TOO LATE!)
autopsy_insights = get_recent_autopsy_insights(user_id, days=3)
```

**The Issue:**
- Autopsy insights were retrieved AFTER the LLM API call
- The prompt never included autopsy learnings
- Recommendations were only marked as "autopsy-informed" for tracking, but the LLM never saw the autopsy data

## Solution Implemented

### **CHANGES:**

#### 1. **Retrieve Autopsy Insights BEFORE Prompt Creation**
File: `app/llm_recommendations_module.py` (lines 755-770)

```python
# CRITICAL FIX: Get autopsy insights BEFORE creating prompt
autopsy_insights = get_recent_autopsy_insights(user_id, days=3)
is_autopsy_informed = bool(autopsy_insights and autopsy_insights.get('count', 0) > 0)

if is_autopsy_informed:
    logger.info(f"Generating autopsy-informed recommendation with {autopsy_insights['count']} recent autopsies")
else:
    logger.info("Generating standard recommendation without recent autopsy data")

# Pass autopsy insights to prompt creation
prompt = create_enhanced_prompt_with_tone(current_metrics, activities, pattern_analysis, 
                                         training_guide, user_id, tone_instructions, autopsy_insights)

# NOW call the API with autopsy-informed prompt
llm_response = call_anthropic_api(prompt)
```

#### 2. **Update Prompt Function to Accept and Use Autopsy Insights**
File: `app/llm_recommendations_module.py` (line 815)

**Function Signature Updated:**
```python
def create_enhanced_prompt_with_tone(current_metrics, activities, pattern_analysis, 
                                    training_guide, user_id, tone_instructions, autopsy_insights=None):
```

#### 3. **Build Autopsy Context Section**
File: `app/llm_recommendations_module.py` (lines 878-898)

```python
# Build autopsy context section if insights available
autopsy_context = ""
if autopsy_insights and autopsy_insights.get('count', 0) > 0:
    alignment_trend = autopsy_insights.get('alignment_trend', [])
    trend_description = "improving" if len(alignment_trend) >= 2 and alignment_trend[-1] > alignment_trend[0] else "mixed"
    
    autopsy_context = f"""
### RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses)
- Average Alignment Score: {autopsy_insights['avg_alignment']:.1f}/10
- Alignment Trend: {trend_description} ({alignment_trend})
- Latest Insights: {autopsy_insights.get('latest_insights', 'No specific insights')[:200]}

**COACHING ADAPTATION STRATEGY:**
- If alignment >7: Athlete follows guidance well - build on successful patterns
- If alignment 4-7: Address recurring deviations - simplify recommendations
- If alignment <4: Major strategy adjustment needed - focus on compliance over optimization

**IMPORTANT:** Use this autopsy learning to adapt today's recommendation. If recent alignment is low, 
recommend more conservative/achievable targets. If alignment is high, maintain current approach.
"""
```

#### 4. **Inject Autopsy Context into LLM Prompt**
File: `app/llm_recommendations_module.py` (line 922)

The autopsy context is now inserted between CURRENT METRICS and PATTERN ANALYSIS sections in the prompt:

```
### CURRENT METRICS (as of {current_date})
- External ACWR: {formatted_metrics['external_acwr']}
- Internal ACWR: {formatted_metrics['internal_acwr']}
- Days Since Rest: {formatted_metrics['days_since_rest']}
{autopsy_context}  ← AUTOPSY LEARNING INSERTED HERE
### PATTERN ANALYSIS
```

## Expected Behavior After Fix

### **Workflow Sequence:**

1. **User saves journal entry** with observations (energy, RPE, pain, notes)
2. **Autopsy generated** comparing prescribed vs actual workout
3. **Autopsy insights retrieved** (alignment score, trends, key learnings)
4. **Training decision generated** with autopsy context included in prompt
5. **LLM receives:**
   - Current metrics (ACWR, divergence, days since rest)
   - **Autopsy learning** (alignment scores, recent patterns, athlete behavior)
   - Pattern analysis
   - Training guide
6. **LLM generates** recommendation that:
   - Considers recent autopsy findings
   - Adapts to athlete's demonstrated preferences
   - Adjusts intensity/volume based on alignment history

### **Example - Low Alignment Scenario:**

If autopsy shows athlete consistently misaligns (alignment score 2/10):
- **Autopsy Context Injected:**
  ```
  ### RECENT AUTOPSY LEARNING (3 analyses)
  - Average Alignment Score: 2.3/10
  - Alignment Trend: mixed
  - Latest Insights: Athlete consistently exceeded prescribed intensity...
  
  COACHING ADAPTATION: Major strategy adjustment needed - focus on compliance over optimization
  ```
- **Expected Decision:** More conservative recommendation, simpler targets, emphasis on following the plan

### **Example - High Alignment Scenario:**

If autopsy shows athlete follows guidance well (alignment score 8/10):
- **Autopsy Context Injected:**
  ```
  ### RECENT AUTOPSY LEARNING (3 analyses)
  - Average Alignment Score: 8.2/10
  - Alignment Trend: improving
  - Latest Insights: Athlete demonstrated excellent recovery awareness...
  
  COACHING ADAPTATION: Build on successful patterns, athlete follows guidance well
  ```
- **Expected Decision:** Progressive recommendation, maintain current approach

## Testing Recommendations

1. **Save journal entry** for a completed workout with observations
2. **Verify autopsy generation** in database (`ai_autopsies` table)
3. **Check logs** for: `"Generating autopsy-informed recommendation with X recent autopsies"`
4. **Review training decision** on Journal page - should reflect autopsy learnings
5. **Compare metrics vs recommendation** - should show adaptive coaching based on alignment

## Technical Notes

- **Backward Compatible**: `autopsy_insights=None` parameter allows function to work without autopsy data
- **Graceful Degradation**: If no autopsy insights available, prompt excludes autopsy context section
- **Logging Enhanced**: Clear log messages distinguish autopsy-informed vs standard recommendations
- **No Breaking Changes**: Existing recommendation generation still works if autopsy system unavailable

## Files Modified

1. `app/llm_recommendations_module.py`
   - Line 755-770: Moved autopsy retrieval before prompt creation
   - Line 815: Updated function signature to accept `autopsy_insights`
   - Line 878-898: Added autopsy context building logic
   - Line 922: Injected autopsy context into LLM prompt

## Related Documents

- `AUTOPSY_WORKFLOW_FIX_SUMMARY.md` - Original autopsy workflow implementation
- `TOMORROW_ROW_FIX_SUMMARY.md` - UI display of autopsy-informed decisions
- `TRAININGMONKEY_SPECIFICATION.md` - Overall system architecture








