# Date Format Standards and Rules

**Last Updated**: 2025-01-10  
**Status**: Active Standards  
**Scope**: All date handling across the application

## 🎯 **Core Principles**

1. **Consistency**: All date operations must use standardized formats
2. **Database Compatibility**: DATE columns require date-only values (no time/timezone)
3. **API Consistency**: All APIs return standardized date strings
4. **Error Prevention**: Robust date conversion prevents silent failures

## 📅 **Date Format Standards**

### **1. Database Operations**

#### **Date Range Queries:**
```python
# ✅ CORRECT: Use date-only objects for DATE column comparisons
from datetime import datetime, timedelta

end_date = datetime.now().date()  # Date only, no time
start_date = end_date - timedelta(days=days_back)

# Database query with proper date parameters
query = """
    SELECT date, trimp FROM activities 
    WHERE user_id = %s AND date >= %s AND date <= %s
"""
result = db_utils.execute_query(query, (user_id, start_date, end_date), fetch=True)
```

#### **Date Column Comparisons:**
```sql
-- ✅ CORRECT: Direct date comparison
SELECT * FROM activities WHERE user_id = ? AND date = ?

-- ❌ WRONG: Text casting (legacy pattern)
SELECT * FROM activities WHERE user_id = ? AND date::text = ?
```

#### **Date Parameter Binding:**
```python
# ✅ CORRECT: Pass date objects directly
db_utils.execute_query(query, (user_id, date_obj), fetch=True)

# ✅ CORRECT: Pass date strings in YYYY-MM-DD format
db_utils.execute_query(query, (user_id, '2025-01-10'), fetch=True)
```

### **2. Date Conversion and Parsing**

#### **Robust Date Conversion (from database results):**
```python
def convert_database_date(row_date):
    """Convert database date result to consistent string format"""
    if hasattr(row_date, 'date'):
        # datetime object - extract date part
        return row_date.date().strftime('%Y-%m-%d')
    elif hasattr(row_date, 'strftime'):
        # date object - format directly
        return row_date.strftime('%Y-%m-%d')
    else:
        # string - use as-is
        return str(row_date)
```

#### **Safe Date Parsing (for user input):**
```python
def safe_date_parse(date_input):
    """
    Safely convert date input to datetime.date object
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
```

### **3. API Response Formatting**

#### **Date Serialization:**
```python
# ✅ CORRECT: Consistent ISO date format for all APIs
def format_api_date(date_obj):
    """Format date for API responses"""
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime('%Y-%m-%d')
    else:
        return str(date_obj)

# API response example
return jsonify({
    'success': True,
    'data': {
        'date': format_api_date(activity_date),
        'value': acwr_value
    },
    'metadata': {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d')
    }
})
```

### **4. Frontend JavaScript**

#### **Date Handling:**
```javascript
// ✅ CORRECT: Consistent date format for API calls
const analysisDate = document.getElementById('sensitivityDate').value || 
                    new Date().toISOString().split('T')[0];

// ✅ CORRECT: Date formatting for display
const formattedDate = new Date(dateString).toLocaleDateString();

// ✅ CORRECT: Date range calculations
const endDate = new Date();
const startDate = new Date(endDate.getTime() - (days * 24 * 60 * 60 * 1000));
```

## 🚫 **Common Mistakes to Avoid**

### **1. Database Query Mistakes:**
```python
# ❌ WRONG: Using datetime with time for DATE columns
end_date = datetime.now()  # Includes time and timezone
start_date = end_date - timedelta(days=days_back)

# ❌ WRONG: Text casting in queries
query = "SELECT * FROM activities WHERE date::text = ?"
```

### **2. Date Conversion Mistakes:**
```python
# ❌ WRONG: Assuming all dates are strings
activity_date = str(row['date'])  # May lose date object benefits

# ❌ WRONG: Inconsistent date parsing
if isinstance(date_input, str):
    return date_input  # Doesn't validate format
```

