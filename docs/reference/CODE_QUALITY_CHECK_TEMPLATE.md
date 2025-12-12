# Code Quality Check Template

Use these standard phrases when requesting comprehensive quality control checks from your AI coding assistant.

---

## 🔍 **STANDARD QC REQUEST TEMPLATE**

### For New Feature/Function Implementation

> "Please perform a comprehensive quality control check on the [FEATURE/FUNCTION NAME] implementation. Specifically:
> 
> 1. **Conflict Analysis**: Search the codebase for any existing functions that may conflict with, duplicate, or bypass the new logic
> 2. **Integration Points**: Identify all places where similar operations are performed
> 3. **Alternative Paths**: Check for any alternative code paths that might circumvent the new implementation
> 4. **Database Operations**: Verify all database queries follow the same pattern and constraints
> 5. **Consistency Check**: Ensure the implementation is consistent with project standards and patterns
> 
> Please provide:
> - A list of all potential conflicts found
> - Severity rating (CRITICAL/HIGH/MEDIUM/LOW) for each issue
> - Whether each conflicting function is actively used
> - Specific recommendations to resolve conflicts"

---

## 📋 **SPECIFIC QC CHECKS**

### 1. Function Duplication Check
```
"Search the codebase for any functions with similar names or purposes to [FUNCTION_NAME]. 
Check if they perform overlapping operations or could interfere with each other."
```

### 2. Database Operation Audit
```
"Audit all database operations related to [TABLE_NAME]. 
Find all INSERT, UPDATE, DELETE, and SELECT queries.
Verify they all follow the same constraints and use consistent field names."
```

### 3. Bypass Detection
```
"Check for any code paths that might bypass [FEATURE_NAME].
Look for direct database calls, alternative API endpoints, or legacy functions 
that perform similar operations without going through the new implementation."
```

### 4. Integration Point Analysis
```
"Identify all integration points where [SYSTEM_A] interacts with [SYSTEM_B].
Check if our changes affect all integration points consistently."
```

### 5. Deprecated Function Check
```
"Search for any deprecated or legacy functions that should be updated or removed 
to prevent confusion with the new [FEATURE_NAME] implementation."
```

---

## 🎯 **EXAMPLE QC REQUESTS**

### Example 1: After Implementing a Cache Layer
```
"Please perform a conflict check on the new caching implementation for user sessions.
Search for:
1. Any existing caching mechanisms that might conflict
2. Direct database queries that bypass the cache
3. Functions that modify session data without invalidating the cache
4. Legacy session management code that should be deprecated"
```

### Example 2: After Adding Validation Logic
```
"Check the codebase for validation bypass issues. Specifically:
1. Find all places where [DATA_TYPE] is saved to the database
2. Verify they all go through the new validation function
3. Identify any API endpoints that accept [DATA_TYPE] without validation
4. Check for any admin/internal functions that skip validation"
```

### Example 3: After Database Schema Changes
```
"Audit all code that interacts with the [TABLE_NAME] table:
1. Find all queries using the old field name [OLD_FIELD]
2. Check if migration handles existing data correctly
3. Identify any ORM models that need updating
4. Verify indexes are used consistently in all queries"
```

### Example 4: After Implementing Access Control
```
"Perform security audit on the new access control for [FEATURE_NAME]:
1. Find all API endpoints that access this feature
2. Verify they all check permissions consistently  
3. Look for any direct function calls that bypass permission checks
4. Check for any legacy admin bypasses that should be removed"
```

---

## 🔧 **POST-QC ACTION TEMPLATE**

After receiving the QC report, use this template to request fixes:

```
"Based on the QC findings, please fix all CRITICAL and HIGH severity issues:

1. [ISSUE_1]: [Brief description]
   - Apply fix: [Specific action]
   
2. [ISSUE_2]: [Brief description]
   - Apply fix: [Specific action]

For MEDIUM severity issues, please:
- Add deprecation warnings
- Document the issue for future refactoring

For LOW severity issues:
- Document only, no code changes needed

Please apply fixes and verify no new linter errors are introduced."
```

---

