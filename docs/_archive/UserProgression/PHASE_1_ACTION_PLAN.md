# Phase 1 Implementation: Move Users to Features

**Goal:** Guide users from Dashboard to Journal to see their daily recommendation
**Strategy:** Don't move features TO the dashboard - move USERS to the features
**Timeline:** Week 1
**Priority:** HIGH - Foundation for entire progression system

---

## CORE PRINCIPLE

The daily recommendation already exists on the **Journal page**. The challenge is getting users there. We use an incremental reveal process to build confidence:

```
Dashboard (see metrics) → Journal (get recommendation) → Log workout → Autopsy → Coach
```

**Key Insight:** Users need to understand what they're seeing on the Dashboard BEFORE they'll trust the recommendation. The pop-up explains the Dashboard metrics and motivates the journey to Journal.

---

## PHASE 1 APPROACH: OPTION D (COMBINATION)

### Three Components Working Together:

1. **Daily Status Pop-up** - Explains Dashboard metrics, points to Journal
2. **Teaser Card** - Persistent card at top of Dashboard (replaces bottom "Get My Coach")
3. **Journal Tab Badge** - Visual indicator when recommendation is waiting

---

## COMPONENT 1: DAILY STATUS POP-UP

### Purpose
Explain what the user is seeing on the Dashboard and point them to Journal for their personalized recommendation.

### Design

```
┌─────────────────────────────────────────────────────────────────┐
│                                                            ✕    │
│  YOUR TRAINING STATUS                                           │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │  ACWR: 1.32     │  │  Divergence:    │                       │
│  │  ████████░░     │  │    -0.08        │                       │
│  │  ELEVATED       │  │  FATIGUED       │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
│  INJURY RISK: MODERATE-HIGH                                     │
│                                                                  │
│  Your training load is elevated and your body is showing        │
│  signs of accumulated fatigue. Your heart rate has been         │
│  running higher than expected for your effort levels.           │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  TODAY'S RECOMMENDATION:                                         │
│  Rest day or very easy recovery (Zone 1 only, < 30 min)         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │        See Full Analysis & Log Your Workout →           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│                        [Remind Me Later]                         │
└─────────────────────────────────────────────────────────────────┘
```

### Content Breakdown

**Section 1: Current Metrics (from Dashboard data)**
- ACWR value with visual gauge and status label
- Divergence value with status label
- These are the same metrics shown on Dashboard - the pop-up EXPLAINS them

**Section 2: Risk Interpretation**
- Synthesizes ACWR + Divergence into plain English
- Explains what the numbers MEAN for the user
- Examples:
  - "Your training load is elevated and your body is showing signs of accumulated fatigue."
  - "Your heart rate has been running higher than expected for your effort levels."
  - "You're in the optimal training zone with good recovery indicators."

**Section 3: Brief Recommendation (Teaser)**
- One-line recommendation (not the full analysis)
- Just enough to create curiosity
- Examples:
  - "Rest day or very easy recovery (Zone 1 only, < 30 min)"
  - "You're primed for a quality workout today"
  - "Light training recommended - monitor how you feel"

**Section 4: Call to Action**
- Primary: "See Full Analysis & Log Your Workout →" (navigates to Journal)
- Secondary: "Remind Me Later" (dismisses, shows badge on Journal tab)

### Status Interpretation Logic

**ACWR Status:**
| ACWR Range | Status Label | Color |
|------------|--------------|-------|
| < 0.8 | UNDERTRAINED | Blue |
| 0.8 - 1.1 | OPTIMAL | Green |
| 1.1 - 1.3 | BUILDING | Yellow |
| 1.3 - 1.5 | ELEVATED | Orange |
| > 1.5 | HIGH RISK | Red |

**Divergence Status:**
| Divergence Range | Status Label | Meaning |
|------------------|--------------|---------|
| > 0.05 | FRESH | Body adapting well |
| -0.05 to 0.05 | NEUTRAL | Normal state |
| -0.15 to -0.05 | FATIGUED | Accumulated stress |
| < -0.15 | OVERREACHING | High strain |

**Combined Risk Assessment:**
| ACWR | Divergence | Risk Level | Interpretation |
|------|------------|------------|----------------|
| High (>1.3) | Negative (<-0.05) | HIGH | Training load elevated + body fatigued |
| High (>1.3) | Neutral/Positive | MODERATE | Training load elevated but adapting |
| Optimal | Negative | MODERATE | Good load but accumulated fatigue |
| Optimal | Positive | LOW | Sweet spot - training effectively |
| Low (<0.8) | Any | LOW | Undertrained - room to build |

