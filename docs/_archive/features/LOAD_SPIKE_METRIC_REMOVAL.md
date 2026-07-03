# Load Spike Metric Removal Summary

**Date:** October 27, 2025  
**Type:** Conceptual Fix - Training Load Analysis Methodology

## Problem Identified

The system was using a "load spike above 7-day average" metric that fundamentally contradicted ACWR (Acute-Chronic Workload Ratio) principles:

- **Flawed Logic**: Compared single-day load to 7-day average
- **Not ACWR**: ACWR compares 7-day acute average to 28-42 day chronic average
- **Conflicting Signals**: LLM received both proper ACWR values AND misleading spike warnings

## Why This Was Counterproductive

**Example Scenario** (reported by user):
- Light training days (3-4 mi) to manage load
- Scheduled long run (15 mi)
- **Result**: 
  - ✅ ACWR stays optimal (1.0-1.1) - **GOOD TRAINING**
  - ❌ "Load spike" flags 200%+ warning - **FALSE ALARM**

This penalized smart periodization and load management strategies that intentionally use lighter days before higher-load sessions.

## Changes Made

### 1. Code Changes (`app/llm_recommendations_module.py`)
- Removed calculation logic from `analyze_pattern_flags()` function (lines 235-243)
- Removed `load_spike_percent` thresholds from all risk tolerance profiles:
  - Conservative: was 1.4 (140% threshold)
  - Balanced: was 1.5 (150% threshold)
  - Adaptive: was 1.55 (155% threshold)
  - Aggressive: was 1.7 (170% threshold)
- Removed "Load Spike Warning" line from LLM prompt in `create_enhanced_prompt_with_tone()`
- Updated function docstrings

### 2. Documentation Changes
- **`app/Training_Metrics_Reference_Guide.md`**: Removed "Load Spike Sensitivity" from Red Flag Patterns
- **`app/templates/tutorials.html`**: Removed "Load Spike Sensitivity" references (2 locations)

### 3. Verification
- Confirmed no remaining references to `load_spike` in codebase
- No linter errors introduced

## What Remains (Valid ACWR Methodology)

The system continues to use proper evidence-based metrics:

1. **External ACWR** = 7-day acute load avg / 28-42 day chronic load avg (exponentially weighted)
2. **Internal ACWR** = 7-day acute TRIMP avg / 28-42 day chronic TRIMP avg (exponentially weighted)
3. **Normalized Divergence** = Balance between external and internal stress
4. **Volume Sensitivity** = How ACWR responds to weekly volume increases (valid pattern recognition)

## Impact

✅ **Positive Outcomes:**
- LLM recommendations now focus on proper ACWR methodology
- Smart periodization strategies (light days + scheduled hard days) are properly recognized
- No more conflicting signals between ACWR and "spike" warnings
- Cleaner, more consistent training load analysis

❌ **No Negative Impact:**
- Proper ACWR calculation already captures problematic load increases
- Chronic ACWR elevation detection (>1.3 for 5+ days) remains active
- All other red flag patterns remain functional

## Implementation Notes

- Changes are backward compatible (only removes unused threshold parameter)
- No database schema changes required
- No API contract changes
- Existing user data unaffected

## Testing Recommendations

When deploying:
1. Verify LLM recommendations no longer reference "load spike above 7-day average"
2. Confirm ACWR-based recommendations remain functional
3. Test scenario: light days → long run should not trigger false warnings
4. Check pattern analysis flags only show ACWR-based concerns

---

**Conclusion**: This fix aligns the system entirely with evidence-based ACWR methodology, eliminating a metric that was conceptually flawed and counterproductive to proper training load management.

