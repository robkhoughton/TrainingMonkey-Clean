# Conversation Summary: ACWR/Divergence Fix + Troubleshooting Protocol Creation

**Date**: 2025-12-12
**Session Focus**: (1) Eliminate duplicate calculations causing inconsistent ACWR/divergence values, (2) Create systematic troubleshooting protocol to prevent patch-based solutions

---

## Main Objectives

1. **Technical**: Fix discrepancy where External/Internal ACWR showed different values in chart (0.55/0.20) vs. card (1.77/0.75)
2. **Process**: Address pattern of proposing patches instead of root cause fixes, create enforceable troubleshooting methodology

## Key Discussions

- **Root Cause Analysis**: Two separate API endpoints calculated metrics differently
  - `/api/training-data` recalculated with custom config → used by charts
  - `/api/stats` used raw DB values (no recalculation) → used by card
- **Architecture Flaw**: Multiple calculation functions with different logic created inconsistencies
- **Single Source of Truth**: User correctly identified need to consolidate to one calculation point

## Code Changes

**Frontend:**
- `frontend/src/TrainingLoadDashboard.tsx`
  - Removed `/api/stats` fetch call (lines 584-603)
  - Now calculates metrics from latest entry in `/api/training-data` response
  - Removed `calculateNormalizedDivergence` function (duplicate logic)
  - Fixed divergence to always use backend value, never recalculate (line 546)

**Backend:**
- `app/strava_app.py`
  - **DELETED** `/api/stats` endpoint entirely (lines 1870-1966, ~96 lines)
  - Fixed `recalculate_acwr_with_config` to use canonical `UnifiedMetricsService._calculate_normalized_divergence` (lines 7767-7774)

**Cleanup:**
- Deleted `app/templates/dashboard.html` (legacy template, unused)

## Issues Identified

1. **Duplicate Calculations**: 3 different divergence calculation functions with inconsistent logic:
   - `UnifiedMetricsService._calculate_normalized_divergence` (canonical)
   - `recalculate_acwr_with_config` (custom logic)
   - Frontend `calculateNormalizedDivergence`

2. **Redundant API Endpoints**: `/api/stats` provided same data as `/api/training-data` but without custom config recalculation

3. **Inconsistent Data Flow**: Card used different data source than charts

## Solutions Implemented

### 1. Single Source of Truth for Divergence
- `UnifiedMetricsService._calculate_normalized_divergence` is now the ONLY calculation
- `recalculate_acwr_with_config` calls this canonical function instead of duplicating logic
- Frontend never recalculates, only displays backend values

### 2. Unified Data Source
- Eliminated `/api/stats` endpoint
- Frontend derives all metrics from `/api/training-data` latest entry
- Both card and charts now use identical data source

### 3. Simplified Architecture
```
Before:
/api/training-data → Charts (recalculated)
/api/stats → Card (raw DB values) ❌ Inconsistent!

After:
/api/training-data → Charts AND Card ✓ Consistent!
```

## Decisions Made

1. **Frontend over Backend for metric extraction**: Since `/api/training-data` already has all needed data, frontend extracts latest values instead of making separate API call
2. **Delete vs. Deprecate**: Deleted `/api/stats` entirely (not used elsewhere per grep search)
3. **Zero Tolerance for Frontend Recalculation**: Frontend NEVER recalculates metrics, only displays backend values

## Meta-Discussion: Problem-Solving Methodology

### Issue Identified
Assistant initially proposed **patches** (sync endpoints, add recalculation logic) rather than addressing **root causes** (eliminate duplicate endpoints), despite explicit guidance in `.claude/CLAUDE.md`:
> "Address Root Causes, Not Symptoms - Avoid workarounds, try-catch blocks that hide errors, or conditional logic that masks issues"

### Root Cause Analysis of the Analysis Problem
User identified pattern: Assistant was focused on **transparency** (showing reasoning) rather than **process** (following systematic methodology)

**Key insight**: "Should the word 'troubleshoot' trigger a specific process?"

