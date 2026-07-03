# LLM Recommendations Comparison: Dashboard vs Coach Page

**Date**: November 30, 2025  
**Issue**: Strategic context on Coach page is less robust than original Dashboard LLM recommendations

---

## COMPARISON SUMMARY

### **Original Dashboard LLM Recommendations** (`llm_recommendations_module.py`)

**Purpose**: Comprehensive daily training decisions with pattern analysis  
**Frequency**: Generated daily at 6 AM UTC  
**Display Location**: Dashboard page (now removed)  
**Database Table**: `llm_recommendations`

**Three Sections**:
1. **DAILY RECOMMENDATION** (~150-200 words)
   - Applies Decision Framework: Safety → Overtraining → ACWR → Recovery → Progression
   - Uses athlete's personalized risk tolerance thresholds
   - Includes specific volume/intensity targets
   - References current 7-day averages
   - Evidence-based with specific numbers

2. **WEEKLY PLANNING** (~100-150 words)
   - Weekly planning priorities from Training Guide
   - Addresses red flags and positive patterns
   - Specific ACWR management strategies
   - Athlete profile considerations

3. **PATTERN INSIGHTS** (~100-150 words)
   - 2-3 specific observations using pattern recognition framework
   - Metrics relative to personalized thresholds
   - Forward-looking trend analysis
   - Identifies red flags and positive patterns

**Total**: ~350-500 words of detailed coaching guidance

---

### **Current Coach Page Strategic Context** (`coach_recommendations.py`)

**Purpose**: Brief strategic narrative for weekly workout plan context  
**Frequency**: Generated weekly (or on-demand)  
**Display Location**: Coach page below weekly workout plan  
**Database Table**: `weekly_programs` (embedded in JSON)

**Three Fields**:
1. **weekly_focus** (2-3 sentences)
   - Primary training goal this week
   - How it aligns with training stage

2. **load_management_strategy** (2-3 sentences)
   - ACWR targets and predicted outcomes
   - Volume/intensity balance rationale

3. **pattern_insights** (2-3 sentences)
   - Recent training response observations
   - Key adaptations or concerns to monitor

**Total**: ~6-9 sentences (~100-150 words) of brief context

---

## KEY DIFFERENCES

| Aspect | Dashboard LLM Recommendations | Coach Page Strategic Context |
|--------|------------------------------|------------------------------|
| **Depth** | Comprehensive (~400 words) | Brief (~125 words) |
| **Frequency** | Daily | Weekly |
| **Focus** | Daily tactical decisions | Weekly strategic context |
| **Framework** | Full Training Guide analysis | Summary insights only |
| **Risk Tolerance** | Personalized thresholds | Generic guidance |
| **Pattern Analysis** | Detailed red flags, warnings, positive patterns | High-level observations |
| **Athlete Profile** | Considers athlete type, risk tolerance | Generic approach |
| **Autopsy Integration** | Learns from recent autopsies | No autopsy learning |
| **ACWR Specifics** | References athlete's specific thresholds | General ACWR guidance |
| **Decision Framework** | Explicit Safety→Overtraining→ACWR→Recovery→Progression | Implicit |
| **Coaching Tone** | Personalized (3-spectrum system) | Generic expert tone |

---

## WHAT'S MISSING ON COACH PAGE

### 1. **Pattern Analysis System**
Dashboard had sophisticated pattern recognition:
```python
Red Flags: {', '.join(pattern_flags['red_flags']) if pattern_flags['red_flags'] else 'None detected'}
Positive Patterns: {', '.join(pattern_flags['positive_patterns']) if pattern_flags['positive_patterns'] else 'None identified'}
Warnings: {', '.join(pattern_flags['warnings']) if pattern_flags['warnings'] else 'None'}
```

Coach page: No pattern flag analysis

### 2. **Personalized Risk Tolerance**
Dashboard prompt:
```
ATHLETE RISK TOLERANCE: {recommendation_style.upper()} ({thresholds['description']})
- ACWR High Risk Threshold: >{thresholds['acwr_high_risk']}
- Maximum Days Without Rest: {thresholds['days_since_rest_max']} days
- Divergence Overtraining Risk: <{thresholds['divergence_overtraining']}
```

Coach page: Uses generic thresholds

### 3. **Autopsy Learning Integration**
Dashboard includes:
```
RECENT AUTOPSY LEARNING ({autopsy_insights['count']} analyses):
- Average Alignment Score: {autopsy_insights['avg_alignment']}/10
- Alignment Trend: {trend_description}
- Key Learning: {autopsy_insights['latest_insights']}
```

