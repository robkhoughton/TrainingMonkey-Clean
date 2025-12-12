# TrainingMonkey Architecture - Quick Reference

**Last Updated:** 2025-12-07

---

## 📊 Application at a Glance

```
TrainingMonkey Flask Application
├─ 127 total files
├─ 64,383 lines of code
├─ 250+ routes (39 HTML, 211+ JSON)
└─ 3 registered Blueprints (migration admin disabled)
```

---

## 🏗️ Architecture Layers

```
┌────────────────────────────────────────────────────┐
│ Layer 1: Web Interface                             │
│ ├─ 39 HTML templates (31,061 lines)               │
│ ├─ React SPA for /dashboard                       │
│ └─ 250+ Flask routes                               │
└────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────┐
│ Layer 2: Application Logic                         │
│ ├─ strava_app.py (12,438 lines)                   │
│ ├─ 21 direct dependencies (12,630 lines)          │
│ └─ 4 ACWR Blueprints                               │
└────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────┐
│ Layer 3: Services                                   │
│ ├─ LLM Recommendations (2,294 lines)              │
│ ├─ Strava Integration (2,034 lines)               │
│ ├─ ACWR Services (6 files, 3,658 lines)           │
│ └─ Database Utils (1,145 lines)                    │
└────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────┐
│ Layer 4: Data & External Services                  │
│ ├─ PostgreSQL Database                             │
│ ├─ Strava API                                      │
│ ├─ Claude AI API                                   │
│ └─ Training Metrics Guide (410 lines)             │
└────────────────────────────────────────────────────┘
```

---

## 📁 Directory Structure

```
TrainingMonkey-Clean/
├─ app/                          # Core application (42 Python files)
│  ├─ strava_app.py              # Main Flask app (12,438 lines)
│  ├─ llm_recommendations_module.py  # AI coaching (2,294 lines)
│  ├─ strava_training_load.py    # Strava integration (2,034 lines)
│  ├─ acwr_*.py                  # ACWR system (11 files)
│  ├─ templates/                 # HTML templates (39 files)
│  ├─ static/                    # CSS, JS, images
│  ├─ tests/                     # Unit tests (26 files)
│  ├─ utils/                     # Utility modules (5 files)
│  └─ Training_Metrics_Reference_Guide.md  # LLM training data
│
├─ scripts/                      # Development tools
│  ├─ admin/                     # Admin scripts (9 files)
│  ├─ migrations/                # DB migrations (16 files)
│  ├─ monitoring/                # Monitoring tools (5 files)
│  ├─ processing/                # Data processing (4 files)
│  ├─ dev/                       # Dev utilities (15 files)
│  ├─ testing/                   # Test scripts (4 files)
│  ├─ utils/                     # Utility scripts (13 files)
│  └─ deployment/                # Deploy scripts
│
├─ docs/                         # Documentation
│  ├─ APPLICATION_ARCHITECTURE.md  # Complete architecture doc
│  ├─ features/                  # Feature docs (41 files)
│  ├─ deployment/                # Deployment guides (23 files)
│  ├─ database/                  # DB documentation (16 files)
│  ├─ branding/                  # Branding guides (5 files)
│  └─ reference/                 # Reference docs (5 files)
│
├─ archive/                      # Historical/deprecated code
│  ├─ deprecated/                # Superseded files
│  ├─ onboarding_system/         # Unused onboarding features
│  ├─ oauth_prototypes/          # OAuth experiments
│  └─ old_docs/                  # Historical documentation
│
├─ sql/                          # SQL schemas (41 files)
├─ templates/                    # Template files (3 files)
└─ frontend/                     # React application source
```

---

## 🔗 Key Dependencies

### Python Code Dependencies

```
strava_app.py [12,438]
├─ llm_recommendations_module.py [2,294]
│  ├─ unified_metrics_service.py [599]
│  └─ Training_Metrics_Reference_Guide.md [410] ★ Critical
├─ strava_training_load.py [2,034]
│  ├─ acwr_calculation_service.py [386]
│  ├─ timezone_utils.py [190]
│  └─ utils/feature_flags.py [110]
├─ db_utils.py [1,145]
├─ enhanced_token_management.py [1,138]
└─ [17 more dependencies...]
```

### Template Dependencies

