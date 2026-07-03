# Profile/Training vs Coach Page Reconciliation Analysis

## Executive Summary

The Coach page (launched recently) has created **significant redundancy** with the existing Settings/Training page. The Coach page uses separate dedicated database tables (`race_goals`, `race_history`, `training_schedule_json` in `user_settings`) while the Settings/Training page uses older single fields (`race_goal_date`, `current_phase`, `weekly_training_hours`).

**Critical Issue**: Two parallel systems for managing race goals and training configuration with no clear migration path.

---

## Current State: Redundant Fields

### Settings/Training Page (Legacy System)
**Location**: `/settings/training` template: `app/templates/settings_training.html`  
**Database**: `user_settings` table

| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| `primary_sport` | VARCHAR | Primary training focus | ✅ **KEEP** - Still needed |
| `secondary_sport` | VARCHAR | Cross-training sport | ✅ **KEEP** - Still needed |
| `training_experience` | VARCHAR | Skill level (beginner/intermediate/advanced/elite) | ✅ **KEEP** - Used by Coach for program generation |
| `weekly_training_hours` | INTEGER | Basic weekly volume | ⚠️ **REDUNDANT** - Superseded by detailed schedule |
| `current_phase` | VARCHAR | Manual phase selection (base/build/peak/race/recovery) | ⚠️ **REDUNDANT** - Coach calculates this automatically |
| `race_goal_date` | DATE | Single race date | 🔴 **DEPRECATED** - Replaced by `race_goals` table |

### Coach Page (New System)
**Location**: `/coach` (CoachPage.tsx) with 4 tabs  
**Database**: Dedicated tables + new `user_settings` columns

| Feature | Database Storage | Purpose | Status |
|---------|-----------------|---------|--------|
| **Goals Tab** | `race_goals` table | Multiple races with A/B/C priorities | ✅ **ACTIVE** |
| **History Tab** | `race_history` table | Past race performances for trend analysis | ✅ **ACTIVE** |
| **Schedule Tab** | `user_settings.training_schedule_json` (JSONB) | Day-by-day availability, time blocks, constraints | ✅ **ACTIVE** |
| **Supplemental Training** | `include_strength_training`, `strength_hours_per_week`, etc. | Strength/mobility/cross-training config | ✅ **ACTIVE** |

---

## Conflicts & Issues

### 1. **Race Goal Date Conflict** 🔴 CRITICAL

- **Legacy**: Single `race_goal_date` field in `user_settings`
- **New**: Multiple races in `race_goals` table with priorities
- **Problem**: Two sources of truth - users could have both populated
- **Impact**: Coach page ignores `race_goal_date` entirely

**Migration Status Unknown**: Need to run Query 2 to see how many users have legacy `race_goal_date` set.

### 2. **Training Volume Duplication** ⚠️

- **Legacy**: `weekly_training_hours` - single number (e.g., "10 hours/week")
- **New**: `training_schedule_json` - detailed breakdown with available days, time blocks, supplemental training
- **Problem**: Which is authoritative when both exist?
- **Current Behavior**: Coach page uses detailed schedule if available, falls back to basic hours

### 3. **Training Phase Ambiguity** ⚠️

- **Legacy**: Manual `current_phase` selection (user chooses base/build/peak/race/recovery)
- **New**: Automatic stage calculation based on race goals and timeline
- **Problem**: Manual setting could conflict with automated calculation
- **Current Behavior**: Coach page calculates stage dynamically, ignores `current_phase`

### 4. **User Experience Confusion** 📉

Users must visit **two different locations** to configure training:
- **Settings/Training**: Basic info (sport, experience, old race date, phase)
- **Coach Page**: Goals, history, detailed schedule

No indication in Settings that fields are deprecated or superseded by Coach page.

---

## Database Impact Assessment

### Tables Involved

1. **`user_settings`** - Main user configuration (both systems)
2. **`race_goals`** - New (Coach page only)
3. **`race_history`** - New (Coach page only)

### Fields Status

```
user_settings table:
├── primary_sport              ✅ KEEP - Used by both
├── secondary_sport            ✅ KEEP - Used by both  
├── training_experience        ✅ KEEP - Used by Coach for program generation
├── weekly_training_hours      ⚠️  REDUNDANT - Use detailed schedule instead
├── current_phase              ⚠️  REDUNDANT - Coach calculates automatically
├── race_goal_date             🔴 DEPRECATED - Migrate to race_goals table
├── training_schedule_json     ✅ KEEP - Coach page feature
├── include_strength_training  ✅ KEEP - Coach page feature
├── strength_hours_per_week    ✅ KEEP - Coach page feature
├── include_mobility           ✅ KEEP - Coach page feature
├── mobility_hours_per_week    ✅ KEEP - Coach page feature
├── include_cross_training     ✅ KEEP - Coach page feature
├── cross_training_type        ✅ KEEP - Coach page feature
└── cross_training_hours_per_week  ✅ KEEP - Coach page feature
```

