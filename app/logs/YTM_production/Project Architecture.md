# Your Training Monkey - Project Architecture & Implementation Guide

## 🏗️ **System Architecture Overview**

### **Current Production System**
- **Platform**: Multi-user SaaS application deployed on Google Cloud Run
- **Database**: PostgreSQL Cloud SQL with user-isolated data
- **Backend**: Python Flask with Flask-Login authentication
- **Frontend**: React with TypeScript, Recharts for data visualization
- **APIs**: Strava OAuth integration, Anthropic Claude AI recommendations
- **Status**: 95% complete, fully functional with 1 admin user + expanding beta

### **Application Structure**
```
Your Training Monkey (Production SaaS)
├── Authentication Layer (Flask-Login)
├── Tab Navigation System (File Folder Style)
├── Dashboard Tab
│   ├── IntegratedDashboardBanner (Strava sync, branding)
│   └── TrainingLoadDashboard (Analytics, charts, AI recommendations)
├── Activities Tab (NEW - Phase 1 Complete)
│   └── ActivitiesPage (Database management, elevation editing)
├── Journal Tab (Phase 2 - To Be Implemented)
└── Settings Tab (Phase 3 - To Be Implemented)
```

---

## 📋 **Project Scope & Objectives**

### **Primary Goals**
1. **Journal System**: Daily training diary with AI-powered analysis
2. **Activities Management**: Database view with missing data completion
3. **Enhanced Navigation**: Professional file folder tab system
4. **Data Consistency**: Single source of truth across all views

### **Key Requirements**
- **Multi-user support**: All features must filter by `user_id`
- **Strava compliance**: Proper branding and "View on Strava" links
- **Data integrity**: Same data source for charts and tables
- **Professional UX**: Clean, intuitive interface design
- **Production quality**: Error handling, logging, security

---

## ✅ **Completed Work (Phase 1)**

### **Architecture & Navigation**
- ✅ **Tab system implemented** in `App.tsx` with file folder styling
- ✅ **State management** for tab switching with persistence
- ✅ **Responsive design** maintaining mobile compatibility

### **Activities Page**
- ✅ **Data endpoint**: `/api/activities-management` using same data as dashboard
- ✅ **Database consistency**: Uses `/api/training-data` for data source alignment
- ✅ **Elevation editing**: `/api/activities-management/update-elevation` with validation
- ✅ **Sorting & pagination**: Professional table with user controls
- ✅ **Strava branding**: Compliant "POWERED BY STRAVA" footer
- ✅ **User edit tracking**: Clear notation for modified data
- ✅ **Rest day inclusion**: Same data set as dashboard charts

### **Database Schema**
- ✅ **User isolation**: All queries filter by `current_user.id`
- ✅ **Data validation**: Elevation constraints (0-15000ft) with user feedback
- ✅ **Multi-user support**: Existing schema supports all planned features

### **Production Deployment**
- ✅ **Cloud Run integration**: New endpoints deployed and tested
- ✅ **Error handling**: Comprehensive logging and user feedback
- ✅ **Security**: All endpoints require authentication and user validation

---

## 🚧 **Remaining Work - Detailed Implementation Guide**

## **Phase 2: Journal Page Implementation (Estimated: 2-3 weeks)**

### **2.1 Database Schema Updates**
**File**: Database migration script
```sql
-- Create journal_entries table
CREATE TABLE journal_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id) NOT NULL,
    date DATE NOT NULL,
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 5),
    rpe_score INTEGER CHECK (rpe_score >= 1 AND rpe_score <= 10),
    pain_percentage INTEGER CHECK (pain_percentage IN (0, 20, 40, 60, 80, 100)),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Create ai_autopsies table
CREATE TABLE ai_autopsies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id) NOT NULL,
    date DATE NOT NULL,
    prescribed_action TEXT, -- Today's Decision from recommendations
    actual_activities TEXT, -- Summary of what user actually did
    autopsy_analysis TEXT, -- AI-generated analysis
    alignment_score INTEGER CHECK (alignment_score >= 1 AND alignment_score <= 10),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);
```

### **2.2 Backend API Endpoints**
**File**: `strava_app.py` - Add these endpoints

#### **Journal Data Management**
```python
@login_required
@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    """Get journal entries for rolling 7-day view with navigation"""
    # Parameters: ?date=YYYY-MM-DD (optional, defaults to today)
    # Returns: 7 days of journal data centered on requested date
    # Include: journal observations, activity summaries, AI decisions, autopsies

@login_required
@app.route('/api/journal', methods=['POST'])
def save_journal_entry():
    """Save or update journal observations for a specific date"""
    # Body: {date, energy_level, rpe_score, pain_percentage, notes}
    # Validation: Check date belongs to user, validate ranges
    # Return: Success/error with updated entry

@login_required
@app.route('/api/journal/activity-summary/<date>', methods=['GET'])
def get_activity_summary():
    """Generate activity summary for journal display"""
    # Process: Query activities for date, analyze HR zones, classify workout
    # Return: {type, distance, elevation, workout_classification, hr_analysis}
```

#### **AI Autopsy System**
```python
@login_required
@app.route('/api/journal/generate-autopsy', methods=['POST'])
def generate_ai_autopsy():
    """Generate AI autopsy comparing prescription vs actual activity"""
    # Body: {date}
    # Process: 
    #   1. Get Today's Decision for that date
    #   2. Get actual activities performed
    #   3. Get user observations (energy, RPE, pain)
    #   4. Call Claude API with comparison prompt
    #   5. Save autopsy to database
    # Return: Generated autopsy text
```

