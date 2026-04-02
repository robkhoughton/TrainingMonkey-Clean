---
paths: ["frontend/src/**/*.tsx", "frontend/src/**/*.ts"]
---

# Frontend Standards (React/TypeScript)

## Performance Monitoring

This project uses a **two-hook system** for performance tracking.

### Hook Types

| Hook | Returns | Purpose |
|------|---------|---------|
| `usePagePerformanceMonitoring()` | `void` | Auto-tracks Core Web Vitals (TTFB, FCP, LCP) |
| `useComponentPerformanceMonitoring()` | `{ trackFetchStart, trackFetchEnd, reportMetrics }` | Manual tracking for data fetches |

### Data-Driven Pages (Dashboard, Activities, Journal, Coach)

Use BOTH hooks:

```typescript
import { usePagePerformanceMonitoring, useComponentPerformanceMonitoring } from './usePerformanceMonitoring';

const DataPage: React.FC = () => {
  // Page-level: auto Web Vitals (no return value!)
  usePagePerformanceMonitoring('data-page');

  // Component-level: returns tracking methods
  const perfMonitor = useComponentPerformanceMonitoring('DataPageComponent');

  useEffect(() => {
    const fetchData = async () => {
      perfMonitor.trackFetchStart();
      const data = await fetch('/api/data');
      perfMonitor.trackFetchEnd();
      perfMonitor.reportMetrics(data.length);
    };
    fetchData();
  }, [perfMonitor]);  // Include perfMonitor in deps!

  return <div>...</div>;
};
```

### Simple Pages (Settings, static content)

Page hook only:

```typescript
import { usePagePerformanceMonitoring } from './usePerformanceMonitoring';

const SimplePage: React.FC = () => {
  usePagePerformanceMonitoring('simple-page');
  return <div>Static content</div>;
};
```

### Common Mistakes

```typescript
// WRONG: usePagePerformanceMonitoring returns void, not an object!
const perfMonitor = usePagePerformanceMonitoring('page');
perfMonitor.reportMetrics();  // ERROR: Cannot read properties of undefined

// WRONG: Missing perfMonitor in dependency array (stale closure)
useEffect(() => {
  perfMonitor.trackFetchStart();
}, []);  // Missing perfMonitor!

// WRONG: Using only page hook when you need component metrics
usePagePerformanceMonitoring('page');
// Can't call reportMetrics() - need useComponentPerformanceMonitoring
```

## Timezone & Date Display

ISO date-only strings (`'YYYY-MM-DD'`) are parsed as **UTC midnight** by JavaScript. In Pacific
time (UTC-7), this rolls back to the previous evening — displaying one day earlier than intended.

**Always append `T12:00:00` when parsing a date-only string for display:**

```typescript
// CORRECT — anchors to local noon, no UTC→local day shift
const displayDate = new Date(dateString + 'T12:00:00').toLocaleDateString('en-US', {
  weekday: 'long', month: 'short', day: 'numeric'
});

// WRONG — UTC midnight shifts to previous day in Pacific time
const displayDate = new Date(dateString).toLocaleDateString();
```

This applies everywhere a `YYYY-MM-DD` string is passed to `new Date()` for display:
`toLocaleDateString`, `toLocaleDateString` with options, weekday derivation, etc.

**Week structure:** The training week runs **Sunday–Saturday**. Plans are generated Sunday
morning (after the 2am Strava sync captures Saturday's activity). `week_start_date` is always
a Sunday.

## API Communication

```typescript
// Standard fetch pattern
const response = await fetch('/api/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ date: '2025-01-15' })  // YYYY-MM-DD format
});

// Error handling
if (!response.ok) {
  throw new Error(`API error: ${response.status}`);
}
const data = await response.json();
```

## Component Patterns

- Use functional components with hooks
- Include `perfMonitor` in useCallback/useEffect dependency arrays
- Handle loading and error states explicitly
- Use TypeScript interfaces for props and API responses