### **3. API Response Mistakes:**
```python
# ❌ WRONG: Inconsistent date formats
return {
    'date': date_obj.isoformat(),  # May include time
    'other_date': str(date_obj)    # Inconsistent format
}
```

## 🔧 **Implementation Guidelines**

### **1. New Date Operations:**
- Always use `datetime.now().date()` for date-only operations
- Use `safe_date_parse()` for user input validation
- Use `strftime('%Y-%m-%d')` for consistent string formatting
- Handle database date objects with robust conversion logic

### **2. Database Queries:**
- Use `date = ?` for DATE column comparisons
- Pass date objects or YYYY-MM-DD strings as parameters
- Never use `date::text` casting in queries

### **3. API Development:**
- All date fields in responses use `'YYYY-MM-DD'` format
- Include date range metadata in time-series APIs
- Validate date parameters with `safe_date_parse()`

### **4. Frontend Integration:**
- Use `toISOString().split('T')[0]` for date picker values
- Expect `'YYYY-MM-DD'` format from all APIs
- Handle date parsing errors gracefully

## 📊 **Date Format Reference**

| Context | Format | Example | Notes |
|---------|--------|---------|-------|
| Database DATE column | `date` | `2025-01-10` | Date only, no time |
| Database queries | `date = ?` | `date = '2025-01-10'` | Direct comparison |
| API responses | `'YYYY-MM-DD'` | `'2025-01-10'` | ISO date string |
| Frontend JavaScript | `'YYYY-MM-DD'` | `'2025-01-10'` | ISO date string |
| Date calculations | `datetime.date` | `date(2025, 1, 10)` | Python date object |
| User input parsing | `'YYYY-MM-DD'` | `'2025-01-10'` | Validated format |

## 🧪 **Testing Standards**

### **1. Date Conversion Tests:**
```python
def test_date_conversion():
    """Test all date conversion scenarios"""
    test_cases = [
        (datetime(2025, 1, 10, 14, 30), '2025-01-10'),
        (date(2025, 1, 10), '2025-01-10'),
        ('2025-01-10', '2025-01-10'),
        ('2025-01-10T14:30:00Z', '2025-01-10'),
    ]
    
    for input_date, expected in test_cases:
        result = convert_database_date(input_date)
        assert result == expected
```

### **2. Database Query Tests:**
```python
def test_date_queries():
    """Test date range queries work correctly"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    result = db_utils.execute_query(
        "SELECT COUNT(*) FROM activities WHERE date >= %s AND date <= %s",
        (start_date, end_date),
        fetch=True
    )
    assert result is not None
```

### **3. API Response Tests:**
```python
def test_api_date_format():
    """Test API responses use consistent date format"""
    response = client.get('/api/activities?user_id=1')
    data = response.json()
    
    for item in data['activities']:
        assert re.match(r'\d{4}-\d{2}-\d{2}', item['date'])
```

## 📚 **Related Documentation**

- [Database Schema Rules](database_schema_rules.md) - Database management standards
- [Date Format Fixes Implementation](DATE_FORMAT_FIXES_IMPLEMENTED.md) - Historical fixes
- [Complete Date Format Audit](COMPLETE%20DATE%20FORMAT%20AUDIT%20AND%20FIX.md) - Original audit

## 🔄 **Maintenance**

### **Regular Reviews:**
- **Monthly**: Check for new date handling patterns
- **Quarterly**: Review date format consistency across modules
- **Annually**: Update standards based on new requirements

### **Code Review Checklist:**
- [ ] Date operations use `datetime.now().date()` for date-only calculations
- [ ] Database queries use `date = ?` format
- [ ] API responses use `'YYYY-MM-DD'` format
- [ ] Date conversion handles all object types robustly
- [ ] Frontend expects consistent date format from APIs

---

**Enforcement**: All new code must follow these standards. Existing code should be updated during regular maintenance cycles.