### **2.3 Frontend Components**
**File**: `src/JournalPage.tsx`

#### **Component Structure**
```typescript
interface JournalEntry {
  date: string;
  todaysDecision: string;        // From LLM recommendations
  activitySummary: ActivitySummary;
  observations: UserObservations;
  aiAutopsy: string | null;
}

interface ActivitySummary {
  type: string;
  distance: number;
  elevation: number;
  workoutClassification: 'easy' | 'moderate' | 'tempo' | 'intervals' | 'recovery';
  hrZoneDistribution: number[];
}

interface UserObservations {
  energyLevel: number;    // 1-5 scale
  rpeScore: number;       // 1-10 scale
  painPercentage: number; // 0,20,40,60,80,100
  notes: string;
}
```

#### **Key Features to Implement**
1. **7-day rolling table** with date navigation (< Today >)
2. **Activity summary generation** using HR zone analysis
3. **Dropdown observations** with proper validation
4. **AI autopsy integration** with loading states
5. **Auto-save functionality** for user observations
6. **Mobile-responsive design** matching existing dashboard

### **2.4 AI Integration Enhancement**
**File**: `llm_recommendations_module.py` - Extend for autopsy generation

#### **New Function: Generate Autopsy**
```python
def generate_activity_autopsy(user_id, date, prescribed_action, actual_activities, observations):
    """Generate AI autopsy comparing prescribed vs actual training"""
    # Prompt engineering for post-activity analysis
    # Compare prescription with reality
    # Factor in user observations (energy, RPE, pain)
    # Provide learning insights and future recommendations
    # Return structured autopsy text
```

---

## **Phase 3: Settings & Polish (Estimated: 1 week)**

### **3.1 Settings Page**
**File**: `src/SettingsPage.tsx`
- **User profile management**: HR zones, personal info
- **Journal preferences**: Default views, notification settings
- **Data export options**: CSV download functionality
- **Account settings**: Password change, data management

### **3.2 System Enhancements**
- **Error boundary components**: Graceful error handling
- **Loading state improvements**: Skeleton screens
- **Performance optimization**: Data caching strategies
- **Accessibility compliance**: ARIA labels, keyboard navigation

---

## **Phase 4: Advanced Features (Future)**

### **4.1 Enhanced Analytics**
- **Training plan generation**: AI-powered periodization
- **Comparative analytics**: Peer benchmarking (opt-in)
- **Advanced visualizations**: 3D charts, interactive timelines

### **4.2 Integration Expansions**
- **Garmin Connect**: Additional data source option
- **TrainingPeaks**: Power meter integration
- **Email notifications**: Weekly summaries, alerts

---

## 🛠️ **Implementation Guidelines for Junior Engineers**

### **Development Environment Setup**
1. **Clone repository** and set up local development
2. **Database access**: Request Cloud SQL credentials
3. **API keys**: Ensure Anthropic and Strava keys in environment
4. **Testing**: Use existing user account for development

### **Code Standards**
- **Follow existing patterns**: Study `ActivitiesPage.tsx` and `/api/activities-management`
- **Error handling**: Always include try-catch with user feedback
- **Logging**: Use `logger.info/error` for debugging
- **User isolation**: Every query must filter by `current_user.id`
- **Type safety**: Use TypeScript interfaces for all data structures

### **Testing Checklist**
- [ ] Multi-user data isolation (test with different accounts)
- [ ] Mobile responsiveness (test on various screen sizes)
- [ ] Error states (network failures, invalid data)
- [ ] Loading states (slow API responses)
- [ ] Data consistency (compare with dashboard values)
- [ ] Security (unauthorized access attempts)

### **Deployment Process**
1. **Local testing**: Verify all functionality works locally
2. **Code review**: Submit PR with detailed description
3. **Staging deployment**: Test on Cloud Run staging environment
4. **Production deployment**: Use existing deployment scripts
5. **User acceptance testing**: Verify with beta users

---

## 📊 **Success Metrics**

### **Technical Metrics**
- **Page load times**: < 2 seconds for all pages
- **API response times**: < 500ms for data endpoints
- **Error rates**: < 1% of requests
- **Mobile compatibility**: 100% feature parity

### **User Experience Metrics**
- **Journal completion rate**: > 80% daily entries
- **Data accuracy**: < 5% user corrections needed
- **Feature adoption**: > 60% use of AI autopsy
- **User satisfaction**: > 4.5/5 in feedback surveys

---

## 🔗 **Key Resources**

### **Documentation**
- **Strava API**: Brand guidelines, rate limits
- **Anthropic Claude**: API documentation, best practices
- **Google Cloud**: Deployment guides, monitoring tools

### **Existing Codebase Patterns**
- **Data fetching**: Study `TrainingLoadDashboard.tsx` useEffect patterns
- **API design**: Follow `/api/training-data` and `/api/stats` structure
- **Styling**: Use `TrainingLoadDashboard.module.css` classes
- **Authentication**: Follow `@login_required` decorator pattern

### **External Dependencies**
- **React**: Hooks, TypeScript integration
- **Recharts**: Data visualization library
- **Flask**: Route handling, authentication
- **PostgreSQL**: Multi-user query patterns

This implementation guide provides a complete roadmap for finishing the Your Training Monkey enhancement project while maintaining the high production standards of the existing system.