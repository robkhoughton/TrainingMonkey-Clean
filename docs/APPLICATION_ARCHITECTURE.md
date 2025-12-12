# TrainingMonkey Application Architecture Documentation

**Generated:** 2025-12-07
**Version:** 1.0
**Purpose:** Complete dependency map and architecture overview

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Application Statistics](#application-statistics)
3. [Python Code Dependency Tree](#python-code-dependency-tree)
4. [Template Rendering Map](#template-rendering-map)
5. [Route-to-Template Mappings](#route-to-template-mappings)
6. [Static Assets](#static-assets)
7. [Data Dependencies](#data-dependencies)
8. [Complete Architecture Diagram](#complete-architecture-diagram)
9. [Refactoring Opportunities](#refactoring-opportunities)

---

## Executive Summary

TrainingMonkey is a Flask-based web application that provides AI-powered training recommendations for endurance athletes. The application integrates with Strava for activity data and uses Claude AI for generating personalized coaching insights.

### Key Metrics

- **Total Files:** 127 files
- **Total Lines of Code:** 64,383 lines
- **Python Modules:** 28 files (28,726 lines)
- **HTML Templates:** 39 files (31,061 lines)
- **JavaScript:** 32 files (1,197 lines)
- **CSS:** 4 files (2,989 lines)
- **Images:** 23 files
- **Routes:** 250+ endpoints (39 render HTML, 211+ return JSON)

---

## Application Statistics

### Code Distribution

| Component | Files | Lines | % of Total |
|-----------|-------|-------|-----------|
| **Python Code** | | | |
| ├─ Tier 0 (strava_app.py) | 1 | 12,438 | 25.9% |
| ├─ Tier 1 (Direct deps) | 21 | 12,630 | 26.3% |
| ├─ Tier 2 (Services) | 6 | 3,658 | 7.6% |
| **Data Assets** | | | |
| └─ Training Guide | 1 | 410 | 0.9% |
| **Frontend** | | | |
| ├─ HTML Templates | 39 | 31,061 | 64.7% |
| ├─ CSS | 4 | 2,989 | 6.2% |
| ├─ JavaScript | 32 | 1,197 | 2.5% |
| ├─ Images | 23 | - | - |
| **TOTAL** | **127** | **64,383** | **100%** |

### Size Comparison

```
Python Code:  28,726 lines (45%)  ████████████████████████
Templates:    31,061 lines (49%)  ██████████████████████████
CSS:           2,989 lines (5%)   ███
JavaScript:    1,197 lines (2%)   █
```

---

## Python Code Dependency Tree

### Tier 0: Root Application
**Total: 1 file, 12,438 lines**

```
strava_app.py [12,438 lines]
├─ Main Flask application entry point
├─ Defines 250+ routes
├─ Registers 4 Blueprints
└─ Serves React SPA at /dashboard
```

### Tier 1: Direct Dependencies
**Total: 21 files, 12,630 lines (avg 601 lines/file)**

**Core Services:**
- `llm_recommendations_module.py` [2,294] - AI-powered training recommendations
- `strava_training_load.py` [2,034] - Strava API integration & training load calculations
- `db_utils.py` [1,145] - Database utility functions
- `enhanced_token_management.py` [1,138] - OAuth token management
- `acwr_visualization_routes.py` [930] - ACWR visualization Blueprint
- `acwr_configuration_admin.py` [945] - ACWR configuration Blueprint
- `acwr_migration_admin.py` [804] - ACWR migration Blueprint
- `csrf_protection.py` [528] - CSRF protection
- `optimized_acwr_service.py` [516] - Optimized ACWR calculations
- `optimized_token_management.py` [421] - Batch token refresh
- `settings_utils.py` [416] - Settings management
- `db_connection_manager.py` [294] - Connection pooling
- `acwr_feature_flag_admin.py` [236] - Feature flags Blueprint
- `timezone_utils.py` [190] - Timezone handling
- `sync_fix.py` [165] - Data sync fixes
- `auth.py` [150] - Authentication

**Utilities Package:**
- `utils/data_aggregation.py` [223] - Activity aggregation
- `utils/feature_flags.py` [110] - Feature flag system
- `utils/date_processing.py` [47] - Date serialization
- `utils/secrets_manager.py` [27] - Cloud secrets
- `utils/__init__.py` [17] - Package init

### Tier 2: Secondary Dependencies
**Total: 7 files, 4,158 lines (avg 594 lines/file)**

- `acwr_configuration_service.py` [1,014] - ACWR config management
  - Depends on: `exponential_decay_engine.py`
- `acwr_visualization_service.py` [710] - Visualization data service
- `acwr_migration_service.py` [694] - Migration orchestration
- `unified_metrics_service.py` [599] - Unified metrics
- `exponential_decay_engine.py` [~500] - Exponential decay calculations ★ Critical
- `acwr_calculation_service.py` [386] - Core ACWR calculations
- `acwr_feature_flag_monitor.py` [255] - Feature flag monitoring

### Dependency Insights

**Largest Python Files:**
1. strava_app.py: 12,438 lines (43% of Python code)
2. llm_recommendations_module.py: 2,294 lines
3. strava_training_load.py: 2,034 lines
4. db_utils.py: 1,145 lines
5. enhanced_token_management.py: 1,138 lines

**Most Connected Modules:**
- `db_utils.py` - imported by 10+ modules
- `acwr_configuration_service.py` - imported by 6 modules
- `timezone_utils.py` - imported by LLM and Strava modules

**Dependency Depth:** Shallow (only 2 tiers), indicating good modular design

---

## Template Rendering Map

### Module-to-Template Rendering

#### strava_app.py
**Renders 21 unique templates + 1 React SPA**

**Public Pages (7 templates):**
- `landing.html` - Route: `/`
- `guide.html` - Route: `/guide`
- `faq.html` - Route: `/faq`
- `tutorials.html` - Route: `/tutorials`
- `getting_started_resources.html` - Route: `/getting-started`
- `legal/terms.html` - Route: `/legal/terms`
- `legal/privacy.html` - Route: `/legal/privacy`
- `legal/disclaimer.html` - Route: `/legal/disclaimer`

**Authentication (3 templates):**
- `login.html` - Route: `/login`
- `signup.html` - Routes: `/signup`, `/signup/resume/<id>`
- `strava_setup.html` - Route: `/strava-setup`

**Onboarding (3 templates):**
- `onboarding.html` - Route: `/dashboard/first-time`
- `welcome_post_strava.html` - Route: `/welcome-post-strava`
- `goals_setup.html` - Route: `/goals-setup`

**Settings (5 templates):**
- `settings_profile.html` - Route: `/settings/profile`
- `settings_hrzones.html` - Route: `/settings/hrzones`
- `settings_training.html` - Route: `/settings/training`
- `settings_coaching.html` - Route: `/settings/coaching`
- `settings_acwr.html` - Route: `/settings/acwr`

**Admin (1 template):**
- `admin_trimp_settings.html` - Route: `/admin/trimp-settings`

**Error Pages (1 template):**
- `error.html` - Error handler

**React SPA (1 file):**
- `build/index.html` - Routes: `/dashboard`, `/<path>` (catch-all)

#### acwr_migration_admin.py
**Renders 5 templates**

- `migration_dashboard.html` - Route: `/admin/migration/`
- `create_migration.html` - Route: `/admin/migration/create`
- `monitor_migration.html` - Route: `/admin/migration/monitor/<id>`
- `migration_history.html` - Route: `/admin/migration/history`
- `migration_alerts.html` - Route: `/admin/migration/alerts`

#### acwr_configuration_admin.py
**Renders 1 template**

- `admin_acwr_configuration.html` - Route: `/admin/acwr-configuration`

#### acwr_feature_flag_admin.py
**Renders 1 template**

- `admin_acwr_feature_flags.html` - Route: `/admin/acwr-feature-flags`

#### acwr_visualization_routes.py
**Renders 1 template**

- `acwr_visualization_dashboard.html` - Route: `/acwr-visualization`

### Template Usage Summary

| Python Module | Templates | Lines of Code |
|---------------|-----------|---------------|
| strava_app.py | 21 | 12,438 |
| acwr_migration_admin.py | 5 | 804 |
| acwr_configuration_admin.py | 1 | 945 |
| acwr_feature_flag_admin.py | 1 | 236 |
| acwr_visualization_routes.py | 1 | 930 |
| **TOTAL** | **29** | **15,353** |

---

## Route-to-Template Mappings

### Server-Rendered HTML Routes (39 unique templates)

#### Public Routes (8)
- `/` → `landing.html`
- `/landing` → `landing.html`
- `/guide` → `guide.html`
- `/faq` → `faq.html`
- `/tutorials` → `tutorials.html`
- `/getting-started` → `getting_started_resources.html`
- `/legal/terms` → `legal/terms.html`
- `/legal/privacy` → `legal/privacy.html`
- `/legal/disclaimer` → `legal/disclaimer.html`

#### Authentication Routes (5)
- `/login` → `login.html`
- `/signup` → `signup.html`
- `/signup/resume/<int:user_id>` → `signup.html`
- `/auth/strava` → Redirect to Strava OAuth
- `/auth/strava-signup` → Redirect to Strava OAuth
- `/oauth-callback` → Handle callback, redirect
- `/logout` → Clear session, redirect
- `/strava-setup` → `strava_setup.html`

#### Main App Routes (3)
- `/dashboard` → `build/index.html` (React SPA)
- `/dashboard/first-time` → `onboarding.html`
- `/<path:path>` → `build/index.html` (React Router catch-all)

#### Onboarding Flow (2)
- `/welcome-post-strava` → `welcome_post_strava.html`
- `/goals-setup` → `goals_setup.html`

#### Settings Pages (5)
- `/settings/profile` → `settings_profile.html`
- `/settings/hrzones` → `settings_hrzones.html`
- `/settings/training` → `settings_training.html`
- `/settings/coaching` → `settings_coaching.html`
- `/settings/acwr` → `settings_acwr.html`

#### Admin Routes (10)
- `/admin/trimp-settings` → `admin_trimp_settings.html`
- `/admin/acwr-feature-flags` → `admin_acwr_feature_flags.html`
- `/admin/acwr-configuration` → `admin_acwr_configuration.html`
- `/admin/migration/` → `migration_dashboard.html`
- `/admin/migration/create` → `create_migration.html`
- `/admin/migration/monitor/<id>` → `monitor_migration.html`
- `/admin/migration/history` → `migration_history.html`
- `/admin/migration/alerts` → `migration_alerts.html`
- `/acwr-visualization` → `acwr_visualization_dashboard.html`
- `/admin/migration/elevation` → Inline HTML

### API-Only Routes (211+ endpoints)

**Categories:**
- Training data & stats (10+ endpoints)
- Journal (3 endpoints)
- LLM recommendations (2 endpoints)
- User management (10+ endpoints)
- Settings API (15+ endpoints)
- Strava sync (10+ endpoints)
- Activities management (3 endpoints)
- Coaching features (15+ endpoints)
- Analytics & tutorials (20+ endpoints)
- Legal API (3 endpoints)
- Signup/Registration API (15+ endpoints)
- Feedback (2 endpoints)
- Admin API (50+ endpoints)
- ACWR Admin Blueprints (40+ endpoints)
- Cron jobs (4 endpoints)

---

## Static Assets

### Templates (39 files, 31,061 lines)

**Location:** `app/templates/`

**By Category:**
- Public/Marketing: 7 templates
- Legal: 3 templates
- Authentication: 3 templates
- Onboarding: 3 templates
- Settings: 5 templates
- Admin: 9 templates
- ACWR Admin: 9 templates
- Error: 1 template
- React SPA: 1 file (build/index.html)

### CSS Stylesheets (4 files, 2,989 lines)

**Location:** `app/static/`

- style.css
- dashboard.css
- [2 additional CSS files]

### JavaScript (32 files, 1,197 lines)

**Location:** `app/static/`

- dashboard.js
- settings.js
- [30 additional JS files]

### Images (23 files)

**Location:** `app/static/images/`

**Logo Assets:**
- YTM_Logo_byandfor.webp (main logo, 75 KB)
- YTM_Logo_byandfor_110.webp (small, 109 KB)
- YTM_Logo_byandfor_300.webp (medium, 107 KB)
- YTM_Logo_cropped.webp (92 KB)

**Watercolor Assets:**
- YTM_waterColor_patch800x800.webp (117 KB)
- YTM_waterColor_patch800x800_clean.webp (167 KB)
- YTM_waterColor_patch800x800_transparentBackground.png (1 MB)
- YTM_waterColor_patch10x10.jpg (4.5 KB)

**Background/UI Assets:**
- compass-bg.png (260 KB)
- monkey-fg.png (188 KB)
- overtraining-risk-chart.png (155 KB)

**Strava Branding:**
- Located in app/Strava_brand/

---

## Data Dependencies

### Training Metrics Reference Guide

**File:** `app/Training_Metrics_Reference_Guide.md`
**Size:** 410 lines
**Critical Dependency:** YES

**Used By:**
- `llm_recommendations_module.py` - Loaded at runtime via `load_training_guide()`
- Included in LLM prompts for daily recommendations
- Contains Decision Framework and metrics definitions
- Required for proper AI coaching functionality

**Path:** Must remain in `app/` directory (runtime dependency, not just documentation)

**Purpose:**
- Provides training metrics definitions
- Decision framework for recommendations
- Optimal ranges and pattern recognition guidelines
- Classification terminology

---

## Complete Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│ TIER 0: Root Application (1 file, 12,438 lines)                         │
│ └─ strava_app.py [12,438 lines]                                          │
│    ├─ Defines 250+ routes (39 HTML, 211+ JSON)                          │
│    ├─ Registers 3 Blueprints (ACWR admin - migration disabled)          │
│    └─ Serves React SPA at /dashboard                                    │
└──────────────────────────────────────────────────────────────────────────┘
                         │
      ┌──────────────────┴─────────────────┬──────────────────────────┐
      ▼                                    ▼                          ▼
┌──────────────────────┐   ┌─────────────────────────┐   ┌──────────────────┐
│ TIER 1A: Python Code │   │ TIER 1B: Static Assets  │   │ TIER 1C: Data    │
│ (21 files, 12,630)   │   │ (98 files, 35,247)      │   │ Assets (1 file)  │
├──────────────────────┤   ├─────────────────────────┤   ├──────────────────┤
│ Core Services:       │   │ Templates (39 files):   │   │ Training Guide:  │
│ ├─ llm_recs [2,294]──┼───┼─ 31,061 lines          │   │ └─ Training_     │
│ │                    │   │   ├─ Public (7)         │   │    Metrics_      │
│ ├─ strava_load       │   │   ├─ Auth (3)           │   │    Reference_    │
│ │  [2,034]           │   │   ├─ Onboarding (3)     │   │    Guide.md      │
│ ├─ db_utils [1,145]  │   │   ├─ Settings (5)       │   │    [410 lines]   │
│ ├─ enhanced_token    │   │   ├─ Admin (9)          │   │                  │
│ │  [1,138]           │   │   └─ React (1)          │   │ Used by LLM for  │
│ └─ [17 more...]      │   │                         │   │ daily recs       │
│                      │   │ CSS (4 files, 2,989)    │   └──────────────────┘
│ ACWR Blueprints:     │   │ JS (32 files, 1,197)    │
│ ├─ visualization     │   │ Images (23 files)       │
│ ├─ configuration     │   └─────────────────────────┘
│ ├─ migration         │
│ └─ feature_flags     │
└──────────────────────┘
           │
           ▼
┌──────────────────────┐
│ TIER 2: Services     │
│ (6 files, 3,658)     │
├──────────────────────┤
│ ├─ acwr_config_svc   │
│ │  [1,014]           │
│ ├─ acwr_viz_svc      │
│ │  [710]             │
│ ├─ acwr_migration    │
│ │  _svc [694]        │
│ ├─ unified_metrics   │
│ │  [599]             │
│ ├─ acwr_calc [386]   │
│ └─ feature_flag      │
│    _monitor [255]    │
└──────────────────────┘
           │
           ▼
   [No Further Dependencies]
   (Standard library & external packages)
```

---

## Refactoring Opportunities

### 1. Break Up strava_app.py

**Current State:**
- 12,438 lines (43% of Python codebase)
- Handles 250+ routes
- Renders 21 templates
- Manages authentication, settings, onboarding, public pages

**Recommendations:**
- Create Settings Blueprint (5 templates, ~500 lines)
- Create Auth Blueprint (3 templates, ~400 lines)
- Create Public Pages Blueprint (7 templates, ~300 lines)
- Extract onboarding logic (3 templates, ~200 lines)

**Expected Result:**
- strava_app.py reduced to ~11,000 lines
- Better separation of concerns
- Easier maintenance and testing

### 2. Template Ownership

**Current Distribution:**
```
strava_app.py (21 templates)     72%
acwr_migration_admin.py (5)      17%
Other blueprints (3)             11%
```

**Recommendation:**
- Move settings templates to Settings Blueprint
- Move auth templates to Auth Blueprint
- Move public templates to Public Blueprint

**Expected Result:**
```
strava_app.py (~10 templates)    35%
Settings Blueprint (5)           17%
Auth Blueprint (3)               10%
Public Blueprint (7)             24%
ACWR Blueprints (9)              31%
```

### 3. ACWR System Organization

**Current State:**
- Well-separated into 4 blueprints
- 11 total files (7,294 lines)
- Good separation of concerns

**Recommendation:**
- Move ACWR files to `app/acwr/` subdirectory
- Better namespace organization
- Easier to navigate

### 4. Migration System (Disabled)

**Status:** Migration admin blueprint disabled (Dec 2025) - one-time migration complete.

**Files in scripts/migrations/ (no longer needed at runtime):**
- acwr_migration_batch_processor.py
- acwr_migration_monitoring.py
- acwr_migration_progress_tracker.py
- acwr_migration_rollback_executor.py

**Note:** The `/admin/migration/` routes are disabled in strava_app.py. To re-enable, uncomment the `acwr_migration_admin` import and registration.

### 5. React SPA Integration

**Current State:**
- React app built to `build/` directory
- Served via `send_from_directory()`
- Client-side routing handled by React Router

**Recommendation:**
- Document React build process
- Ensure build/ is in .gitignore
- Consider separating React app to its own repository

---

## Architecture Strengths

1. **Shallow Dependency Tree:** Only 2 tiers deep, indicating good modular design
2. **Blueprint Architecture:** ACWR features properly separated into dedicated blueprints
3. **Clear Separation:** No template sharing between modules
4. **API-First:** 211+ JSON endpoints for modern SPA architecture
5. **Comprehensive Testing:** 26 test files in app/tests/

## Architecture Challenges

1. **Large Main File:** strava_app.py at 12,438 lines needs refactoring
2. **Template Ownership:** 72% of templates rendered by single file
3. **Frontend Complexity:** HTML templates (49%) exceed Python code (45%)
4. **Missing Documentation:** Route documentation needs improvement

---

## Maintenance Notes

### Critical Runtime Dependencies

1. **app/Training_Metrics_Reference_Guide.md** - Required by LLM module
2. **app/exponential_decay_engine.py** - Required by ACWR configuration service
3. **app/config.json** - Application configuration
4. **app/Dockerfile.strava** - Docker deployment
5. **build/index.html** - React SPA entry point

### Development Dependencies

Located in `scripts/`:
- `scripts/admin/` - Admin utilities (9 files)
- `scripts/migrations/` - Migration scripts (16 files)
- `scripts/monitoring/` - Monitoring tools (5 files)
- `scripts/processing/` - Data processing (4 files)
- `scripts/dev/` - Development tools (15 files)

### Archived Code

Located in `archive/`:
- `archive/deprecated/` - Superseded code
- `archive/onboarding_system/` - Unused onboarding features
- `archive/oauth_prototypes/` - OAuth experiments

**Note:** Do NOT move `exponential_decay_engine.py` to archive - it is a runtime dependency.

---

## Version History

- **v1.0** (2025-12-07): Initial architecture documentation
  - Complete dependency tree mapping
  - Route-to-template analysis
  - Static asset inventory
  - Refactoring recommendations

---

## Related Documentation

- `docs/reference/` - Reference documentation
- `docs/features/` - Feature documentation
- `docs/deployment/` - Deployment guides
- `docs/database/` - Database documentation
- `docs/branding/` - Branding guidelines

---

**End of Document**
