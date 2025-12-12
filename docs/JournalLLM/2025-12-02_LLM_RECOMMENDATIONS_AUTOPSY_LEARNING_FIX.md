# LLM Recommendations & Autopsy Learning System Overhaul
**Date:** December 2, 2025
**Session Type:** Critical Bug Fixes & System Architecture Improvements

---

## Executive Summary

This session addressed critical bugs in the LLM recommendation system and fundamentally improved how autopsy-informed learning influences training decisions. The primary issue was that the system was ignoring injury/medical status from autopsy analysis and user notes, instead defaulting to ACWR-based volume optimization that could harm injured athletes.

**Key Result:** Established medical safety as the highest priority in the decision hierarchy, overriding all other metrics when injury or medical constraints are present.

---

## Initial Problem Identified

### Primary Issues:
1. **Display Bug:** "Today's Training Decision" column showing full recommendation (daily + weekly + pattern sections, ~2500+ chars) instead of just the daily section (~150-200 words)
2. **Button Logic Bug:** Save button not appearing when journal observations entered on Rest Day
3. **Critical Safety Issue:** System prescribing aggressive training despite:
   - 2/10 autopsy alignment score
   - User notes explicitly stating "rehabilitation of Achilles/ankle/plantar fasciitis issues"
   - Autopsy recommending "abandon volume-based prescriptions, treadmill only until 7 pain-free days"

### User's Live Example:
**Autopsy for Dec 2:**
- Alignment: 2/10
- Analysis: "Critical coaching failure - prescription ignored active injury status requiring rehabilitation protocol"
- Recommendation: "Immediate protocol change: Abandon volume-based prescriptions. Continue treadmill until 7 consecutive pain-free days."

**User's Notes:**
- "super easy treadmill effort aimed at rehabilitation of Achilles/ankle/plantar fasciitis issues"

**System's Next Recommendation (Dec 3) - WRONG:**
- 10-12 miles with 1,200-1,500ft elevation gain
- TRIMP 65-80 (moderate intensity)
- **Completely ignored injury rehabilitation needs!**

---

## Phase 1: Comprehensive Code Audit

**User's Decision:** Before making parser changes, conduct full audit of LLM recommendation system for conflicts/duplication

### Key Findings:

#### 1. **CRITICAL: Duplicate Function**
- `get_user_coaching_spectrum()` defined TWICE (lines 1251 and 1688)
- Line 1688 version was **active** but lacked fallback logic for `coaching_tone` migration
- Line 1251 version had proper fallback: `coaching_tone` → `coaching_style_spectrum` mapping
- **Impact:** Silent failures when spectrum value was NULL but coaching_tone was set

#### 2. **Format Mismatch**
- **Prompt requests:** `**DAILY RECOMMENDATION:**` (bold with colon)
- **Claude returns:** `DAILY RECOMMENDATION` (plain text, no colon)
- **Parser expected:** Bold format with asterisks
- **Result:** Parser failed to match → fell back to dumping all 3 sections into `daily_recommendation` field

#### 3. **System Architecture Mapped**
Three separate LLM systems identified:
- **Dashboard System:** Daily/weekly recommendations (3-part format)
- **Weekly Program System:** Coach page 7-day plans (JSON format)
- **Autopsy System:** Training analysis with alignment scoring

---

## Phase 2: Critical Infrastructure Fixes

### Fix 1: Removed Duplicate Function ✅
**File:** `app/llm_recommendations_module.py`
**Action:** Deleted inferior `get_user_coaching_spectrum()` at line 1688
**Verification:** Python test confirmed line 1251 version now active with proper fallback logic

**Impact:** Coaching tone fallback now works correctly for users migrating from old `coaching_tone` to new `coaching_style_spectrum` field

---

### Fix 2: Frontend Button Logic ✅
**File:** `frontend/src/JournalPage.tsx`
**Lines:** 889-918

**Before:**
```javascript
// State 0: Today + Rest Day + Not Saved → Show "Mark as Rest Day"
// State 1: Has unsaved changes → Show "Save"
// Problem: State 0 checked FIRST, blocking State 1
```

