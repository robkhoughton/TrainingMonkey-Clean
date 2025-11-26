# Performance Monitor Pattern - Historical Context & Fix

## Issue Discovered
**Console Error**: `Uncaught (in promise) TypeError: Cannot read properties of undefined (reading 'reportMetrics')`

**Location**: `CoachPage.tsx` (newly created component)

---

## Root Cause Analysis

### The Incorrect Pattern (CoachPage - Initial Implementation)
```typescript
const CoachPage: React.FC = () => {
  // ❌ WRONG - usePagePerformanceMonitoring doesn't return anything
  const perfMonitor = usePagePerformanceMonitoring('coach');
  
  // Later in code...
  perfMonitor.reportMetrics(loadTime);  // ❌ ERROR: perfMonitor is undefined
}
```

### Why This Failed
From `usePerformanceMonitoring.ts` (line 79):
```typescript
export const usePagePerformanceMonitoring = (pageName: string) => {
  // ... implementation ...
  // ⚠️ NO RETURN VALUE - this hook manages its own lifecycle
};
```

The hook **does not return an object**. It automatically captures and reports page-level metrics (TTFB, FCP, LCP) without requiring manual calls.

---

## Established Pattern (From Prior Implementation)

### Performance Monitoring Architecture
Implemented in **October 2025** (commit `394c104`), documented in `PERFORMANCE_MONITORING_IMPLEMENTATION.md`:

**Two Hook Types:**

1. **`usePagePerformanceMonitoring(pageName)`** - Page-level metrics
   - Tracks Core Web Vitals (TTFB, FCP, LCP)
   - Automatically captures navigation timing
   - **Returns**: Nothing (void)
   - **Usage**: Call once, no manual reporting needed

2. **`useComponentPerformanceMonitoring(componentName)`** - Component-level metrics
   - Tracks fetch/process/render breakdown
   - **Returns**: Object with `{ trackFetchStart, trackFetchEnd, reportMetrics }`
   - **Usage**: Call methods to track component lifecycle

---

## Correct Patterns (From Existing Pages)

### Pattern 1: Page + Component Monitoring (Dashboard, Activities, Journal)

**Example from `TrainingLoadDashboard.tsx`** (line 127-129):
```typescript
const TrainingLoadDashboard: React.FC<TrainingLoadDashboardProps> = ({ onNavigateToTab }) => {
  // ✅ CORRECT - Page-level metrics (no return value)
  usePagePerformanceMonitoring('dashboard');
  
  // ✅ CORRECT - Component-level metrics (returns perfMonitor object)
  const perfMonitor = useComponentPerformanceMonitoring('TrainingLoadDashboard');
  
  // Later...
  perfMonitor.reportMetrics(data.length);  // ✅ Works!
}
```

**Example from `ActivitiesPage.tsx`** (line 34-36):
```typescript
const ActivitiesPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('activities');
  const perfMonitor = useComponentPerformanceMonitoring('ActivitiesPage');
  // ... component uses perfMonitor.reportMetrics()
}
```

**Example from `JournalPage.tsx`** (line 41-43):
```typescript
const JournalPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('journal');
  const perfMonitor = useComponentPerformanceMonitoring('JournalPage');
  // ... component uses perfMonitor.reportMetrics()
}
```

### Pattern 2: Page-Only Monitoring (Settings)

**Example from `SettingsPage.tsx`** (line 5-6):
```typescript
export const SettingsPage: React.FC = () => {
  // Performance monitoring
  usePagePerformanceMonitoring('settings');
  // ✅ No perfMonitor needed - page just redirects
}
```

**When to Use**: Simple pages without data fetching or complex rendering that don't need component-level tracking.

---

## Prior Related Fixes

### November 2025 (commit `ebf2c45`) - "Fix frontend warnings"

**Issue**: React Hook dependency warnings for `perfMonitor`

**Fixes Applied**:
1. **ActivitiesPage.tsx**: Added `perfMonitor` to `useCallback` deps
   ```typescript
   // Before
   }, [days]);  // ❌ Missing perfMonitor dependency
   
   // After
   }, [days, perfMonitor]);  // ✅ Complete dependencies
   ```

2. **JournalPage.tsx**: Added `perfMonitor` to `useCallback` deps
   ```typescript
   // Before
   }, []);  // ❌ Missing perfMonitor dependency
   
   // After
   }, [perfMonitor]);  // ✅ Complete dependencies
   ```

**Why This Matters**: The `perfMonitor` object is used inside callbacks, so React's exhaustive-deps rule requires it in the dependency array to prevent stale closures.

---

## Current Fix Applied (November 2025 - CoachPage)

