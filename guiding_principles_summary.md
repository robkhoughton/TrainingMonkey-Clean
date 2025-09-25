# TrainingMonkey Development Guiding Principles

## 🎯 Problem-Solving Approach

### **Root Cause Analysis**
- **Facts First**: Always gather database evidence before making assumptions
- **Systematic Investigation**: Check what's actually happening vs. what should happen
- **Holistic Thinking**: Step back when multiple fixes don't work - missing something fundamental

### **Debugging Strategy**
- **Database Verification**: Check actual data state, not just code logic
- **End-to-End Testing**: Test complete user flows, not just individual components
- **Session vs Database**: Distinguish between session state and persistent data issues

## 🔧 Technical Standards

### **Database Rules (PostgreSQL)**

#### **SQL Syntax Standards**
- **Placeholders**: Use `%s` (NOT `?`) for all parameter binding
- **Primary Keys**: Use `SERIAL PRIMARY KEY` (NOT `INTEGER PRIMARY KEY AUTOINCREMENT`)
- **Timestamps**: Use `NOW()` (NOT `CURRENT_TIMESTAMP`)
- **Data Types**: Use PostgreSQL types only:
  - `VARCHAR(n)` for limited strings
  - `JSONB` for JSON data
  - `TIMESTAMP` for datetime fields
  - `DATE` for date-only fields

#### **Schema Management**
- **Schema Changes**: Use SQL Editor ONLY, never in code
- **One-time Operations**: SQL Editor for table creation, column additions, indexes
- **Runtime Validation**: Code can check if columns exist during startup
- **Documentation**: All schema changes must be documented

#### **Database Connection**
- **Local Development**: Connect directly to cloud PostgreSQL
- **No Local Database**: Do not create local SQLite or PostgreSQL instances
- **Testing**: Defer database-dependent tests to post-deployment
- **Environment**: Use `DATABASE_URL` in `.env` file

#### **Date and Time Handling**
- **Date-only Operations**: Use `datetime.now().date()` (NOT `datetime.now()`)
- **Database Queries**: Use `date = %s` for DATE column comparisons
- **API Format**: All dates in `'YYYY-MM-DD'` format
- **Parameter Binding**: Pass date objects or YYYY-MM-DD strings directly
- **Timezone Handling**: Use UTC for storage, convert for display
- **Robust Conversion**: Handle all date object types in conversion functions

#### **Timezone Management Standards**
- **Storage**: Always store timestamps in UTC in database
- **Application Logic**: Use `get_app_current_date()` for consistent date handling
- **User Display**: Convert to user's timezone for display only
- **API Consistency**: All date APIs return `'YYYY-MM-DD'` format
- **Debugging**: Use `log_timezone_debug()` for timezone-related issues
- **Configuration**: Set `APP_TIMEZONE` for application-wide timezone handling

### **SQL Syntax Validation**

#### **Common SQLite Syntax Issues to Avoid**
- ❌ Using `?` placeholders instead of `%s`
- ❌ Using `INTEGER PRIMARY KEY AUTOINCREMENT` instead of `SERIAL PRIMARY KEY`
- ❌ Using `CURRENT_TIMESTAMP` instead of `NOW()`
- ❌ Using `date::text` casting in queries
- ❌ Inconsistent date formats in API responses

#### **Validation Process**
- **Pre-commit Validation**: Run `validate_sql_syntax.py` before commits
- **Systematic Review**: Check all SQL queries for PostgreSQL compatibility
- **Testing**: Verify queries work against live cloud database
- **Documentation**: Update schema documentation for any changes

### **Code Quality**
- **Public APIs**: Use intended public methods, avoid private method calls
- **Error Handling**: Fail gracefully, provide meaningful error messages
- **Transaction Management**: Explicit commits, proper connection handling
- **Performance**: Batch database operations when possible
- **SQL Injection Prevention**: Always use parameterized queries
- **Connection Management**: Use context managers for database connections

## 🚀 Development Workflow

### **Issue Resolution**
1. **Reproduce** the issue reliably
2. **Investigate** database state and logs
3. **Identify** root cause (not just symptoms)
4. **Fix** systematically with proper testing
5. **Verify** end-to-end functionality
6. **Clean up** debugging artifacts

### **Code Changes**
- **Architecture Respect**: Use proper class methods and APIs
- **Session Management**: Handle Flask session scope limitations
- **Background Processes**: Avoid session access in background threads
- **Legal Compliance**: Maintain audit trails, optimize for performance

## 📋 Quality Assurance

### **Testing Approach**
- **Database State**: Verify all expected fields are updated
- **User Experience**: Test complete signup flow end-to-end
- **Error Scenarios**: Test validation and error handling
- **Performance**: Ensure operations complete in reasonable time

### **Maintenance**
- **Clean Codebase**: Remove debugging artifacts and temporary bypasses
- **Proper Validation**: Restore production-ready validation logic
- **Documentation**: Keep principles and lessons learned accessible
- **Monitoring**: Verify Cloud Run logs remain clean

## 🎉 Success Criteria

### **New User Signup Flow**
- ✅ OAuth authorization works
- ✅ Form submission saves all data
- ✅ Onboarding completes properly
- ✅ User redirected to dashboard
- ✅ No timeouts or hanging
- ✅ Clean error handling

### **Data Integrity**
- ✅ All profile fields populated
- ✅ Legal compliance logged
- ✅ Onboarding flags set correctly
- ✅ Account status updated
- ✅ Strava integration working

---

**Key Lesson**: When multiple targeted fixes don't work, step back and examine the fundamental architecture and data flow. Often the issue is using the wrong API or method, not a complex logic problem.