### Solution: Structured Troubleshooting Protocol
Created `.claude/commands/troubleshoot.md` - enforced 4-phase methodology:

**Phase 1: Context Gathering (Mandatory)**
- Read project guidelines (`.claude/CLAUDE.md`, `.cursorrules`)
- Define symptom precisely
- Map all instances of the issue
- Output required before proceeding

**Phase 2: Root Cause Investigation (No Solutions)**
- Apply "5 Whys" technique with documented evidence
- Anti-pattern detection checklist (duplicate calculations, multiple sources of truth, etc.)
- Determine ground truth and what should be eliminated
- Output required before proceeding

**Phase 3: Solution Design (USER DECISION GATE)**
- State root cause clearly
- Analyze impact (files to change, code to delete, risks)
- Propose 2-3 architectural solutions
- **STOP - Wait for user approval before implementing**

**Phase 4: Implementation (Only After Approval)**
- Implement approved solution
- Remove duplicates
- Verify consistency
- Document changes

### Red Flags (Abort and Reassess)
Command includes explicit anti-patterns that indicate root cause not found:
- ❌ Copying code from one location to another
- ❌ Adding conditional logic to "synchronize" values
- ❌ Creating a second calculation of the same value
- ❌ Implementing workarounds instead of fixing root cause

### Process Over Promises
Key realization: Need **systematic enforcement**, not just "trying harder" or "being more transparent"
- Command creates mandatory checkpoints
- Can't skip to solutions without completing investigation phases
- User approval required before implementation
- Success criteria: Elimination not addition, consolidation not synchronization

## Next Steps

**Required:**
1. Rebuild frontend: `cd frontend && npm run build`
2. Deploy: `scripts\build_and_copy.bat`
3. Verify ACWR and divergence values match between card and chart

**Recommended:**
- Monitor for any issues from `/api/stats` deletion
- Test `/troubleshoot` command on next bug/inconsistency to validate methodology
- Consider adding automated tests to prevent calculation divergence in future

## Technical Details

### Key Code Changes

**Divergence Calculation (strava_app.py:7767-7774):**
```python
# OLD: Custom logic in recalculate_acwr_with_config
if new_external_acwr > 0 and new_internal_acwr > 0:
    avg_acwr = (new_external_acwr + new_internal_acwr) / 2
    new_normalized_divergence = (new_external_acwr - new_internal_acwr) / avg_acwr

# NEW: Use canonical function
from unified_metrics_service import UnifiedMetricsService
new_normalized_divergence = UnifiedMetricsService._calculate_normalized_divergence(
    new_external_acwr, new_internal_acwr
)
```

**Frontend Metric Extraction (TrainingLoadDashboard.tsx:584-628):**
```typescript
// Calculate metrics from latest entry in processedData
if (processedData.length > 0) {
    const latestEntry = processedData[processedData.length - 1];

    setMetrics({
        externalAcwr: coerceNumber(latestEntry.acute_chronic_ratio, 0),
        internalAcwr: coerceNumber(latestEntry.trimp_acute_chronic_ratio, 0),
        normalizedDivergence: coerceNumber(latestEntry.normalized_divergence, 0),
        // ... other metrics
    });
}
```

**Days Since Rest Calculation:**
Frontend now calculates from data instead of API:
```typescript
let daysSinceRest = 0;
for (let i = processedData.length - 1; i >= 0; i--) {
    if (processedData[i].activity_id === 0 || processedData[i].type === 'rest') {
        daysSinceRest = processedData.length - 1 - i;
        break;
    }
}
```

### Files Modified
- `frontend/src/TrainingLoadDashboard.tsx`
- `app/strava_app.py`

### Files Created
- `.claude/commands/troubleshoot.md` (structured troubleshooting protocol)

### Files Deleted
- `app/templates/dashboard.html`

### Root Cause Summary
User had custom dashboard config (chronic period ≠ 28 days or decay rate ≠ 0). The `/api/training-data` endpoint correctly recalculated ACWR with this config, but `/api/stats` used raw database values calculated with default settings, causing the discrepancy.