**After:**
```javascript
// State 1: Has unsaved changes → Show "Save" (CHECK THIS FIRST)
// State 0: Today + Rest Day + NO observations → Show "Mark as Rest Day"
```

**Impact:** Save button now appears when observations entered, even if activity is marked as Rest Day

---

### Fix 3: Parser Format Updates ✅
**File:** `app/llm_recommendations_module.py`
**Lines:** 1080-1115, 1871-1885

#### Updated Prompt (line 1871-1885):
**Before:**
```
**DAILY RECOMMENDATION:**
**WEEKLY PLANNING:**
**PATTERN INSIGHTS:**
```

**After:**
```
REQUIRED OUTPUT FORMAT (CRITICAL - FOLLOW EXACTLY):

Your response must have exactly three sections with these headers on their own lines:

DAILY RECOMMENDATION

WEEKLY PLANNING

PATTERN INSIGHTS
```

#### Updated Parser (line 1080-1115):
Now tries 3 formats in order of preference:

1. **Plain text headers** (what Claude currently returns):
   ```regex
   ^DAILY\s+RECOMMENDATION\s*\n+
   ```

2. **Bold headers with colons** (legacy format):
   ```regex
   \*\*DAILY\s+RECOMMENDATION:?\*\*
   ```

3. **Markdown headers** (older fallback):
   ```regex
   ##\s*DAILY\s+RECOMMENDATION
   ```

#### Added Format Detection Logging:
```python
logger.info(f"✅ Found daily section ({format_used}): {len(sections['daily_recommendation'])} chars")
```

**Impact:** Parser now handles multiple Claude response formats robustly

---

## Phase 3: Autopsy Learning System Overhaul

### Root Causes Identified:

#### 1. **Autopsy Insights Severely Truncated**
**Location:** `llm_recommendations_module.py:1621-1623, 1821`

**Problem:**
- Autopsy analysis extracted: First 200 chars (line 1623)
- Then truncated AGAIN in prompt: First 150 chars (line 1821)
- **Result:** Out of comprehensive autopsy like "Critical coaching failure. Prescription ignored active injury status requiring rehabilitation protocol. Your Achilles/ankle/plantar fasciitis complex demands 4-6 week progressive loading...", only first 150 chars reached the recommendation prompt

#### 2. **Blanket Assumption: Low Alignment = Non-Compliance**
**Location:** `llm_recommendations_module.py:1823-1828, 1864-1867`

**Old Logic:**
```
COACHING ADAPTATION STRATEGY:
- If alignment >7: Build on successful patterns
- If alignment 4-7: Address recurring deviations, simplify recommendations
- If alignment <4: Major strategy change needed, focus on compliance over optimization

ADAPTIVE COACHING LOGIC:
- Low alignment: Simplify recommendations, focus on achievable targets over optimization
```

**Problem:** System assumed low alignment always meant non-compliance/need for simplification