### The Fix
```typescript
// ❌ BEFORE (Incorrect)
const CoachPage: React.FC = () => {
  const perfMonitor = usePagePerformanceMonitoring('coach');  // Returns undefined!
  // ...
}

// ✅ AFTER (Correct)
const CoachPage: React.FC = () => {
  // Page-level metrics
  usePagePerformanceMonitoring('coach');
  
  // Component-level metrics (returns perfMonitor object)
  const perfMonitor = useComponentPerformanceMonitoring('CoachPage');
  // ...
}
```

### Files Changed
- `frontend/src/CoachPage.tsx`:
  - Updated import: Added `useComponentPerformanceMonitoring`
  - Updated hook calls: Use both hooks correctly
  - Result: `perfMonitor.reportMetrics()` now works

### Commit
```
b7d34ab fix(coach): correct performance monitoring hook usage
```

---

## Pattern Summary & Best Practices

### ✅ Correct Pattern for Data-Driven Pages

```typescript
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

const MyPage: React.FC = () => {
  // 1. Page-level metrics (automatic, no return value)
  usePagePerformanceMonitoring('my-page-name');
  
  // 2. Component-level metrics (returns object)
  const perfMonitor = useComponentPerformanceMonitoring('MyPageComponent');
  
  useEffect(() => {
    const fetchData = async () => {
      const startTime = performance.now();
      
      // Optional: Track fetch phase
      perfMonitor.trackFetchStart();
      const data = await fetch('/api/data');
      perfMonitor.trackFetchEnd();
      
      // Report metrics
      const loadTime = performance.now() - startTime;
      perfMonitor.reportMetrics(data.length);
    };
    
    fetchData();
  }, [perfMonitor]);  // Include perfMonitor in deps!
  
  // ... rest of component
};
```

### ✅ Correct Pattern for Simple Pages

```typescript
import { usePagePerformanceMonitoring } from './usePerformanceMonitoring';

const SimplePage: React.FC = () => {
  // Page-level metrics only
  usePagePerformanceMonitoring('simple-page');
  
  // No perfMonitor needed - just renders content
  return <div>Content</div>;
};
```

### ❌ Common Mistakes to Avoid

1. **Trying to use return value of usePagePerformanceMonitoring**
   ```typescript
   // ❌ WRONG
   const perfMonitor = usePagePerformanceMonitoring('page');
   perfMonitor.reportMetrics();  // ERROR: undefined
   ```

2. **Forgetting perfMonitor in dependencies**
   ```typescript
   // ❌ WRONG
   useEffect(() => {
     perfMonitor.reportMetrics(data.length);
   }, [data]);  // Missing perfMonitor!
   
   // ✅ CORRECT
   useEffect(() => {
     perfMonitor.reportMetrics(data.length);
   }, [data, perfMonitor]);
   ```

3. **Using only page hook when component metrics needed**
   ```typescript
   // ❌ INCOMPLETE
   usePagePerformanceMonitoring('page');
   // Can't call reportMetrics() later
   
   // ✅ COMPLETE
   usePagePerformanceMonitoring('page');
   const perfMonitor = useComponentPerformanceMonitoring('Component');
   ```

---

## Testing Verification

### Before Fix
```
Console Error:
Uncaught (in promise) TypeError: Cannot read properties of undefined (reading 'reportMetrics')
    at CoachPage.tsx:190
```

### After Fix
```
✅ No console errors
✅ Performance metrics logged:
   📊 Page Performance Metrics: { page: 'coach', ttfb: '245ms', ... }
   📈 Component Performance (CoachPage): { fetch: '325ms', total: '493ms', ... }
```

---

## Related Documentation

1. **`PERFORMANCE_MONITORING_IMPLEMENTATION.md`** - Complete RUM system documentation
2. **`FRONTEND_CLEANUP_SUMMARY.md`** - Previous perfMonitor dependency fixes
3. **`frontend/src/usePerformanceMonitoring.ts`** - Hook implementation

---

## Lessons Learned

1. **New components must follow established patterns**: When creating `CoachPage`, should have referenced existing pages (`Dashboard`, `Activities`, `Journal`) for correct hook usage

2. **Hook return types matter**: 
   - `usePagePerformanceMonitoring()` → void (no return)
   - `useComponentPerformanceMonitoring()` → object with methods

3. **Both hooks serve different purposes**:
   - Page hook: Automatic Core Web Vitals tracking
   - Component hook: Manual component lifecycle tracking

4. **Dependency arrays are critical**: When using `perfMonitor` in callbacks/effects, include it in dependencies

5. **Pattern documentation prevents errors**: Clear examples in existing code serve as templates for new features

---

## Status

✅ **Fixed and Deployed**
- Error resolved in `CoachPage.tsx`
- Pattern now consistent across all pages
- No console errors
- Performance monitoring working correctly

**Future Action**: When creating new pages that fetch data, copy the pattern from `Dashboard`, `Activities`, or `Journal` pages.

