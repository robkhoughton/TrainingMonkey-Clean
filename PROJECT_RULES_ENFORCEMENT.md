# Project Rules Enforcement Guide

## 🎯 Overview

This document outlines how to enforce project rules to prevent violations like SQLite syntax in PostgreSQL projects.

## 📋 Current Project Rules

### Database Rules
- **Database Platform**: PostgreSQL ONLY
- **SQL Syntax**: Use `%s` placeholders (NOT `?`)
- **Data Types**: Use PostgreSQL types (SERIAL, VARCHAR, etc.)
- **No SQLite**: No sqlite3 imports or SQLite-specific syntax

### Code Quality Rules
- **Date Handling**: Use `datetime.date` for date-only operations
- **Error Handling**: Proper exception handling with logging
- **Testing**: Database modifications require manual SQL execution

## 🛡️ Enforcement Mechanisms

### 1. Automated Validation

#### SQL Syntax Validator
```bash
# Run before every commit
python scripts/validate_sql_syntax.py
```

**What it checks:**
- SQLite placeholders (`?`) → PostgreSQL placeholders (`%s`)
- SQLite data types → PostgreSQL equivalents
- SQLite-specific syntax → PostgreSQL equivalents

#### Pre-commit Hooks
```bash
# Run all validation checks
python scripts/pre-commit-hooks.py
```

**What it checks:**
- SQL syntax compliance
- Database rule violations
- Forbidden imports (sqlite3)

### 2. Code Review Checklist

#### Database Code Review
- [ ] All SQL queries use `%s` placeholders
- [ ] No SQLite-specific syntax
- [ ] PostgreSQL data types used
- [ ] No sqlite3 imports
- [ ] Date handling uses `datetime.date`

#### API Code Review
- [ ] Date parameters properly parsed
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Database queries validated

### 3. Testing Requirements

#### Database Testing
- [ ] All SQL queries tested with PostgreSQL
- [ ] Date format handling verified
- [ ] Error scenarios tested
- [ ] Performance validated

#### Integration Testing
- [ ] API endpoints tested
- [ ] Data flow validated
- [ ] Error handling verified

## 🚨 Violation Response

### Immediate Actions
1. **Stop deployment** if critical violations found
2. **Fix violations** before proceeding
3. **Update validation** to catch similar issues
4. **Document lessons learned**

### Prevention Measures
1. **Run validation** before every commit
2. **Code review** all database changes
3. **Test thoroughly** before deployment
4. **Update rules** as needed

## 📊 Monitoring & Metrics

### Track These Metrics
- **Validation failures** per commit
- **Rule violations** by type
- **Time to fix** violations
- **Deployment delays** due to violations

### Success Criteria
- **Zero critical violations** in production
- **< 5 minutes** to fix validation issues
- **100% compliance** with database rules
- **No deployment delays** due to rule violations

## 🔄 Continuous Improvement

### Regular Reviews
- **Monthly**: Review validation rules
- **Quarterly**: Update enforcement mechanisms
- **Annually**: Comprehensive rule audit

### Feedback Loop
- **Collect feedback** from developers
- **Improve validation** based on issues
- **Update documentation** as needed
- **Share lessons learned**

## 🎯 Implementation Plan

### Phase 1: Immediate (This Week)
- [ ] Deploy SQL syntax validator
- [ ] Run validation on existing code
- [ ] Fix all critical violations
- [ ] Document process

### Phase 2: Short-term (Next Month)
- [ ] Implement pre-commit hooks
- [ ] Train team on new process
- [ ] Monitor compliance metrics
- [ ] Refine validation rules

### Phase 3: Long-term (Ongoing)
- [ ] Integrate with CI/CD pipeline
- [ ] Add more validation rules
- [ ] Improve error messages
- [ ] Automate rule updates

## 📞 Support

### Questions or Issues?
- **Technical**: Check validation scripts
- **Process**: Review this document
- **Escalation**: Contact project lead

### Getting Help
- **Documentation**: This guide and related docs
- **SQL Syntax Guide**: `docs/SQL_SYNTAX_GUIDE.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **Scripts**: `scripts/validate_sql_syntax.py`
- **Examples**: See existing compliant code
- **Training**: Request team training session