**Brief Recommendation Logic:**
| Risk Level | Days Since Rest | Recommendation |
|------------|-----------------|----------------|
| HIGH | Any | Rest day strongly recommended |
| MODERATE | > 5 | Easy recovery or rest |
| MODERATE | <= 5 | Light training, monitor fatigue |
| LOW (optimal) | Any | Primed for quality session |
| LOW (undertrained) | Any | Time to build - increase volume |

### When to Show Pop-up

1. **First dashboard visit of the day** (after data loads)
2. **Only if user hasn't visited Journal today**
3. **After data sync completes** (fresh metrics available)

### Dismiss Behavior

- **"See Full Analysis →"** → Navigate to Journal page
- **"Remind Me Later"** → Dismiss pop-up, show badge on Journal tab
- **"✕" close** → Same as "Remind Me Later"
- **Don't show again today** after any dismiss action

### Session Tracking

```typescript
// Check if should show pop-up
const shouldShowPopup = () => {
  const today = new Date().toDateString();
  const lastShown = localStorage.getItem('statusPopup_lastShown');
  const visitedJournalToday = localStorage.getItem('journal_visited_' + today);

  return lastShown !== today && !visitedJournalToday;
};

// Mark as shown
const markPopupShown = () => {
  localStorage.setItem('statusPopup_lastShown', new Date().toDateString());
};
```

---

## COMPONENT 2: TEASER CARD (TOP OF DASHBOARD)

### Purpose
Persistent reminder that points to Journal. Replaces the current "Get My Coach" banner at the bottom.

### Design

```
┌─────────────────────────────────────────────────────────────────┐
│  Your daily training recommendation is ready                     │
│  ACWR: 1.32 (Elevated) • Divergence: -0.08 (Fatigued)           │
│                                          [View on Journal →]    │
└─────────────────────────────────────────────────────────────────┘
```

