# Training Monkey Development Guide

## 🎯 Overview

This guide provides essential information for developers working on the Training Monkey project.

## 🗄️ Database Rules

### **CRITICAL: PostgreSQL Only**
This project uses **PostgreSQL exclusively**. SQLite syntax is forbidden.

### Key Rules:
- ✅ Use `%s` placeholders (NOT `?`)
- ✅ Use PostgreSQL data types (SERIAL, VARCHAR, etc.)
- ❌ No SQLite imports or syntax
- ❌ No `AUTOINCREMENT`, `INTEGER PRIMARY KEY`, `REAL` types

### Validation:
```bash
# Run before every commit
python scripts/validate_sql_syntax.py
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL database
- Strava API credentials

### Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables (see `.env.example`)
4. Run database migrations
5. Start the application: `python app/strava_app.py`

## 📁 Project Structure

```
app/                    # Main application code
├── strava_app.py      # Flask application
├── db_utils.py        # Database utilities
├── strava_training_load.py  # TRIMP calculations
└── templates/         # HTML templates

docs/                  # Documentation
├── SQL_SYNTAX_GUIDE.md    # SQL syntax rules
├── PROJECT_RULES_ENFORCEMENT.md  # Enforcement guide
└── DEVELOPMENT_GUIDE.md   # This file

scripts/               # Utility scripts
├── validate_sql_syntax.py  # SQL validation
└── pre-commit-hooks.py     # Pre-commit checks
```

## 🔧 Development Workflow

### Before Committing
1. **Run SQL validation:**
   ```bash
   python scripts/validate_sql_syntax.py
   ```

2. **Run pre-commit checks:**
   ```bash
   python scripts/pre-commit-hooks.py
   ```

3. **Test your changes:**
   - Test database queries
   - Verify API endpoints
   - Check error handling

### Code Review Checklist
- [ ] All SQL uses PostgreSQL syntax
- [ ] No SQLite placeholders (`?`)
- [ ] Proper error handling
- [ ] Logging added where needed
- [ ] Date handling uses `datetime.date`

## 🐛 Common Issues

### SQLite Syntax Errors
**Problem:** Using `?` instead of `%s` in SQL queries
**Solution:** Replace all `?` with `%s` in SQL strings

### Date Format Issues
**Problem:** `datetime.date` object has no attribute 'date'
**Solution:** Don't call `.date()` on objects that are already dates

### Database Connection Issues
**Problem:** Connection errors or timeouts
**Solution:** Check `DATABASE_URL` environment variable

## 📚 Key Documentation

- [SQL Syntax Guide](SQL_SYNTAX_GUIDE.md) - PostgreSQL syntax rules
- [Project Rules Enforcement](PROJECT_RULES_ENFORCEMENT.md) - Enforcement mechanisms
- [Database Rules](DATABASE_RULES_UPDATED.md) - Database-specific rules
- [TRIMP Enhancement Guide](trimp_discrepancy_action_plan.md) - TRIMP calculation details

## 🚨 Emergency Procedures

### If SQLite Syntax is Found
1. **Stop deployment immediately**
2. **Run validation script** to identify all issues
3. **Fix all critical errors** before proceeding
4. **Update validation rules** if needed

### If Database Issues Occur
1. **Check connection string**
2. **Verify database is running**
3. **Check for SQL syntax errors**
4. **Review recent changes**

## 📞 Support

### Getting Help
- **Technical issues:** Check documentation first
- **SQL syntax:** Use validation script and syntax guide
- **Database problems:** Review database rules and connection setup
- **Feature questions:** Check relevant documentation

### Resources
- **Validation Script:** `scripts/validate_sql_syntax.py`
- **Pre-commit Hooks:** `scripts/pre-commit-hooks.py`
- **SQL Guide:** `docs/SQL_SYNTAX_GUIDE.md`
- **Project Rules:** `docs/PROJECT_RULES_ENFORCEMENT.md`

## 🎯 Best Practices

1. **Always validate SQL syntax** before committing
2. **Use PostgreSQL syntax exclusively**
3. **Test database queries** thoroughly
4. **Handle errors gracefully** with proper logging
5. **Follow the established patterns** in the codebase
6. **Document complex logic** with clear comments

Remember: **PostgreSQL syntax is mandatory for this project!**