---

## Recommended Reconciliation Plan

### Phase 1: Data Assessment (IMMEDIATE)

**Run the analysis queries** to understand current state:

```bash
# Run queries in TRAINING_SETTINGS_ANALYSIS_QUERIES.sql
psql $DATABASE_URL -f TRAINING_SETTINGS_ANALYSIS_QUERIES.sql
```

**Key Questions to Answer**:
1. How many users have `race_goal_date` populated?
2. How many users have BOTH `race_goal_date` AND entries in `race_goals`?
3. How many users have detailed schedule vs basic weekly hours?
4. What's the adoption rate of Coach page features?

### Phase 2: Quick Fixes (1-2 days)

#### 2.1 Add Deprecation Warnings
Update `app/templates/settings_training.html`:

```html
<!-- Add warning banner at top -->
<div class="warning-banner" style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; margin-bottom: 20px; border-radius: 8px;">
    <h3 style="color: #856404; margin-top: 0;">ℹ️ New Coach Page Available</h3>
    <p>Configure your race goals and detailed training schedule in the new <a href="/?tab=coach" style="font-weight: bold;">Coach Page</a>.</p>
</div>

<!-- Modify race_goal_date field -->
<div class="form-group">
    <label for="race_goal_date">
        Race Goal Date (Optional) 
        <span style="color: #dc3545; font-weight: bold;">⚠️ DEPRECATED</span>
    </label>
    <input type="date" id="race_goal_date" name="race_goal_date" ...>
    <small style="color: #dc3545;">
        This field is deprecated. Please use 
        <a href="/?tab=coach" target="_blank">Coach > Goals</a> 
        to manage your race goals.
    </small>
</div>

<!-- Modify current_phase field -->
<div class="form-group">
    <label for="current_phase">Current Training Phase</label>
    <select id="current_phase" name="current_phase" ...>
        ...
    </select>
    <small style="color: #6b7280;">
        Note: When race goals are configured in the Coach page, 
        your training phase is calculated automatically.
    </small>
</div>
```

####2.2 Add Link in Coach Page
In `frontend/src/CoachPage.tsx`, add a Settings link:

```typescript
// In the header/navigation area
<div className={styles.settingsLink}>
    <a href="/settings/training" target="_blank">
        ⚙️ Training Settings (Sport, Experience)
    </a>
</div>
```

### Phase 3: Data Migration (Week 1)

#### 3.1 Migration Script: Legacy Race Date → Race Goals Table

Create `app/migrate_legacy_race_goals.py`:

```python
#!/usr/bin/env python3
"""
Migration: Convert legacy race_goal_date to race_goals table entries
"""

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

def migrate_legacy_race_goals():
    print("=" * 60)
    print("Migrating legacy race_goal_date to race_goals table")
    print("=" * 60)
    
    # Find users with race_goal_date but no race_goals entries
    users = db_utils.execute_query("""
        SELECT id, email, race_goal_date 
        FROM user_settings 
        WHERE race_goal_date IS NOT NULL 
        AND id NOT IN (SELECT DISTINCT user_id FROM race_goals)
        AND email IS NOT NULL
    """, fetch=True)
    
    print(f"\nFound {len(users)} users with legacy race_goal_date to migrate\n")
    
    migrated_count = 0
    for user in users:
        user_id = user['id']
        race_date = user['race_goal_date']
        email = user['email']
        
        print(f"Migrating user {user_id} ({email}): {race_date}")
        
        # Create A-priority race goal from legacy date
        db_utils.execute_query("""
            INSERT INTO race_goals 
            (user_id, race_name, race_date, priority, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, 'Goal Race (Migrated)', race_date, 'A'))
        
        migrated_count += 1
    
    print(f"\n✅ Successfully migrated {migrated_count} race goals")
    print("\nNote: Legacy race_goal_date fields NOT deleted (preserved for rollback)")
    print("=" * 60)

if __name__ == '__main__':
    migrate_legacy_race_goals()
```

**Run Migration**:
```bash
cd app
python migrate_legacy_race_goals.py
```

### Phase 4: UI Consolidation (Week 2-3)

#### 4.1 Reorganize Settings Page

