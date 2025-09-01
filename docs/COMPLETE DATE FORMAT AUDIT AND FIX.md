COMPLETE DATE FORMAT AUDIT AND FIX PLAN
# Based on project knowledge analysis, here are all the date format issues to fix:

## CRITICAL ISSUES FOUND:

### 1. LEGACY date::text QUERIES (HIGH PRIORITY)
# These still exist in multiple files and need immediate fixing:

# IN strava_app.py - Multiple instances of date::text patterns:
# FIND AND REPLACE ALL OF THESE:

# OLD (BROKEN):
"SELECT energy_level, rpe_score, pain_percentage, notes FROM journal_entries WHERE user_id = ? AND date::text = ?"

# NEW (FIXED):  
"SELECT energy_level, rpe_score, pain_percentage, notes FROM journal_entries WHERE user_id = ? AND date = ?"

# OLD (BROKEN):
"SELECT autopsy_analysis, alignment_score, generated_at FROM ai_autopsies WHERE user_id = ? AND date::text = ?"

# NEW (FIXED):
"SELECT autopsy_analysis, alignment_score, generated_at FROM ai_autopsies WHERE user_id = ? AND date = ?"

### 2. llm_recommendations_module.py DATE HANDLING
# The safe_date_parse function is incomplete and needs enhancement:

def safe_date_parse(date_input):
    """
    ENHANCED: Safely convert date input to datetime.date object
    Handles strings, date objects, and datetime objects consistently
    """
    if date_input is None:
        return None
    elif isinstance(date_input, date):
        return date_input  # Already a date object
    elif isinstance(date_input, datetime):
        return date_input.date()  # Extract date from datetime
    elif isinstance(date_input, str):
        if 'T' in date_input:
            # ISO format with time: "2025-07-26T00:00:00Z"
            return datetime.fromisoformat(date_input.split('T')[0]).date()
        else:
            # Simple date string: "2025-07-26"
            return datetime.strptime(date_input, '%Y-%m-%d').date()
    else:
        logger.warning(f"Unexpected date input type: {type(date_input)} - {date_input}")
        return None

### 3. INCONSISTENT DATE KEY HANDLING (MEDIUM PRIORITY)
# Create a universal date key normalizer for all lookup dictionaries:

def normalize_date_key_universal(date_key):
    """Universal date key normalizer for consistent lookup across entire application"""
    if date_key is None:
        return None
    elif hasattr(date_key, 'date'):
        # datetime object
        return date_key.date().strftime('%Y-%m-%d')
    elif hasattr(date_key, 'strftime'):
        # date object
        return date_key.strftime('%Y-%m-%d')
    elif isinstance(date_key, str):
        if 'T' in date_key:
            # ISO string: "2025-07-26T00:00:00Z"
            return date_key.split('T')[0]
        else:
            # Already in YYYY-MM-DD format
            return date_key
    else:
        return str(date_key)

### 4. SEARCH PATTERNS TO FIND ALL INSTANCES
# Run these searches in PyCharm to find all occurrences:

SEARCH_PATTERNS = [
    "date::text",           # PostgreSQL text casting
    "DATE(date)",          # MySQL date casting  
    "strftime.*date",      # Date formatting patterns
    "datetime.strptime",   # Date parsing
    "date.strftime",       # Date string conversion
    ".split('T')[0]",      # ISO date extraction
    "isoformat()",         # Date serialization
]

## COMPREHENSIVE FIX STRATEGY:

### PHASE 1: IMMEDIATE CRITICAL FIXES (Deploy Today)

# 1. Replace ALL date::text patterns in strava_app.py
def fix_date_text_queries():
    """
    Search for: date::text = ?
    Replace with: date = ?
    
    Files to check:
    - strava_app.py (confirmed instances)
    - Any other .py files with database queries
    """
    pass

# 2. Add universal date normalizer to utils
def add_universal_date_utils():
    """
    Add to db_utils.py or create date_utils.py:
    - normalize_date_key_universal()
    - safe_date_parse_enhanced()
    - consistent_date_format()
    """
    pass

### PHASE 2: SYSTEMATIC CODEBASE AUDIT (This Week)

# 1. Audit all database queries for date handling
QUERY_AUDIT_CHECKLIST = [
    "âœ“ journal_entries queries - FIXED",
    "âœ“ ai_autopsies queries - FIXED", 
    "â³ activities queries - NEEDS REVIEW",
    "â³ llm_recommendations queries - NEEDS REVIEW",
    "â³ user_settings queries - NEEDS REVIEW",
    "â³ Any JOIN queries with date conditions",
]

# 2. Audit all date-based lookup dictionaries
LOOKUP_AUDIT_CHECKLIST = [
    "âœ“ obs_by_date - FIXED",
    "âœ“ autopsy_by_date - FIXED",
    "â³ recommendations_by_date - NEEDS REVIEW", 
    "â³ activities_by_date - NEEDS REVIEW",
    "â³ Any other date-keyed dictionaries",
]

# 3. Audit date serialization for API responses
API_AUDIT_CHECKLIST = [
    "â³ Journal API responses",
    "â³ Dashboard API responses", 
    "â³ Activity API responses",
    "â³ Recommendation API responses",
    "â³ Any date fields in JSON responses",
]

### PHASE 3: FRONTEND DATE HANDLING (Next Week)

# Check JavaScript date handling issues
FRONTEND_AUDIT_CHECKLIST = [
    "â³ Chart date parsing in React components",
    "â³ Date filtering in dashboard charts", 
    "â³ Timezone handling in journal page",
    "â³ Date display formatting",
    "â³ Date comparison logic",
]

## IMPLEMENTATION PRIORITY:

### HIGH PRIORITY (Fix Today):
1. Replace all date::text queries with date = queries
2. Fix any remaining individual date queries in get_journal_entries
3. Add universal date normalizer function
4. Test journal page functionality

### MEDIUM PRIORITY (This Week):
1. Audit all database query files for date patterns
2. Standardize all date-based lookup dictionaries  
3. Review llm_recommendations_module date handling
4. Check activities-related date queries

### LOW PRIORITY (Next Week):
1. Frontend JavaScript date handling review
2. API response date serialization audit
3. Timezone consistency check across app
4. Performance optimization of date queries

## TESTING STRATEGY:

# Create comprehensive date testing script
def test_date_consistency():
    """
    Test all date-related functionality:
    1. Database queries return expected formats
    2. Lookup dictionaries work correctly
    3. API responses serialize dates properly
    4. Frontend displays dates correctly
    5. Cross-table JOINs work properly
    """
    
    test_cases = [
        "âœ“ Journal observations display",
        "âœ“ Autopsy alignment scores display",
        "â³ Dashboard chart data alignment", 
        "â³ ACWR calculations accuracy",
        "â³ Activity summaries correctness",
        "â³ Recommendation date targeting",
    ]
    
    return test_cases

## EXPECTED BENEFITS:

PERFORMANCE_IMPROVEMENTS = [
    "Faster database queries (no text casting)",
    "Cleaner JOIN operations",
    "Consistent date handling", 
    "Reduced debugging time",
    "Better user experience",
]

RELIABILITY_IMPROVEMENTS = [
    "Eliminate silent date mismatch failures",
    "Consistent data display across app",
    "Accurate cross-table relationships",
    "Reliable date-based filtering",
    "Predictable date serialization",
]