**Reality:** Low alignment could mean:
- ❌ **Injury/Medical Constraints** (like user's case - Achilles rehabilitation)
- Non-compliance pattern
- External constraints (time, access, equipment)
- Unclear guidance from coach
- Life circumstances

**User's Key Insight:** "The autopsy itself should dictate the strategy change, not a blanket assumption about compliance."

#### 3. **Journal Notes Not Included in Recommendation Prompt**
**Problem:**
- User notes contained explicit injury information: "rehabilitation of Achilles/ankle/plantar fasciitis issues"
- Notes only visible in autopsy analysis
- Autopsy analysis got truncated to 150 chars
- **Result:** Critical medical information never reached recommendation generation

#### 4. **ACWR Optimization Overrode Medical Safety**
**Problem:**
- Metrics showed "undertraining" (External ACWR: 0.74, Internal ACWR: 0.55 - both below optimal 0.8-1.3)
- System prioritized "restore training stimulus" over injury rehabilitation
- Decision logic: Low ACWR → Increase volume
- **Should have been:** Injury present → Conservative protocol regardless of ACWR

---

## Phase 4: Comprehensive Fixes Implemented

**User's Decision:** "Implement all four fixes"

### Fix 1: Increased Autopsy Insight Character Limits ✅
**File:** `app/llm_recommendations_module.py`
**Lines:** 1623-1625, 1823

**Changes:**
```python
# OLD:
key_insights.append(insights_section[:200])  # First 200 chars
# In prompt:
- Key Learning: {autopsy_insights['latest_insights'][:150] ...}  # Truncated to 150

# NEW:
# For low alignment scores (<4), capture more context for critical guidance
char_limit = 500 if autopsy.get('alignment_score', 10) < 4 else 300
key_insights.append(insights_section[:char_limit])
# In prompt:
- Key Learning: {autopsy_insights['latest_insights'] ...}  # No truncation
```

**Impact:**
- Low alignment (<4): 500 chars of autopsy guidance (3.3x increase)
- Normal alignment: 300 chars (1.5x increase)
- No second truncation in prompt

---

### Fix 2: Replaced "Low Alignment = Simplify" with Nuanced Logic ✅
**File:** `app/llm_recommendations_module.py`
**Lines:** 1825-1835, 1873-1883

#### First Section (Autopsy Context - line 1825-1835):

**OLD:**
```
COACHING ADAPTATION STRATEGY:
- If alignment >7: Build on successful patterns, athlete follows guidance well
- If alignment 4-7: Address recurring deviations, simplify recommendations
- If alignment <4: Major strategy change needed, focus on compliance over optimization
```

**NEW:**
```
AUTOPSY-INFORMED ADAPTATION (CRITICAL):
- The autopsy analysis above identifies the ROOT CAUSE of alignment mismatches
- If alignment <4: The autopsy contains SPECIFIC STRATEGY CHANGES needed - READ IT CAREFULLY
- Common root causes and correct coaching responses:
  * INJURY/PAIN mentioned in autopsy or notes → OVERRIDE ACWR logic, prescribe rehabilitation protocol
  * User notes indicate medical constraints → HONOR those constraints, do not push volume
  * Non-compliance pattern → Simplify guidance for better adherence
  * External constraints (time, access) → Adjust for athlete's reality
- DO NOT assume low alignment = simplification needed
- APPLY THE AUTOPSY'S SPECIFIC RECOMMENDATIONS, not generic defaults
- When injury/medical issues present: Current metrics (ACWR, divergence) are SECONDARY to safe recovery
```

#### Second Section (Instructions - line 1873-1883):

**OLD:**
```
ADAPTIVE COACHING LOGIC:
- High recent alignment: Reinforce successful approaches, maintain recommendation style
- Mixed alignment: Address specific recurring deviations, provide clearer guidance
- Low alignment: Simplify recommendations, focus on achievable targets over optimization
- Always respect the athlete's personalized risk tolerance thresholds listed above
```

**NEW:**
```
CRITICAL DECISION HIERARCHY (APPLY IN THIS ORDER):
1. INJURY/MEDICAL STATUS (from autopsy or notes) - HIGHEST PRIORITY
   - If injury/pain/rehabilitation mentioned → Conservative protocol overrides all other metrics
   - Ignore ACWR optimization when injury present
2. AUTOPSY-SPECIFIC GUIDANCE (from Key Learning above)
   - Apply the exact strategy changes recommended in autopsy analysis
   - Don't assume low alignment = simplify; read what autopsy actually says
3. CURRENT METRICS (ACWR, divergence, days since rest)
   - Only apply normal training progression if no injury/medical issues present
4. ATHLETE RISK TOLERANCE
   - Respect personalized thresholds, but medical safety always trumps risk tolerance
```

**Impact:** Established clear priority: Medical safety > Autopsy guidance > Metrics > Risk tolerance

---

### Fix 3: Added Journal Notes Fetching Function ✅
**File:** `app/llm_recommendations_module.py`
**Lines:** 1641-1681

**New Function:**
```python
def get_recent_journal_notes(user_id, days=3):
    """
    Get recent journal notes to provide context for recommendation generation.
    Notes may contain critical information about injury status, medical constraints,
    or reasons for deviating from prescriptions.
    """
    # Fetches notes from journal_entries table
    # Returns formatted string with date, energy, RPE, pain, and notes
```

**Returns Format:**
```
  2025-12-02: Energy 4/5, RPE 1/10, Pain 0%
  Notes: super easy treadmill effort aimed at rehabilitation of
         Achilles/ankle/plantar fasciitis issues.

  2025-12-01: Energy 3/5, RPE 2/10, Pain 20%
  Notes: Took it easy due to ankle soreness...
```

**Impact:** Direct access to user's injury/medical context from notes

---

### Fix 4: Added Journal Notes to Recommendation Prompt ✅
**File:** `app/llm_recommendations_module.py`
**Lines:** 1856-1866, 1919

**Added to Prompt:**
```python
# Get recent journal notes for additional context (may contain injury/medical info)
recent_notes = get_recent_journal_notes(user_id, days=3)
notes_context = ""
if recent_notes:
    notes_context = f"""
RECENT JOURNAL NOTES (Last 3 Days):
{recent_notes}

CRITICAL: If notes mention injury, pain, rehabilitation, medical issues, or reasons for
deviating from prescription, these override normal training progression logic.
"""

# Include in prompt (line 1919):
{weekly_program_context}

{notes_context}

{autopsy_context}
```

**Impact:** Notes with injury information now explicitly shown BEFORE autopsy context and training framework

---

## Key Design Decisions Made

### 1. Trust the Autopsy, Not Generic Rules
**Principle:** Autopsy analysis contains nuanced understanding of WHY alignment was low
- Don't make blanket assumptions (low alignment ≠ always simplify)
- Read and apply autopsy's specific recommendations
- Different root causes require different coaching responses

### 2. Medical Safety First, Metrics Second
**Principle:** Establish clear decision hierarchy
- **HIGHEST PRIORITY:** INJURY/MEDICAL STATUS (from autopsy or notes)
- **SECOND:** AUTOPSY-SPECIFIC GUIDANCE (read what it actually says)
- **THIRD:** CURRENT METRICS (ACWR, divergence) - only if no injury
- **FOURTH:** ATHLETE RISK TOLERANCE (but medical safety always trumps)

**Impact:** When injury present, ignore ACWR "undertraining" signals that would normally trigger volume increase

### 3. User Notes Are Critical Context
**Principle:** Notes may contain information not captured in structured data
- Include notes directly in recommendation prompt (not just in autopsy)
- Emphasize notes can override normal progression logic
- Notes are athlete's voice - honor what they're telling us

### 4. Character Limits Based on Severity
**Principle:** Adaptive approach based on situation criticality
- Low alignment (<4) = more context needed (500 chars) for critical guidance like injury protocols
- Normal alignment = standard context sufficient (300 chars)
- Don't truncate critical medical information to save tokens

---

## Expected Impact

### Before This Session:
❌ Full recommendation showing in daily column (~2500+ chars) - parsing bug
❌ Save button not appearing when Rest Day + observations - button logic bug
❌ Injury status ignored, aggressive training prescribed - autopsy learning bug
❌ User notes not considered in recommendations
❌ Low alignment assumed to mean non-compliance
❌ ACWR optimization overrode medical safety

### After This Session:
✅ Daily column shows only daily section (150-200 words)
✅ Save button appears when observations entered
✅ Injury status from autopsy + notes overrides ACWR optimization
✅ Rehabilitation protocol should be prescribed when injury present
✅ More nuanced autopsy-informed decision making
✅ Medical safety established as highest priority

---

## Testing Strategy

**User chose Option C:** Wait for next real recommendation generation to observe logs

### What to Monitor:

#### 1. Parser Format Detection
**Look for:**
```
✅ Found daily section (plain_text_headers): 850 chars
✅ Found weekly section: 620 chars
✅ Found insights section: 480 chars
```

**Should NOT see:**
```
⚠️ No structured sections found, using entire response as daily recommendation
```

#### 2. Character Counts in Database
**Query:**
```sql
SELECT
    target_date,
    LENGTH(daily_recommendation) as daily_chars,
    LENGTH(weekly_recommendation) as weekly_chars,
    LENGTH(pattern_insights) as insights_chars
FROM llm_recommendations
WHERE user_id = ? AND target_date = ?
ORDER BY id DESC LIMIT 1;
```

**Expected:**
- `daily_chars`: 800-1400 (not 2500+)
- `weekly_chars`: 600-1000
- `insights_chars`: 450-700

#### 3. Autopsy Insight Capture
**Look for:**
```
Fetching recent journal notes for user...
Found 2 recent notes with content
Autopsy insights: 500 chars captured (low alignment <4)
```

#### 4. Injury Protocol Application
**Recommendation should:**
- Reference injury status from notes
- Prescribe conservative rehabilitation training
- Mention "treadmill only" or similar injury-appropriate guidance
- **NOT** default to aggressive volume increase despite low ACWR

---

## Files Modified

### 1. `app/llm_recommendations_module.py`
**Changes:**
- Line 1688: Deleted duplicate `get_user_coaching_spectrum()` function
- Lines 1623-1625: Updated autopsy insight character limits (200 → 500/300 based on alignment)
- Lines 1825-1835: Replaced "COACHING ADAPTATION STRATEGY" with "AUTOPSY-INFORMED ADAPTATION"
- Lines 1873-1883: Replaced "ADAPTIVE COACHING LOGIC" with "CRITICAL DECISION HIERARCHY"
- Lines 1641-1681: Added `get_recent_journal_notes()` function (NEW)
- Lines 1856-1866: Added notes context fetching
- Line 1919: Added notes context to prompt
- Lines 1080-1115: Updated parser to handle multiple formats
- Lines 1871-1885: Updated prompt format instructions

### 2. `frontend/src/JournalPage.tsx`
**Changes:**
- Lines 889-918: Fixed button state logic priority (Save button check moved before Rest Day button)

---

## Architecture Improvements

### Before: Metrics-Driven Optimization
```
Current Metrics (ACWR, divergence)
  ↓
Pattern Analysis (red flags, warnings)
  ↓
Autopsy Learning (truncated to 150 chars)
  ↓
Generate Recommendation
```

### After: Safety-First Decision Hierarchy
```
1. INJURY/MEDICAL STATUS (from notes or autopsy) ← HIGHEST PRIORITY
   ↓
2. AUTOPSY-SPECIFIC GUIDANCE (500 chars if critical)
   ↓
3. CURRENT METRICS (ACWR, divergence) ← Only if no injury
   ↓
4. ATHLETE RISK TOLERANCE
   ↓
Generate Recommendation
```

---

## Code Quality Improvements

### 1. Eliminated Duplicate Code
- Removed inferior duplicate function
- Single source of truth for coaching spectrum retrieval

### 2. Added Comprehensive Logging
- Format detection for parser
- Character count tracking for autopsy insights
- Notes retrieval confirmation

### 3. Improved Error Handling
```python
try:
    recent_notes = get_recent_journal_notes(user_id, days=3)
except Exception as e:
    logger.error(f"Error getting recent journal notes: {str(e)}")
    return None
```

### 4. Self-Documenting Code
- Function docstrings explain purpose and critical use cases
- Comments explain "why" not just "what"
- Example: "For low alignment scores (<4), capture more context for critical guidance (injury, medical issues)"

---

## Lessons Learned

### 1. Don't Make Assumptions About Low Performance
- Low alignment ≠ always non-compliance
- Could be injury, medical constraints, life circumstances, unclear guidance
- Let the autopsy analysis (which has full context) determine root cause

### 2. Medical Safety Must Override All Metrics
- ACWR showing "undertraining" doesn't matter if athlete is injured
- Volume optimization algorithms are dangerous when injury present
- Establish clear priority hierarchy with safety at top

### 3. User Notes Are a Gold Mine
- Athletes often explicitly state critical information in notes
- "rehabilitation of Achilles issues" is clear medical context
- Don't bury notes in truncated autopsy text - surface them prominently

### 4. Character Limits Should Be Adaptive
- Critical situations (injury, low alignment) need more context
- Normal situations can use shorter summaries
- Token cost vs. safety trade-off favors safety

### 5. Test with Real User Data Early
- User's live example (2/10 alignment, injury ignored) revealed fundamental design flaw
- Code audit was valuable but real-world failure mode was more instructive
- Integration testing with actual user scenarios is essential

---

## Future Considerations

### Potential Enhancements:

1. **Injury Tracking Database Table**
   - Structured injury status tracking
   - Not just in notes (unstructured text)
   - Could have fields: injury_type, severity, start_date, status (active/recovering/resolved)

2. **Medical Constraint Flags**
   - Explicit "injury mode" toggle
   - Automatically modifies decision hierarchy
   - Prevents ACWR optimization when flag is set

3. **Autopsy Learning Trends**
   - Track if alignment improving/declining over time
   - Identify patterns: "athlete always ignores elevation gain recommendations"
   - More sophisticated learning than simple average

4. **User Feedback Loop**
   - "Was this recommendation helpful?" rating
   - Captures if autopsy-informed changes are working
   - Continuous improvement of learning system

5. **Multi-Injury Handling**
   - User may have multiple concurrent injuries (Achilles + knee)
   - Notes might mention multiple areas
   - Need prioritization logic for rehab protocols

---

## Deployment Checklist

- [x] Code changes completed and tested (module import)
- [x] Duplicate function removed and verified
- [x] Parser updated with multiple format support
- [x] Frontend button logic fixed
- [x] New function `get_recent_journal_notes()` added
- [x] Prompt updated with injury priority hierarchy
- [x] Character limits increased for critical cases
- [ ] Monitor logs after next recommendation generation
- [ ] Verify injury protocol is applied correctly
- [ ] Confirm daily column shows only daily section
- [ ] Check alignment score impact on char limits
- [ ] User validation of recommendation quality

---

## Session Metrics

- **Duration:** Full session (comprehensive audit + fixes)
- **Issues Fixed:** 7
  1. Duplicate function
  2. Button logic
  3. Parser format mismatch
  4. Autopsy truncation
  5. Bad low-alignment assumptions
  6. Missing journal notes
  7. Inverted decision hierarchy (metrics before safety)
- **Files Modified:** 2
- **Functions Added:** 1 (`get_recent_journal_notes`)
- **Functions Deleted:** 1 (duplicate `get_user_coaching_spectrum`)
- **Lines Changed:** ~150+
- **Architecture Improvements:** Established medical safety as highest priority with clear decision hierarchy

---

## References

**Key Files:**
- `app/llm_recommendations_module.py` - Core recommendation generation
- `app/coach_recommendations.py` - Weekly program generation
- `app/strava_app.py` - API endpoints
- `frontend/src/JournalPage.tsx` - Journal UI

**Related Documentation:**
- Training Reference Framework (loaded in prompts)
- ACWR Calculation Logic
- Autopsy Generation System
- Coaching Tone Spectrum

---

## Contact & Maintenance

**For questions about this implementation:**
- Review this document first
- Check logs for format detection and character counts
- Verify autopsy insights are being captured properly
- Test with low alignment scenarios (<4) to ensure injury protocols apply

**When modifying recommendation logic:**
- Maintain decision hierarchy: Safety > Autopsy > Metrics > Risk Tolerance
- Don't assume root causes - let autopsy analysis determine them
- Include user notes in prompt context
- Use adaptive character limits based on severity

---

**Document Version:** 1.0
**Last Updated:** December 2, 2025
**Status:** Deployed, awaiting real-world testing