Coach page: No autopsy learning

### 4. **Detailed Athlete Profile**
Dashboard includes:
```
Athlete Type: {athlete_profile}
Analysis Period: {start_date} to {end_date} ({days_analyzed} days)
Assessment Category: {assessment_category}
```

Coach page: No athlete classification

### 5. **Explicit Decision Framework**
Dashboard instructions:
```
**DAILY RECOMMENDATION:**
- Apply the Decision Framework assessment order (Safety → Overtraining → ACWR → Recovery → Progression)
- Use the athlete's risk tolerance thresholds listed above (NOT the standard guide thresholds)
- Include specific volume/intensity targets based on current 7-day averages
```

Coach page: No explicit framework application

### 6. **Coaching Tone Personalization**
Dashboard uses 3-spectrum coaching tone system (Supportive/Balanced/Direct)  
Coach page: Single generic expert tone

---

## WHY THEY'RE DIFFERENT SYSTEMS

### **Dashboard LLM Recommendations** = **Daily Tactical Coach**
- Answers: "What should I do TODAY?"
- Deep dive into current metrics
- Personalized to athlete's risk tolerance
- Learns from recent autopsy feedback
- Applies explicit Decision Framework
- ~400 words of detailed guidance

### **Coach Page Strategic Context** = **Weekly Planning Context**
- Answers: "WHY am I doing this week's workouts?"
- High-level strategic overview
- Generic coaching approach
- No learning loop
- Implicit framework
- ~125 words of brief context

---

## THE PROBLEM

**User's observation is correct**: The strategic context on Coach page is much less robust than the original Dashboard LLM recommendations.

**What happened**:
1. We added strategic context to Coach page (new feature ✅)
2. We did NOT actually move the Dashboard recommendations (oversight ❌)
3. The strategic context is intentionally brief (design choice for weekly plan context)
4. But we lost the detailed, personalized daily coaching guidance

---

## RECOMMENDATIONS

### **Option 1: Restore Dashboard Recommendations Alongside Strategic Context**
- Keep Coach page strategic context (weekly overview)
- Restore Dashboard LLM recommendations (daily tactical guidance)
- Two different purposes, both valuable

### **Option 2: Move Full Dashboard Recommendations to Coach Page**
- Add a separate "Daily Training Decision" section on Coach page
- Display latest daily recommendation (from `llm_recommendations` table)
- Keep strategic context for weekly overview
- Creates complete coaching ecosystem on one page

### **Option 3: Enhance Strategic Context to Match Dashboard Depth**
- Expand strategic context from 3 brief fields to 3 comprehensive sections
- Add pattern analysis, risk tolerance, autopsy learning to weekly program prompt
- Make strategic context as detailed as Dashboard recommendations
- Replace Dashboard recommendations entirely

### **Option 4: Create Unified System** (Most Complex)
- Merge `llm_recommendations_module` and `coach_recommendations` into one system
- Generate both daily decisions AND weekly programs from single comprehensive analysis
- Eliminate redundancy while preserving depth
- Major refactoring required

---

## RECOMMENDED APPROACH

**Implement Option 2**: Move Full Dashboard Recommendations to Coach Page

**Rationale**:
1. **Preserves all existing functionality** - No loss of sophisticated coaching guidance
2. **Achieves original PRD goal** - Consolidates coaching on Coach page
3. **Minimal code changes** - Just add display section, no prompt rewrite needed
4. **Clear separation of concerns**:
   - Daily Decision: Tactical, detailed, personalized (~400 words)
   - Weekly Overview: Strategic, concise, plan context (~125 words)
   - Workout Plan: Structured daily workouts (existing)

**Implementation Steps**:
1. Fetch latest daily recommendation from `/api/llm-recommendations` on Coach page
2. Add "Daily Training Decision" section below Weekly Strategy & Context
3. Display three subsections: Daily Recommendation, Weekly Planning, Pattern Insights
4. Keep existing strategic context for weekly plan context
5. Remove from Dashboard (already done partially)

**Result**: Coach page becomes comprehensive coaching hub with both daily tactical guidance AND weekly strategic context.

---

## CONCLUSION

The Coach page strategic context is working as designed (brief weekly overview), but we inadvertently failed to complete the original mission of moving the sophisticated Dashboard LLM recommendations to the Coach page.

The strategic context is NOT a replacement for the Dashboard recommendations - they serve different purposes (weekly vs daily, strategic vs tactical).

**Action Required**: Decide which option to implement to restore the full coaching guidance that was on the Dashboard.