## 📊 **QC REPORT EXPECTATIONS**

A good QC report should include:

### 1. **Findings Table**
| Function/File | Location | Issue | Severity | Active? |
|---------------|----------|-------|----------|---------|
| `function_name` | file.py:123 | Description | HIGH | ✅ Yes |

### 2. **Impact Analysis**
- What happens if the conflict is not resolved?
- Which features are affected?
- Risk of data corruption or inconsistency?

### 3. **Actionable Recommendations**
- Specific code changes needed
- Priority/order of fixes
- Testing recommendations

### 4. **Dependencies**
- Does fixing Issue A require fixing Issue B first?
- Are there any breaking changes?

---

## 🚨 **RED FLAGS TO CHECK FOR**

When requesting QC, specifically ask to check for these common issues:

1. **Direct Database Bypass**
   - Functions that use `execute_query()` directly instead of going through service layers
   - Raw SQL queries that don't use helper functions

2. **Inconsistent Field Usage**
   - Some code uses `field_old`, other code uses `field_new`
   - Mixed date formats (text vs. DATE type)

3. **Missing Validation**
   - Some entry points validate input, others don't
   - Admin endpoints that skip validation

4. **Incomplete Migrations**
   - New field added but not populated in existing records
   - Old field deprecated but still referenced in multiple places

5. **Race Conditions**
   - Multiple functions modifying the same data without coordination
   - No locking or transaction management

6. **Orphaned Functions**
   - Old implementations that are no longer called but not removed
   - Functions marked "TODO: Remove" but still in production

7. **Inconsistent Error Handling**
   - Some functions raise exceptions, others return None
   - Mixed error message formats

---

## 💡 **BEST PRACTICES**

1. **Request QC Immediately After**: 
   - Implementing new core functionality
   - Modifying critical data paths
   - Adding validation or security layers
   - Database schema changes

2. **Be Specific About Scope**:
   - Bad: "Check for issues"
   - Good: "Check all functions that save recommendations to ensure they validate target_date"

3. **Request Severity Ratings**:
   - Helps prioritize fixes
   - CRITICAL = Data corruption / Security risk
   - HIGH = Functionality broken / Bypass exists  
   - MEDIUM = Inconsistency / Deprecation needed
   - LOW = Code cleanup / Documentation

4. **Ask for Active Usage Status**:
   - Is the conflicting function actually being called?
   - Can it be safely deprecated?
   - Is it part of a cron job or background task?

5. **Follow Up with Fixes**:
   - Don't just identify issues—fix them
   - Verify fixes don't introduce new issues
   - Run linters after all changes

---

## 📝 **QUICK REFERENCE**

**Basic QC Request:**
```
"Double check the codebase to verify that there are no conflicting functions 
that may interfere with or duplicate [FEATURE_NAME] functionality."
```

**Comprehensive QC Request:**
```
"Perform a comprehensive conflict analysis for [FEATURE_NAME]:
1. Find all similar/duplicate functions
2. Identify database operation bypasses  
3. Check for inconsistent implementations
4. Rate severity of each issue
5. Provide specific fix recommendations"
```

**Post-Implementation Verification:**
```
"Verify the [FEATURE_NAME] implementation is complete and consistent:
1. All entry points use the new logic
2. No legacy code bypasses the implementation  
3. Database constraints are enforced everywhere
4. Error handling is consistent
5. Logging is adequate for debugging"
```

---

## 🎓 **LESSONS LEARNED**

Based on the TrainingMonkey recommendation date confusion issue, always check:

1. ✅ **Multiple Save Paths**: Are there multiple functions that save the same type of data?
2. ✅ **Constraint Enforcement**: Is the constraint enforced in the database AND in all application code?
3. ✅ **Legacy Functions**: Are there old implementations that should be deprecated?
4. ✅ **Cron Jobs**: Do background tasks bypass the new logic?
5. ✅ **Missing Fields**: Does the new logic add required fields that old code doesn't populate?

---

**Remember**: Quality control is not just about finding bugs—it's about ensuring **consistency, completeness, and maintainability** across the entire codebase.

