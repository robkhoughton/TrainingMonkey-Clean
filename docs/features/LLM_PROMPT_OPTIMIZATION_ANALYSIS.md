# LLM Prompt Optimization Analysis
**Date**: November 19, 2025  
**Status**: Analysis of old vs new prompt functions

## Executive Summary

We have **3 prompt functions** in the codebase:
1. ✅ **`create_enhanced_prompt_with_tone()`** - ACTIVE (comprehensive, weekly cron jobs)
2. ❌ **`create_enhanced_prompt()`** - DEPRECATED (never called, can be removed)
3. ✅ **`create_autopsy_informed_decision_prompt()`** - ACTIVE (journal workflow, just fixed)

---

## Function Status & Usage

### 1. `create_enhanced_prompt()` (Lines 246-366) ❌ DEPRECATED

**Status**: **NOT USED ANYWHERE** - Safe to delete

**Features**:
- ✅ Athlete profile classification
- ✅ Risk tolerance (conservative/moderate/aggressive)
- ✅ Personalized thresholds
- ✅ Pattern flags (red flags, positive patterns, warnings)
- ✅ Recent activities summary
- ✅ Training Reference Framework
- ✅ Three sections (DAILY, WEEKLY, PATTERN)
- ❌ NO coaching tone personalization
- ❌ NO autopsy insights integration

**Why it exists**: This was the original enhanced prompt before coaching tone and autopsy features were added.

**Action**: **DELETE** - All features have been superseded by `create_enhanced_prompt_with_tone()`

---

### 2. `create_enhanced_prompt_with_tone()` (Lines 777-935) ✅ ACTIVE

**Status**: **PRIMARY FUNCTION** - Called by `generate_recommendations()` (line 726)

**Used for**:
- Weekly cron jobs (Sunday/Wednesday)
- Manual "Generate Recommendations" button
- Any comprehensive recommendation generation

**Features**:
- ✅ Athlete profile classification
- ✅ Risk tolerance (conservative/moderate/aggressive)
- ✅ Personalized thresholds
- ✅ Pattern flags (red flags, positive patterns, warnings)
- ✅ Recent activities summary
- ✅ Training Reference Framework
- ✅ Three sections (DAILY, WEEKLY, PATTERN)
- ✅ **Coaching tone personalization** (supportive ↔ analytical spectrum)
- ✅ **Autopsy insights integration** (optional, if available)

**Prompt Quality**: ⭐⭐⭐⭐⭐ (5/5) - This is the GOLD STANDARD prompt

**Action**: **KEEP** - This is optimal and should remain as-is

---

### 3. `create_autopsy_informed_decision_prompt()` (Lines 1857-1922) ✅ ACTIVE

**Status**: **SPECIALIZED FUNCTION** - Called after journal entry completion

**Used for**:
- Journal workflow (user completes journal entry)
- Triggered by `update_recommendations_with_autopsy_learning()`
- Fast, focused recommendations based on recent learning

**Features** (BEFORE today's fix):
- ✅ Autopsy insights integration (primary focus)
- ✅ Adaptive coaching strategy based on alignment scores
- ✅ Current metrics
- ❌ NO athlete profile classification
- ❌ NO risk tolerance thresholds
- ❌ NO pattern flags analysis
- ❌ NO recent activities summary
- ❌ NO Training Reference Framework
- ❌ NO coaching tone personalization
- ❌ Only ONE section (DAILY) ← **JUST FIXED**

**Features** (AFTER today's fix):
- ✅ Three sections (DAILY, WEEKLY, PATTERN) ← **NOW FIXED**
- Still missing: profile, thresholds, pattern flags, coaching tone

**Prompt Quality**: ⭐⭐⭐ (3/5) - Functional but **missing critical context**

**Action**: **NEEDS OPTIMIZATION** - See recommendations below

---

## Problem: Autopsy-Informed Prompt is Missing Key Features

The `create_autopsy_informed_decision_prompt()` is **significantly less sophisticated** than `create_enhanced_prompt_with_tone()`:

### Missing Features (Critical):
1. ❌ **Athlete Profile Classification** (recreational vs competitive vs elite)
2. ❌ **Personalized Risk Tolerance** (conservative vs moderate vs aggressive)
3. ❌ **Pattern Flags Analysis** (red flags, positive patterns, warnings)
4. ❌ **Recent Activities Summary** (detailed activity context)
5. ❌ **Training Reference Framework** (the comprehensive training guide)
6. ❌ **Coaching Tone Personalization** (supportive ↔ analytical spectrum)

### Impact:
- Users get **less sophisticated recommendations** after journal entries
- Coaching style is **inconsistent** (tone-aware on weekly cron, generic after journal)
- Recommendations **lack context** (no pattern analysis, no red flags)
- **No Training Reference Framework** means Claude has less guidance

---

## Recommendations

### Option A: **Merge & Enhance** (Recommended) ⭐

**Goal**: Make autopsy-informed prompt as sophisticated as the comprehensive prompt

**Action**: Refactor `create_autopsy_informed_decision_prompt()` to include ALL features from `create_enhanced_prompt_with_tone()` PLUS autopsy learning

**Benefits**:
- ✅ Consistent coaching quality across all workflows
- ✅ Maintains autopsy learning focus
- ✅ Adds missing context (profile, thresholds, pattern flags)
- ✅ Applies coaching tone personalization
- ✅ Uses Training Reference Framework

**Estimated Effort**: 30-45 minutes

---

### Option B: **Use Same Prompt** (Alternative)

**Goal**: Replace autopsy-informed prompt with the comprehensive prompt

**Action**: Always use `create_enhanced_prompt_with_tone()`, which already supports autopsy insights

**Benefits**:
- ✅ Single prompt to maintain
- ✅ Guaranteed consistency
- ✅ Simpler codebase

**Drawbacks**:
- ⚠️ Loses specialized adaptive coaching logic for journal workflow
- ⚠️ Longer prompt = more expensive API calls

**Estimated Effort**: 15 minutes

---

## Code Cleanup Recommendations

### Delete (Safe):
1. ✅ `create_enhanced_prompt()` (lines 246-366)
   - **Reason**: Never called, fully superseded by `_with_tone` version
   - **Savings**: ~120 lines of dead code

### Keep (Active):
1. ✅ `create_enhanced_prompt_with_tone()` - Primary comprehensive prompt
2. ✅ `create_autopsy_informed_decision_prompt()` - Journal workflow (but optimize it)

### Optimize:
1. 🔧 `create_autopsy_informed_decision_prompt()` - Add missing features from comprehensive prompt

---

## Next Steps

1. **Immediate**: Delete `create_enhanced_prompt()` to clean up dead code
2. **Short-term**: Enhance `create_autopsy_informed_decision_prompt()` with missing features
3. **Long-term**: Consider creating a unified prompt builder that composes features dynamically

---

## Summary

| Function | Status | Quality | Action |
|----------|--------|---------|--------|
| `create_enhanced_prompt()` | ❌ Unused | N/A | **DELETE** |
| `create_enhanced_prompt_with_tone()` | ✅ Active | ⭐⭐⭐⭐⭐ | **KEEP** |
| `create_autopsy_informed_decision_prompt()` | ✅ Active | ⭐⭐⭐ | **OPTIMIZE** |

**Bottom Line**: We have a GREAT comprehensive prompt, but the autopsy-informed prompt is **missing critical features** that make your recommendations sophisticated. We should merge the best of both.