```
strava_app.py renders:
├─ Public: landing.html, guide.html, faq.html, tutorials.html (7 total)
├─ Auth: login.html, signup.html, strava_setup.html (3 total)
├─ Settings: settings_*.html (5 total)
├─ Onboarding: onboarding.html, welcome_post_strava.html (3 total)
└─ React SPA: build/index.html

ACWR Blueprints render:
├─ acwr_configuration_admin.py → 1 config template
├─ acwr_feature_flag_admin.py → 1 flag template
├─ acwr_visualization_routes.py → 1 viz template
└─ (acwr_migration_admin.py disabled - migration complete)
```

---

## 🎯 Key Routes

### Public Routes
- `/` → Landing page
- `/guide` → Training guide
- `/faq` → FAQ page
- `/tutorials` → Tutorials

### Authentication
- `/login` → Login page
- `/signup` → Sign up
- `/auth/strava` → Strava OAuth
- `/oauth-callback` → OAuth handler

### Main Application
- `/dashboard` → React SPA (main app interface)
- `/settings/*` → Settings pages
- `/admin/*` → Admin interfaces

### API Endpoints
- `/api/training-data` → Training metrics
- `/api/llm-recommendations` → AI coaching
- `/api/journal` → Journal entries
- `/api/coach/*` → Coaching features
- [200+ more JSON endpoints]

---

## 📈 Statistics

| Metric | Count | Lines |
|--------|-------|-------|
| Python files (app/) | 42 | 28,726 |
| HTML templates | 39 | 31,061 |
| JavaScript files | 32 | 1,197 |
| CSS files | 4 | 2,989 |
| Images | 23 | - |
| Total routes | 250+ | - |
| Blueprints | 4 | - |

---

## 🔍 Quick Lookup

### Find Code Related To:

**Training Recommendations:**
- `app/llm_recommendations_module.py`
- `app/coach_recommendations.py`
- `app/Training_Metrics_Reference_Guide.md`

**Strava Integration:**
- `app/strava_training_load.py`
- `app/enhanced_token_management.py`
- `app/sync_fix.py`

**ACWR System:**
- `app/acwr_calculation_service.py`
- `app/acwr_configuration_service.py` → depends on `exponential_decay_engine.py`
- `app/exponential_decay_engine.py` ★ Critical runtime dependency
- `app/acwr_visualization_routes.py`
- `app/acwr_configuration_admin.py`
- `app/acwr_feature_flag_admin.py`
- ~~`app/acwr_migration_admin.py`~~ (disabled - migration complete)

**Database:**
- `app/db_utils.py`
- `app/db_connection_manager.py`
- `sql/` directory

**Settings:**
- `app/settings_utils.py`
- `app/templates/settings_*.html`

**Authentication:**
- `app/auth.py`
- `app/enhanced_token_management.py`
- `app/templates/login.html`

---

## 🚀 Getting Started

1. **Main application entry:** `app/strava_app.py`
2. **Configuration:** `app/config.json`
3. **Database setup:** `sql/` directory
4. **Run locally:** `scripts/development/run_flask.py`
5. **Tests:** `app/tests/`

---

## 📚 Documentation

For detailed information, see:
- **[APPLICATION_ARCHITECTURE.md](APPLICATION_ARCHITECTURE.md)** - Complete dependency tree and analysis
- `docs/features/` - Feature-specific documentation
- `docs/deployment/` - Deployment guides
- `docs/database/` - Database schemas and migrations

---

## ⚠️ Critical Files

**Do not delete or move:**
1. `app/Training_Metrics_Reference_Guide.md` - Required by LLM module at runtime
2. `app/exponential_decay_engine.py` - Required by ACWR configuration service at runtime
3. `app/config.json` - Application configuration
4. `app/Dockerfile.strava` - Docker deployment
5. `build/index.html` - React SPA entry point

---

## 🔧 Common Tasks

### Add a new route
→ Edit `app/strava_app.py` or create a Blueprint

### Add a new template
→ Create in `app/templates/`, render in appropriate module

### Add a database migration
→ Create script in `scripts/migrations/`

### Add an admin feature
→ Create Blueprint like ACWR admin blueprints

### Modify training recommendations
→ Edit `app/llm_recommendations_module.py` or `Training_Metrics_Reference_Guide.md`

---

**For complete architecture details, see [APPLICATION_ARCHITECTURE.md](APPLICATION_ARCHITECTURE.md)**
