# ESLint Cleanup and Dead Code Removal - December 2025

## Overview

This document summarizes the work completed to resolve Docker build ESLint warnings and remove dead code from the TrainingMonkey codebase.

**Date:** December 7, 2025
**Initial Warnings:** 17+
**Final Warnings:** 0
**Build Status:** Compiled successfully

---

## Original Issues

The Docker build was producing the following ESLint warnings:

```
src\ActivitiesPage.tsx - Line 105: Missing dependency 'perfMonitor'
src\CoachPage.tsx - Lines 186, 194, 263: Unused interfaces
src\CoachPage.tsx - Line 793: Anchor missing href attribute
src\JournalPage.tsx - Line 244: Missing dependency 'perfMonitor'
src\RaceGoalsManager.tsx - Line 177: Unused 'getPriorityLabel'
src\TimelineVisualization.tsx - Lines 66, 88: Unused variables
src\TrainingLoadDashboard.tsx - Lines 100, 108, 150, 151, 154, 169, 617: Multiple unused variables/functions
src\WeeklyProgramDisplay.tsx - Lines 19, 350: Unused interface and variable
```

---

## Root Cause Analysis

### 1. perfMonitor Hook Instability
**Problem:** `useComponentPerformanceMonitoring` hook returned a new object on every render, causing ESLint to flag missing dependencies.

**Root Cause:** The hook's return value wasn't memoized.

**Fix:** Added `useCallback` for each function and `useMemo` for the return object in `usePerformanceMonitoring.ts`.

### 2. Dead Code in TrainingLoadDashboard
**Problem:** Multiple unused functions and state variables related to LLM recommendations.

**Root Cause:** An incomplete feature was started but never finished. The Dashboard was fetching recommendation data from `/api/llm-recommendations` but never displaying it. The Journal page gets the same data via `/api/journal` endpoint which bundles `todays_decision` into each entry.

**Architecture discovered:**
```
llm_recommendations_module.py → llm_recommendations table
                                        ↓
                    ┌───────────────────┴───────────────────┐
                    ↓                                       ↓
            /api/journal                         /api/llm-recommendations
            (used by JournalPage ✅)             (dead endpoint ❌)
```

### 3. CoachPage Interfaces
**Problem:** `RaceHistory`, `TrainingSchedule`, `RaceAnalysis` interfaces defined but unused.

**Root Cause:** These are input parameter definitions for training plan generation - intentionally kept for documentation/future use.

**Fix:** Added ESLint disable comments since they're intentionally retained.

### 4. Accessibility Issue
**Problem:** Anchor tag used for tab navigation without valid href.

**Fix:** Converted from `<a href="#">` to `<button type="button">` with equivalent styling.

---

## Changes Made

### Frontend Changes

#### `usePerformanceMonitoring.ts`
- Added `useCallback` and `useMemo` imports
- Wrapped `trackFetchStart`, `trackFetchEnd`, `reportMetrics` in `useCallback`
- Wrapped return object in `useMemo`

#### `ActivitiesPage.tsx`
- Added `perfMonitor` to useCallback dependency array (now stable)

#### `JournalPage.tsx`
- Added `perfMonitor` to useCallback dependency array (now stable)

#### `CoachPage.tsx`
- Added ESLint disable comments for intentionally kept interfaces
- Converted tab navigation from `<a>` to `<button>` for accessibility

#### `RaceGoalsManager.tsx`
- Removed unused `getPriorityLabel` function

#### `TimelineVisualization.tsx`
- Removed unused `formatDateShort` function
- Removed unused `currentWeekIndex` variable

#### `WeeklyProgramDisplay.tsx`
- Wired up `AutopsyData` interface to type API response (was defined but unused)
- Removed unused `isFuture` variable

#### `TrainingLoadDashboard.tsx`
- **Removed:** `LLMRecommendation` interface
- **Removed:** `formatNumber`, `formatScaledNumber` helper functions
- **Removed:** `recommendation`, `isLoadingRecommendation`, `journalStatus` state variables
- **Removed:** `getRecommendationDateContext` function
- **Commented out:** `fetchRecommendations`, `fetchJournalStatus`, `generateNewRecommendation` functions
- **Commented out:** useEffect calls to these functions

### Backend Changes

#### `strava_app.py`
- **Commented out:** `/api/llm-recommendations` GET endpoint
- **Commented out:** `/api/llm-recommendations/generate` POST endpoint
- **Commented out:** `/api/journal-status` GET endpoint

---

## Post-Deployment Testing

After deployment, verify:

1. **Journal Page**
   - Loads without errors
   - Displays `todays_decision` (Training Decision) for each day
   - Autopsy-Informed badge displays correctly
   - Navigation between dates works

2. **Dashboard Page**
   - Loads without errors
   - Charts display correctly
   - No console errors about failed API calls

3. **If both work:** Delete the commented-out code:
   - `TrainingLoadDashboard.tsx`: Remove the commented function block
   - `strava_app.py`: Remove the commented endpoint block

---

## Files Modified

```
frontend/src/usePerformanceMonitoring.ts
frontend/src/ActivitiesPage.tsx
frontend/src/JournalPage.tsx
frontend/src/CoachPage.tsx
frontend/src/RaceGoalsManager.tsx
frontend/src/TimelineVisualization.tsx
frontend/src/WeeklyProgramDisplay.tsx
frontend/src/TrainingLoadDashboard.tsx
app/strava_app.py
```

---

## Notes

- The `llm_recommendations` database table and `llm_recommendations_module.py` are **NOT dead code** - they're used by `/api/journal` to provide recommendation data
- The commented-out endpoints may be useful for admin/debugging purposes in the future
- The CoachPage interfaces (`RaceHistory`, `TrainingSchedule`, `RaceAnalysis`) are kept intentionally as they define the data structure for training plan inputs