### Characteristics
- Compact (single line or two lines max)
- Shows current metrics as reminder
- Always visible at top of dashboard
- Does NOT show the recommendation itself (that's on Journal)
- Replaces the bottom "Get My Coach" banner

---

## COMPONENT 3: JOURNAL TAB BADGE

### Purpose
Visual indicator that there's something waiting on Journal.

### Design
```
[Dashboard]  [Activities]  [Journal 🔴]  [Coach]  [Guide]  [Settings]
```

Or with a "NEW" badge:
```
[Dashboard]  [Activities]  [Journal NEW]  [Coach]  [Guide]  [Settings]
```

### When to Show
- When user hasn't visited Journal today
- When user dismissed the pop-up with "Remind Me Later"
- Clear badge after user visits Journal

---

## IMPLEMENTATION TASKS

### Task 1: Create DailyStatusPopup Component

**File:** `frontend/src/DailyStatusPopup.tsx`

```typescript
interface DailyStatusPopupProps {
  metrics: {
    externalAcwr: number;
    internalAcwr: number;
    normalizedDivergence: number;
    daysSinceRest: number;
  };
  onNavigateToJournal: () => void;
  onDismiss: () => void;
}

export const DailyStatusPopup: React.FC<DailyStatusPopupProps> = ({
  metrics,
  onNavigateToJournal,
  onDismiss
}) => {
  // Calculate status labels and risk assessment
  const acwrStatus = getAcwrStatus(metrics.externalAcwr);
  const divergenceStatus = getDivergenceStatus(metrics.normalizedDivergence);
  const riskLevel = calculateRiskLevel(metrics);
  const interpretation = generateInterpretation(metrics, riskLevel);
  const briefRecommendation = generateBriefRecommendation(riskLevel, metrics.daysSinceRest);

  return (
    <div className="popup-overlay">
      <div className="popup-content">
        <button className="popup-close" onClick={onDismiss}>✕</button>

        <h2>YOUR TRAINING STATUS</h2>

        {/* Metrics Display */}
        <div className="metrics-row">
          <div className="metric-card">
            <div className="metric-value">{metrics.externalAcwr.toFixed(2)}</div>
            <div className="metric-label">ACWR</div>
            <div className={`metric-status status-${acwrStatus.color}`}>
              {acwrStatus.label}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{metrics.normalizedDivergence.toFixed(2)}</div>
            <div className="metric-label">Divergence</div>
            <div className={`metric-status status-${divergenceStatus.color}`}>
              {divergenceStatus.label}
            </div>
          </div>
        </div>

        {/* Risk Assessment */}
        <div className={`risk-banner risk-${riskLevel.toLowerCase()}`}>
          INJURY RISK: {riskLevel}
        </div>

        {/* Interpretation */}
        <p className="interpretation">
          {interpretation}
        </p>

        {/* Brief Recommendation */}
        <div className="recommendation-preview">
          <h3>TODAY'S RECOMMENDATION:</h3>
          <p>{briefRecommendation}</p>
        </div>

        {/* Actions */}
        <div className="popup-actions">
          <button className="btn-primary" onClick={onNavigateToJournal}>
            See Full Analysis & Log Your Workout →
          </button>
          <button className="btn-secondary" onClick={onDismiss}>
            Remind Me Later
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper functions
function getAcwrStatus(acwr: number) {
  if (acwr < 0.8) return { label: 'UNDERTRAINED', color: 'blue' };
  if (acwr <= 1.1) return { label: 'OPTIMAL', color: 'green' };
  if (acwr <= 1.3) return { label: 'BUILDING', color: 'yellow' };
  if (acwr <= 1.5) return { label: 'ELEVATED', color: 'orange' };
  return { label: 'HIGH RISK', color: 'red' };
}

function getDivergenceStatus(divergence: number) {
  if (divergence > 0.05) return { label: 'FRESH', color: 'green' };
  if (divergence >= -0.05) return { label: 'NEUTRAL', color: 'yellow' };
  if (divergence >= -0.15) return { label: 'FATIGUED', color: 'orange' };
  return { label: 'OVERREACHING', color: 'red' };
}

function calculateRiskLevel(metrics) {
  const { externalAcwr, normalizedDivergence } = metrics;

  if (externalAcwr > 1.3 && normalizedDivergence < -0.05) return 'HIGH';
  if (externalAcwr > 1.3 || normalizedDivergence < -0.05) return 'MODERATE';
  if (externalAcwr < 0.8) return 'LOW';
  return 'LOW';
}

function generateInterpretation(metrics, riskLevel) {
  const { externalAcwr, normalizedDivergence } = metrics;

  if (riskLevel === 'HIGH') {
    return 'Your training load is elevated and your body is showing signs of accumulated fatigue. Your heart rate has been running higher than expected for your effort levels.';
  }

  if (externalAcwr > 1.3) {
    return 'Your training load is elevated. Monitor how your body responds and consider easier sessions.';
  }

  if (normalizedDivergence < -0.05) {
    return 'Your body is showing signs of accumulated fatigue. Your heart rate has been running higher than expected.';
  }

  if (externalAcwr >= 0.8 && externalAcwr <= 1.1 && normalizedDivergence >= -0.05) {
    return 'You\'re in the optimal training zone with good recovery indicators. Your body is adapting well to training.';
  }

  if (externalAcwr < 0.8) {
    return 'Your recent training load is lower than optimal. You have room to build volume safely.';
  }

  return 'Your training metrics are within normal ranges. Continue monitoring your progress.';
}

function generateBriefRecommendation(riskLevel, daysSinceRest) {
  if (riskLevel === 'HIGH') {
    return 'Rest day strongly recommended';
  }

  if (riskLevel === 'MODERATE' && daysSinceRest > 5) {
    return 'Easy recovery or rest day';
  }

  if (riskLevel === 'MODERATE') {
    return 'Light training - monitor how you feel';
  }

  return 'You\'re primed for a quality session today';
}
```

---

### Task 2: Create TeaserCard Component

**File:** `frontend/src/JournalTeaserCard.tsx`

```typescript
interface JournalTeaserCardProps {
  metrics: {
    externalAcwr: number;
    normalizedDivergence: number;
  };
  onNavigateToJournal: () => void;
}

export const JournalTeaserCard: React.FC<JournalTeaserCardProps> = ({
  metrics,
  onNavigateToJournal
}) => {
  const acwrStatus = getAcwrStatus(metrics.externalAcwr);
  const divergenceStatus = getDivergenceStatus(metrics.normalizedDivergence);

  return (
    <div className="teaser-card">
      <div className="teaser-content">
        <span className="teaser-message">
          Your daily training recommendation is ready
        </span>
        <span className="teaser-metrics">
          ACWR: {metrics.externalAcwr.toFixed(2)} ({acwrStatus.label}) •
          Divergence: {metrics.normalizedDivergence.toFixed(2)} ({divergenceStatus.label})
        </span>
      </div>
      <button className="teaser-cta" onClick={onNavigateToJournal}>
        View on Journal →
      </button>
    </div>
  );
};
```

---

### Task 3: Update Dashboard to Include Pop-up and Teaser

**File:** `frontend/src/TrainingLoadDashboard.tsx`

```typescript
// Add state for pop-up visibility
const [showStatusPopup, setShowStatusPopup] = useState(false);

// Check if should show pop-up on mount
useEffect(() => {
  const today = new Date().toDateString();
  const lastShown = localStorage.getItem('statusPopup_lastShown');
  const visitedJournalToday = localStorage.getItem('journal_visited_' + today);

  if (lastShown !== today && !visitedJournalToday && metrics.externalAcwr > 0) {
    setShowStatusPopup(true);
  }
}, [metrics]);

// Handle navigation to Journal
const handleNavigateToJournal = () => {
  localStorage.setItem('statusPopup_lastShown', new Date().toDateString());
  setShowStatusPopup(false);
  onNavigateToTab?.('journal');
};

// Handle dismiss
const handleDismissPopup = () => {
  localStorage.setItem('statusPopup_lastShown', new Date().toDateString());
  setShowStatusPopup(false);
  // Badge will show on Journal tab (handled by App.tsx)
};

// In render:
return (
  <div>
    {/* Pop-up (conditional) */}
    {showStatusPopup && (
      <DailyStatusPopup
        metrics={metrics}
        onNavigateToJournal={handleNavigateToJournal}
        onDismiss={handleDismissPopup}
      />
    )}

    {/* Teaser Card (always visible at top) */}
    <JournalTeaserCard
      metrics={metrics}
      onNavigateToJournal={() => onNavigateToTab?.('journal')}
    />

    {/* Rest of dashboard... */}
    <CompactDashboardBanner ... />
    {/* Charts, etc. */}

    {/* REMOVE the bottom "Get My Coach" section */}
  </div>
);
```

---

### Task 4: Add Badge to Journal Tab

**File:** `frontend/src/App.tsx` (or navigation component)

```typescript
// Track if user should see badge
const [showJournalBadge, setShowJournalBadge] = useState(false);

useEffect(() => {
  const today = new Date().toDateString();
  const visitedJournalToday = localStorage.getItem('journal_visited_' + today);
  setShowJournalBadge(!visitedJournalToday);
}, []);

// Clear badge when Journal is visited
const handleTabChange = (tab: string) => {
  if (tab === 'journal') {
    localStorage.setItem('journal_visited_' + new Date().toDateString(), 'true');
    setShowJournalBadge(false);
  }
  setActiveTab(tab);
};

// In navigation render:
<a
  href="#journal"
  className={activeTab === 'journal' ? 'active' : ''}
  onClick={() => handleTabChange('journal')}
>
  Journal {showJournalBadge && <span className="badge">NEW</span>}
</a>
```

---

### Task 5: Remove Bottom "Get My Coach" Banner

**File:** `frontend/src/TrainingLoadDashboard.tsx`

Remove or comment out the entire "Coaching Link Section" (lines ~1161-1308) that contains:
- "Ready for Your Personal AI Coach?"
- "Get My Coach" button

This is replaced by the progressive approach (pop-up → teaser → Journal → Coach).

---

## SUCCESS METRICS

### Primary Metrics:
- **Pop-up → Journal click rate:** Target >50%
- **Teaser card → Journal click rate:** Target >30%
- **Journal page visits:** Increase from baseline
- **Time to first Journal visit:** Reduce from baseline

### Google Analytics Events:
```typescript
// Track pop-up interactions
gtag('event', 'status_popup_shown', { risk_level: riskLevel });
gtag('event', 'status_popup_click_journal');
gtag('event', 'status_popup_dismiss');

// Track teaser interactions
gtag('event', 'teaser_card_click_journal');

// Track Journal badge
gtag('event', 'journal_badge_shown');
gtag('event', 'journal_visit_from_badge');
```

---

## TESTING CHECKLIST

- [ ] Pop-up shows on first dashboard visit of the day
- [ ] Pop-up does NOT show if user already visited Journal today
- [ ] Pop-up shows correct ACWR and Divergence values
- [ ] Risk level calculation is correct
- [ ] Interpretation text matches metrics
- [ ] "See Full Analysis" navigates to Journal
- [ ] "Remind Me Later" dismisses and shows badge
- [ ] Pop-up doesn't show again same day after dismiss
- [ ] Teaser card always visible at top of dashboard
- [ ] Teaser card links to Journal
- [ ] Badge shows on Journal tab when appropriate
- [ ] Badge clears after visiting Journal
- [ ] Bottom "Get My Coach" banner is removed

---

## NEXT STEPS (After Phase 1)

Once users are consistently visiting Journal:
- **Phase 2:** Enhance autopsy to be incredibly impressive (AHA moment)
- **Phase 3:** Progressive CTAs for Stages 3-6 (personalization, race goals, schedule)
- **Phase 4:** Coach page promotion (only after Journal engagement established)

---

**END OF PHASE 1 ACTION PLAN - Ready to Implement**