**Current Structure**:
- Profile Settings (`settings_profile.html`)
- HR Zones Settings (`settings_hrzones.html`)
- Training Settings (`settings_training.html`) ← **CONSOLIDATE THIS**
- Coaching Style (`settings_coaching.html`)

**Proposed Structure**:
```
Settings Page
├── Profile (email, birthdate, gender)
├── Sports & Experience
│   ├── Primary Sport
│   ├── Secondary Sport  
│   └── Training Experience Level
├── Heart Rate Zones
└── Coaching Style
```

**Remove from Settings**:
- ~~Race Goal Date~~ → Moved to Coach > Goals
- ~~Current Phase~~ → Auto-calculated by Coach
- ~~Weekly Training Hours~~ → Moved to Coach > Schedule

#### 4.2 Expand Coach Page

Add a new "Profile" or "Settings" sub-tab in Coach page for quick access to:
- Primary/Secondary Sport
- Training Experience
- Link back to full Settings page

### Phase 5: Database Cleanup (3-6 months after migration)

After monitoring period, optionally deprecate unused columns:

```sql
-- Mark as deprecated (rename, don't drop)
ALTER TABLE user_settings 
  RENAME COLUMN race_goal_date TO race_goal_date_deprecated;

ALTER TABLE user_settings 
  RENAME COLUMN current_phase TO current_phase_deprecated;

-- Add comment for future reference
COMMENT ON COLUMN user_settings.race_goal_date_deprecated IS 
  'Deprecated 2025-12. Migrated to race_goals table. Preserved for historical reference.';
```

---

## Migration Checklist

- [ ] **STEP 1**: Run analysis queries (`TRAINING_SETTINGS_ANALYSIS_QUERIES.sql`)
- [ ] **STEP 2**: Review query results with user
- [ ] **STEP 3**: Add deprecation warnings to Settings/Training page
- [ ] **STEP 4**: Create and test migration script
- [ ] **STEP 5**: Backup database before migration
- [ ] **STEP 6**: Run migration script for legacy `race_goal_date`
- [ ] **STEP 7**: Verify migration success (check race_goals table)
- [ ] **STEP 8**: Update Settings page UI (remove deprecated fields)
- [ ] **STEP 9**: Add Settings link to Coach page
- [ ] **STEP 10**: Monitor for 3-6 months
- [ ] **STEP 11**: (Optional) Rename deprecated database columns

---

## Testing Plan

### Pre-Migration Tests
1. Export current `race_goal_date` values
2. Count users in each category (CONFLICT, MIGRATE, OK, EMPTY)
3. Verify Coach page functionality with existing data

### Post-Migration Tests
1. Verify all legacy `race_goal_date` values migrated to `race_goals`
2. Test Coach page displays migrated goals correctly
3. Test weekly program generation uses migrated goals
4. Verify no users lost their race goal data
5. Test Settings page shows deprecation warnings

### Rollback Plan
If migration fails:
1. Delete migrated entries: `DELETE FROM race_goals WHERE race_name = 'Goal Race (Migrated)'`
2. Legacy `race_goal_date` values still intact (not deleted)
3. Restore previous Settings page template

---

## Impact Summary

### User Benefits
✅ Single source of truth for race goals  
✅ Clearer UI - one location for training configuration  
✅ Better features (multiple races, priorities, race history)  
✅ Automatic training stage calculation  

### Technical Benefits
✅ Reduced data redundancy  
✅ Cleaner database schema  
✅ Easier maintenance (one system instead of two)  
✅ Better scalability for future features  

### Risks
⚠️ Users may be confused by UI changes  
⚠️ Migration script must not lose data  
⚠️ Need clear communication about deprecation  

---

## Next Steps

1. **Run the analysis queries** in `TRAINING_SETTINGS_ANALYSIS_QUERIES.sql`
2. **Share results** to understand current data state
3. **Decide on timeline** for Phase 2 (deprecation warnings)
4. **Create migration script** for Phase 3
5. **Test migration** on staging/development environment first

---

## Files to Modify

### Frontend
- `frontend/src/CoachPage.tsx` - Add Settings link
- (Future) Add Sport/Experience to Coach page

### Backend Templates
- `app/templates/settings_training.html` - Add deprecation warnings
- (Future) Reorganize settings structure

### Database
- Migration script: `app/migrate_legacy_race_goals.py` (to create)
- (Future) Rename deprecated columns

### Documentation
- ✅ `TRAINING_SETTINGS_ANALYSIS_QUERIES.sql` - Analysis queries
- ✅ `PROFILE_TRAINING_COACH_RECONCILIATION.md` - This document


