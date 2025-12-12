# Chat Context Universes Map

Complete reference for all chat universes, their context data, and token usage.

---

## Base Context (All Universes)
**Token Estimate:** ~800-1200 tokens
**Loaded once per session, cached for 5 minutes**

### Context Includes:
- **Coaching Tone Instructions**: Personalized based on user settings
- **Risk Tolerance**: User's risk threshold (BALANCED, CONSERVATIVE, AGGRESSIVE)
- **Threshold Descriptions**: Custom ACWR/divergence thresholds
- **Training Guide**: Reference framework for training metrics

---

## 1. AI Autopsy Universe
**Selection:** "AI Autopsy"
**Token Estimate:** ~2000-2500 tokens
**Best For:** Questions about workout analysis, alignment scores, prescribed vs actual training

### Context Includes:
- **Latest Autopsy**: Most recent AI workout analysis
  - Alignment score
  - Workout comparison (prescribed vs actual)
  - Pattern analysis
  - Learning insights
- **Journal Observations**: Notes from that workout day
- **Metrics Snapshot**: ACWR, divergence, load metrics at time of workout

### Example Questions:
- "Why was my alignment score low?"
- "What did you learn from comparing my prescribed vs actual workout?"
- "Explain my latest autopsy analysis"

---

## 2. Training Plan Universe
**Selection:** "Training Plan"
**Token Estimate:** ~4000-5000 tokens (MOST COMPREHENSIVE)
**Best For:** Questions about weekly programs, race strategy, periodization, overall plan

### Context Includes:
- **Weekly Program**: Current week's workout plan (cached, not generated)
- **Race Goals**: Top 3 goals with priorities (A/B/C)
- **Race History**: Recent 5 race results
- **Performance Trend**: Fitness progression analysis
- **Training Stage**: Current phase (Base/Build/Specificity/Taper/Peak)
- **Training Schedule**: Weekly availability and time blocks
- **Current Metrics**: Latest ACWR, divergence, load data
- **Pattern Flags**: Training pattern analysis
- **Autopsy Insights**: Last 7 days of AI analysis
- **Journal Observations**: Recent journal entries

### Example Questions:
- "How does this week's plan prepare me for my race?"
- "Why are you recommending more volume now?"
- "What's my training phase and why?"
- "How do my race goals affect my training?"

---

## 3. Today's Workout Universe
**Selection:** "Today's Workout"
**Token Estimate:** ~3000-3500 tokens
**Best For:** Questions about today's specific recommendation, modifications, workout details

### Context Includes:
- **Daily Recommendation**: Today's specific workout prescription
- **Today's Program**: Details from weekly program for today
- **Current Metrics**: Latest ACWR, divergence, load data
- **Pattern Flags**: Recent training patterns
- **Autopsy Insights**: Last 3 days of AI analysis
- **Recent Journal Notes**: Last 3 days of observations

### Example Questions:
- "Can I modify today's workout?"
- "Why am I doing intervals today?"
- "What if I can't complete the full workout?"
- "How does today fit into my weekly plan?"

---

## 4. My Progress Universe
**Selection:** "My Progress"
**Token Estimate:** ~3000-3500 tokens
**Best For:** Questions about fitness trends, performance analysis, long-term progress

### Context Includes:
- **Current Metrics**: Latest ACWR, divergence, load data
- **Activities Summary**: Last 28 days (total activities, distance, elevation, avg HR)
- **Pattern Flags**: Training pattern analysis
- **Performance Trend**: Race performance progression
- **Race History**: Recent 5 race results
- **Autopsy Insights**: Last 7 days of AI analysis
- **Athlete Profile**: Classification (Elite/Advanced/Intermediate/Beginner)

### Example Questions:
- "How is my fitness progressing?"
- "Am I improving compared to last month?"
- "What patterns do you see in my training?"
- "How do my recent race results compare?"

---

## 5. General Coaching Universe
**Selection:** "General Coaching"
**Token Estimate:** ~800-1200 tokens (MOST EFFICIENT)
**Best For:** General training questions, technique, nutrition, recovery, injury management

### Context Includes:
- **A Race Summary**: Primary race goal and date
- **Training Stage**: Current phase with weeks to race
- **Athlete Profile**: Classification (Elite/Advanced/Intermediate/Beginner)
- **Recent Journal Notes**: Last 7 days, up to 5 entries (includes injury/fatigue notes)

### Example Questions:
- "What should I focus on given my injury?"
- "General advice on nutrition for ultras?"
- "How should I approach recovery days?"
- "Tips for running in hot weather?"

---

## Token Budget Management

Each universe has a token budget enforced by the ContextManager:

| Universe | Budget | Usage |
|----------|--------|-------|
| General | 1,000 tokens | Most efficient for simple questions |
| AI Autopsy | 3,000 tokens | Focused on single workout analysis |
| Today's Workout | 3,500 tokens | Today's context only |
| My Progress | 3,500 tokens | Historical performance focus |
| Training Plan | 5,000 tokens | Most comprehensive, full context |

**Note:** Token budgets include both the base context (~800-1200) plus universe-specific context.

---

## Choosing the Right Universe

### Use **General Coaching** when:
- Asking general training advice
- Discussing injuries or fatigue (includes journal notes)
- Questions about technique, nutrition, recovery
- Want quick, efficient responses

### Use **AI Autopsy** when:
- Reviewing yesterday's workout analysis
- Understanding alignment scores
- Learning what the AI observed about your training

### Use **Today's Workout** when:
- Clarifying today's recommendation
- Need workout modifications
- Want context about today's specific session

### Use **My Progress** when:
- Analyzing fitness trends
- Comparing performance over time
- Understanding training patterns

### Use **Training Plan** when:
- Questions about overall strategy
- Understanding periodization
- Discussing race preparation
- Need full context about everything

---

## Data Sources

All context is loaded **read-only** from the database:
- ✅ No API calls triggered by chat
- ✅ Fast responses (cached data)
- ✅ No unexpected costs
- ✅ Weekly programs not regenerated

Context is refreshed via:
- Weekly program generation (Sunday evening cron)
- Autopsy generation (nightly cron)
- Real-time metric calculations (on activity sync)
- Journal entries (user input on Journal page)

---

Last Updated: December 2025
