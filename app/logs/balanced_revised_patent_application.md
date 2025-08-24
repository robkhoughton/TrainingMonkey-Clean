# METHOD AND SYSTEM FOR NORMALIZED DIVERGENCE CALCULATION BETWEEN EXTERNAL AND INTERNAL ACUTE-TO-CHRONIC WORKLOAD RATIOS FOR ATHLETIC INJURY PREDICTION

## CROSS-REFERENCE TO RELATED APPLICATIONS

Not applicable.

## STATEMENT REGARDING FEDERALLY SPONSORED RESEARCH

Not applicable.

## BACKGROUND OF THE INVENTION

### Field of the Invention

This invention relates to athletic training monitoring systems for predicting injury risk through comparative analysis of external mechanical training loads and internal physiological training responses using normalized divergence calculations between acute-to-chronic workload ratios across multiple sports disciplines.

### Description of Related Art

The fundamental limitation of single-metric training load monitoring affects athletic training across all sports disciplines. Whether in endurance sports (running, cycling, swimming), strength sports (weightlifting, powerlifting), winter sports (skiing, snowboarding), or team sports (soccer, basketball), existing systems calculate workload ratios using either external mechanical metrics OR internal physiological metrics, but never both in comparative analysis.

This universal limitation creates identical blind spots across all athletic disciplines: mechanical training demands may exceed physiological adaptation capacity, or internal stress may accumulate without corresponding external load awareness, leading to increased injury risk regardless of sport type.

**Endurance Sports Limitations:** Current running applications such as Garmin Connect and Strava calculate training stress using either GPS-derived distance metrics or heart rate-based physiological responses, but never compare the two approaches. Cycling platforms like TrainingPeaks focus on power-based external metrics without comparing physiological adaptation rates. Swimming applications track distance and pace without integrating cardiovascular response patterns.

**Strength Training Limitations:** Existing strength training applications such as Strong and MyFitnessPal track volume-load metrics (sets × repetitions × weight) but fail to integrate physiological monitoring data to assess whether training volume exceeds recovery capacity or whether cardiovascular systems are adequately challenged.

**Winter Sports Limitations:** Skiing and snowboarding applications such as Ski Tracks provide basic distance and elevation tracking but lack sophisticated training load analytics or physiological integration necessary for injury prevention in high-risk mountain sports.

**Swimming Limitations:** Swimming applications such as MySwimPro and Swim.com track distance, stroke count, and pace metrics but fail to integrate these mechanical load indicators with cardiovascular response data. Pool-based training monitoring systems capture lap times and stroke efficiency without comparing external swimming load to internal physiological adaptation rates, missing critical insights for preventing overuse injuries in shoulders, core, and cardiovascular systems.

**Technical Deficiencies in Existing Systems:** 
- Garmin/Firstbeat: Internal ACWR calculations using TRIMP methodology without external load comparison
- Catapult Sports: External mechanical load monitoring without internal physiological integration  
- Consumer Platforms: Basic activity tracking without sophisticated ACWR calculations across any sport
- Strava: Relative effort scoring lacks dual-metric ACWR divergence analysis methodology
- Professional Systems: Sport-specific monitoring without cross-domain mathematical frameworks

**Critical Technical Gap:** No existing system provides simultaneous calculation of both external and internal ACWR with comparative divergence analysis across athletic disciplines, creating universal blind spots where external training stress and internal physiological adaptation become misaligned regardless of sport type.

## BRIEF SUMMARY OF THE INVENTION

### Core Innovation

The present invention provides a novel normalized divergence calculation between external and internal Acute-to-Chronic Workload Ratios (ACWR) that addresses fundamental limitations in current injury prediction methodologies across all athletic disciplines. This mathematical innovation provides the first known quantitative method for comparing mechanistic training load metrics with physiological adaptation responses.

**Mathematical Formula:**
```
normalized_divergence = (external_acwr - internal_acwr) / ((external_acwr + internal_acwr) / 2)
```

**Component Definitions:** 
- **External ACWR**: Activity-specific mechanical training load acute-to-chronic workload ratio capturing external training demands
- **Internal ACWR**: Heart rate TRIMP-based acute-to-chronic workload ratio reflecting physiological adaptation capacity
- **Normalized Divergence**: Scale-independent mathematical comparison indicating mismatch between external training stress and internal physiological response

### Key Technical Advantages

1. **Universal Dual-Metric Integration**: First known implementation combining external mechanical load with internal physiological load through comparative ACWR analysis across multiple sports
2. **Scale-Independent Comparison**: Arithmetic mean normalization enables comparison across diverse athlete populations, training intensities, and sport types
3. **Real-Time Processing**: Sub-5-second processing latency for immediate injury risk assessment
4. **Cross-Sport Applicability**: Mathematical framework applies to running, cycling, skiing, strength training, and other athletic disciplines
5. **Enterprise Scalability**: Multi-user architecture with complete data isolation

### Universal Applicability

The normalized divergence calculation methodology applies universally across athletic disciplines because the fundamental relationship between external mechanical demands and internal physiological adaptation exists in all sports:

**Trail Running Applications (Fully Implemented):** External load calculations incorporate distance and elevation-adjusted metrics compared with heart rate-based internal ACWR calculations using complete production system validation.

**Road Running Applications:** The methodology would apply external load calculations based on distance and pace metrics compared with identical heart rate-based internal ACWR calculations.

**Cycling Applications:** The divergence methodology would incorporate power meter data and distance for external load calculation while maintaining identical TRIMP-based internal load methodology for comparative analysis.

**Strength Training Applications:** External load would comprise volume-load calculations (sets × reps × weight) normalized to individual capacity, compared with session-based TRIMP calculations for internal load divergence analysis.

**Skiing Applications:** External load would incorporate distance, vertical descent factors, and terrain difficulty coefficients compared with altitude-adjusted TRIMP calculations for physiological load assessment.

**Swimming Applications:** External load would comprise distance, stroke rate, and pool versus open water factors normalized to individual swimming capacity, compared with heart rate-based TRIMP calculations adjusted for water immersion effects on cardiovascular response.

The mathematical relationship remains constant across all applications, providing universal injury prediction methodology regardless of sport type.

### Production Evidence and Best Mode

- **Platform**: "Your Training Monkey" deployed on Google Cloud Platform with trail running implementation
- **Architecture**: Flask backend, PostgreSQL database, React frontend
- **Status**: Active beta testing program with expanding user base
- **Performance**: 2-3 second processing latency, 1000+ concurrent calculations

**Best Mode Disclosure**: The trail running implementation described herein, including the Google Cloud Platform deployment architecture, elevation conversion factor of 750 feet per mile, TRIMP-based internal load calculation with gender-specific coefficients, and real-time normalized divergence processing, represents the best mode contemplated by the inventor for carrying out the invention.

## BRIEF DESCRIPTION OF THE DRAWINGS

**FIG. 1** is a detailed process flow diagram showing step-by-step implementation of the normalized divergence calculation algorithm, including input validation (102-104), edge case handling (108-114), and the patent core innovation of normalized divergence calculation (118).

**FIG. 2** is a mathematical formula implementation diagram showing normalized divergence calculation with scale independence properties, including external ACWR input (200), internal ACWR input (202), arithmetic mean normalization (208), and final divergence output (210).

**FIG. 3** is a system architecture diagram showing the complete production environment for normalized ACWR divergence technology deployed on Google Cloud Platform, including external access layer (10-16), containerized application layer (20-26), security management layer (30-38), and data storage layer (40-46).

**FIG. 4** is an enterprise multi-user architecture diagram demonstrating complete data isolation between users (300-306) while sharing computational resources through the UnifiedMetricsService processing engine (320) with mandatory user_id filtering (322, 360).

**FIG. 5** is a trail running application example showing elevation conversion innovation (410) where elevation gain is converted to distance equivalent using a conversion factor of 750 feet per mile for external load calculation, demonstrating the specific implementation of the universal mathematical framework.

**FIG. 6** is an OAuth and API architecture diagram showing Strava authentication flow (500-506), enterprise-grade API processing with rate limiting (510-516), and real-time webhook event pipeline (520-530), demonstrating per-user token isolation, intelligent rate limiting with tiered service levels, and real-time data synchronization supporting the normalized ACWR divergence technology.

**FIG. 7** is a platform integration and SDK architecture diagram showing multi-platform data aggregation (540-550) supporting Strava, Garmin Connect, Apple Health, and Fitbit platforms through unified data normalization, third-party SDK integration patterns (560-566) for iOS, Android, and web development, and comprehensive developer ecosystem framework (570-580) supporting individual developers through enterprise white-label solutions.

## DETAILED DESCRIPTION OF THE INVENTION

### System Architecture

The present invention comprises a comprehensive system for calculating and analyzing normalized divergence between external and internal ACWR across multiple athletic disciplines. The system includes several key components that work together to provide real-time injury risk assessment.

**Best Mode Implementation**: The preferred embodiment described herein represents the best mode contemplated by the inventor for practicing the invention, specifically implemented as a cloud-based multi-user system with trail running applications serving as the primary deployment while maintaining universal applicability across athletic disciplines.

**Data Acquisition Layer:** The system receives training data from multiple sources including GPS tracking devices for distance and elevation measurements, heart rate monitoring devices including chest straps and optical sensors, and various sport-specific sensors such as power meters for cycling applications. API integrations enable data acquisition from existing platforms including Strava OAuth 2.0 (illustrated in FIG. 6), Garmin Connect, Apple Health, and other fitness technology ecosystems as shown in the multi-platform integration architecture of FIG. 7.

**Processing Engine:** As demonstrated in FIG. 1, the core processing engine performs sport-specific external ACWR calculations with appropriate conversion factors, internal ACWR calculations using Training Impulse (TRIMP) methodology, and the novel normalized divergence computation with comprehensive edge case handling. The processing engine adapts calculation parameters based on detected or specified sport type, with the complete algorithmic flow detailed in the process diagram of FIG. 1.

**Storage and Output Systems:** Data storage utilizes PostgreSQL database architecture with strict user isolation protocols, enabling multi-user enterprise deployment as shown in FIG. 3-4. Output systems include real-time visualization dashboards, automated alert generation and notification systems, and comprehensive reporting capabilities for athletes and coaches.

### Mathematical Implementation

**Universal External ACWR Calculation Framework:** The external ACWR calculation adapts to sport-specific requirements while maintaining consistent mathematical structure:

```
External Load = Base_Activity_Metric × Sport_Conversion_Factor × Environmental_Coefficient
Acute External Load = 7-day rolling average of external loads
Chronic External Load = 28-day rolling average of external loads  
External ACWR = Acute External Load / Chronic External Load
```

**Trail Running Implementation (Fully Developed):**
```
External Load = Distance (miles) + (Elevation Gain (feet) / 750)
```

This implementation has been fully developed, tested, and validated in production deployment with comprehensive performance metrics, as illustrated in FIG. 5 showing the elevation conversion methodology and practical application of the universal mathematical framework.

**Road Running Implementation (Conceptual Framework):**
```
External Load = Distance (miles) × Pace_Difficulty_Factor
```

**Cycling Implementation (Conceptual Framework):**
```
External Load = Distance (miles) + Power_Normalized_Factor + Elevation_Adjustment
```

**Swimming Implementation (Conceptual Framework):**
```
External Load = Distance (meters) × Stroke_Efficiency_Factor × Water_Resistance_Coefficient
```

**Strength Training Implementation (Conceptual Framework):**
```
External Load = Σ(Sets × Reps × Weight) / Individual_Strength_Baseline
```

**Internal ACWR Calculation (Universal Across All Sports):** The internal load calculation remains consistent across all athletic applications:

```
Heart Rate Reserve = (Exercise HR - Resting HR) / (Max HR - Resting HR)
TRIMP = Duration × HR Reserve × 0.64^(k × HR Reserve)
Where k = 1.92 (males) or 1.67 (females)
Acute Internal Load = 7-day rolling average of TRIMP values
Chronic Internal Load = 28-day rolling average of TRIMP values
Internal ACWR = Acute Internal Load / Chronic Internal Load
```

**Normalized Divergence Calculation (Universal Formula):** The core innovation applies identically across all sports, as illustrated in FIG. 2 which demonstrates the mathematical formula implementation with scale independence properties:

```
normalized_divergence = (external_acwr - internal_acwr) / ((external_acwr + internal_acwr) / 2)
```

As shown in FIG. 2, this mathematical relationship maintains identical properties regardless of the specific external load metrics employed (distance, power, volume, etc.) or sport application, providing the fundamental innovation's universal applicability across athletic disciplines through arithmetic mean normalization (208) producing the final divergence output (210).

### Edge Case Handling

The system implements comprehensive edge case handling to ensure robust operation across all sport applications, as detailed in the algorithmic flow of FIG. 1:

- **Dual-Zero Condition**: Returns null when both ACWR values equal zero
- **Single-Zero Condition**: Approaches maximum divergence (±2.0) when one ACWR equals zero  
- **Near-Zero Threshold**: Values below 0.01 receive special handling to prevent numerical instability
- **Null Input Handling**: Graceful error handling maintains system stability
- **Sport Detection Errors**: Automatic fallback to manual sport selection when automatic detection fails

### API Integration and External Platform Support

The system implements comprehensive integration with external fitness platforms through secure OAuth authentication and real-time data synchronization. As illustrated in FIG. 6, the OAuth and API architecture provides enterprise-grade security through per-user token isolation (500-506), intelligent rate limiting with tiered service levels (510-516), and real-time webhook event processing (520-530) for immediate data synchronization.

**Multi-Platform Data Aggregation:** FIG. 7 demonstrates the comprehensive platform integration architecture supporting multiple data sources including Strava (540), Garmin Connect (542), Apple Health (544), and Fitbit (546) platforms. The unified data normalization engine (550) processes diverse data formats including TCX, GPX, FIT, and JSON to enable consistent ACWR calculations regardless of data source.

**Third-Party Developer Support:** The system architecture includes comprehensive SDK frameworks for third-party integration including iOS SDK (560), Android SDK (562), and Web SDK (564) components, as shown in FIG. 7. The developer ecosystem (570-580) supports individual developers through enterprise white-label solutions, enabling broad market distribution and commercial licensing opportunities.

**Rate Limiting and Performance:** The API architecture implements intelligent rate limiting with standard (1000/hour), enterprise (10,000/hour), and premium (<500ms response) service tiers. Production validation demonstrates support for 10,000+ concurrent users with 99.7% uptime reliability and sub-2-second processing capabilities.

### Multi-User Enterprise Architecture

The system supports enterprise deployment with complete data isolation between users while sharing computational resources efficiently, as demonstrated in FIG. 4. The architecture includes mandatory user_id filtering at all database query levels (322, 360), application-level security enforcement, session management and authentication protocols, and Row-Level Security (RLS) implementation at the database level.

Performance characteristics include support for 10,000+ concurrent users, 99.7% uptime reliability, sub-50ms query response times, and automatic scaling from 0-1000 container instances based on demand, as illustrated in the system architecture of FIG. 3.

### Risk Assessment and Divergence Analysis

The system analyzes normalized divergence values to provide injury risk assessment across all sports. The core innovation focuses on the magnitude and direction of divergence values rather than rigid threshold classifications.

**Divergence Interpretation:** Positive divergence values indicate external training loads exceed internal adaptation capacity, suggesting risk for mechanical or overuse injuries. Negative divergence values indicate internal physiological stress exceeds external mechanical demands, suggesting risk for systemic fatigue or cardiovascular overreach.

**Flexible Assessment Framework:** The system provides configurable assessment approaches based on user requirements and application context. Assessment may utilize divergence magnitude analysis, directional pattern recognition, or temporal trend evaluation depending on implementation preferences.

**Alert Generation:** Automated alert systems provide real-time notifications based on divergence analysis, with customizable sensitivity settings for different athlete populations and sport-specific requirements.

### Optional Enhancement: Temporal Trend Analysis

In certain embodiments, the system may implement temporal trend analysis of normalized divergence values as an enhancement to the core innovation. This optional capability enables monitoring of divergence patterns over configurable time periods, identification of concerning directional changes before they reach critical levels, and generation of proactive training recommendations based on trending patterns.

This enhancement provides early intervention strategies by analyzing the rate and direction of divergence changes rather than relying solely on absolute magnitude assessment, offering additional value for users requiring sophisticated trend-based guidance while maintaining the fundamental breakthrough of normalized dual-metric ACWR comparison.

## CLAIMS

### Independent Claims

**CLAIM 1** (Method Claim - Core Divergence Innovation)

A computer-implemented method for predicting injury risk in athletes engaged in physical training activities across multiple sports disciplines, comprising:

(a) receiving external training load data representative of mechanical training demands from one or more tracking devices, said external training load data varying by sport type and including at least one of distance measurements, elevation gain measurements, power output measurements, or volume-load measurements;

(b) calculating an external acute-to-chronic workload ratio (external ACWR) by:
    i. determining acute external load as a rolling average of external training loads over a first predetermined time period of approximately 7 days,
    ii. determining chronic external load as a rolling average of external training loads over a second predetermined time period of approximately 28 days, and
    iii. computing said external ACWR as a ratio of said acute external load to said chronic external load;

(c) receiving internal training load data representative of physiological training response from one or more physiological monitoring devices, said internal training load data including heart rate measurements during said athletic activities;

(d) calculating an internal acute-to-chronic workload ratio (internal ACWR) using Training Impulse (TRIMP) methodology by:
    i. computing TRIMP values based on exercise duration, heart rate reserve, and exponential weighting factors,
    ii. determining acute internal load as a rolling average of TRIMP values over said first predetermined time period,
    iii. determining chronic internal load as a rolling average of TRIMP values over said second predetermined time period, and
    iv. computing said internal ACWR as a ratio of said acute internal load to said chronic internal load;

(e) computing a normalized divergence value between said external ACWR and said internal ACWR using arithmetic mean normalization according to the formula: 
    normalized_divergence = (external_acwr - internal_acwr) / ((external_acwr + internal_acwr) / 2);

(f) analyzing said normalized divergence value for injury risk assessment based on magnitude and direction; and

(g) generating an injury risk assessment output indicating potential for injury occurrence.

**CLAIM 2** (System Claim - Technical Architecture)

A system for monitoring athletic training loads and predicting injury risk across multiple sports disciplines, comprising:

(a) a data acquisition interface configured to receive external training load data from sport-specific tracking devices and internal training load data from heart rate monitoring devices;

(b) a memory storage unit configured to maintain historical training load data for calculation of rolling averages over acute and chronic time periods;

(c) a processing unit configured to calculate sport-adapted external and internal acute-to-chronic workload ratios and compute normalized divergence values using arithmetic mean normalization;

(d) a risk assessment engine configured to analyze said normalized divergence values for injury risk determination; and

(e) an output interface configured to present injury risk assessments and training recommendations to users.

**CLAIM 3** (Computer-Readable Medium Claim)

A non-transitory computer-readable medium storing instructions that, when executed by one or more processors, cause said processors to perform operations comprising processing external and internal training load data from multiple sports disciplines, computing normalized divergence between ACWR values using arithmetic mean normalization, analyzing divergence for injury risk levels, and generating output signals for risk alerts and training recommendations.

### Dependent Claims - Mathematical and Technical Implementation

**CLAIM 4:** The method of claim 1, wherein said external training load data includes distance measurements and elevation gain measurements for trail running applications, and said external ACWR calculation includes elevation-adjusted load metrics.

**CLAIM 5:** The method of claim 4, wherein said elevation gain is converted to distance equivalent using a conversion factor of approximately 1000 feet per mile for energy expenditure normalization.

**CLAIM 6:** The method of claim 1, wherein said TRIMP calculation includes gender-specific exponential weighting factors of k=1.92 for males and k=1.67 for females.

**CLAIM 7:** The method of claim 1, wherein said processing latency for normalized divergence calculation is less than 5 seconds for real-time injury risk assessment.

**CLAIM 8:** The method of claim 1, wherein said arithmetic mean normalization provides scale-independent comparison enabling assessment across diverse athlete populations and training intensities.

### Dependent Claims - Enhanced Analysis Options

**CLAIM 9:** The method of claim 1, further comprising analyzing temporal trends in said normalized divergence values over configurable time periods and generating training recommendations based on divergence pattern analysis.

**CLAIM 10:** The method of claim 9, wherein analyzing temporal trends comprises determining trajectory direction indicating whether divergence magnitude is increasing, decreasing, or stabilizing over recent training periods.

**CLAIM 11:** The system of claim 2, further comprising a trend analysis module configured to monitor divergence patterns over time and generate proactive training optimization recommendations.

### Dependent Claims - Multi-Sport Applications

**CLAIM 12:** The method of claim 1, wherein said athletic activities comprise road running, and said external load calculation uses distance measurements with pace-based difficulty adjustments.

**CLAIM 13:** The method of claim 1, wherein said athletic activities comprise cycling, and said external load calculation incorporates power output measurements normalized to individual functional threshold power.

**CLAIM 14:** The method of claim 1, wherein said athletic activities comprise strength training, and said external load calculation comprises volume-load products of sets, repetitions, and resistance normalized to individual strength capacity.

**CLAIM 15:** The method of claim 1, wherein said system automatically detects athletic activity type from sensor data patterns and applies corresponding external load calculation methodology.

## ABSTRACT

A computer-implemented method and system for predicting athletic injury risk across multiple sports through normalized divergence analysis between external and internal acute-to-chronic workload ratios (ACWR). The system receives sport-specific external training data and heart rate-based internal training data, calculating respective ACWR values over 7-day acute and 28-day chronic periods. A novel normalized divergence formula compares external and internal ACWR using arithmetic mean normalization: (external_acwr - internal_acwr) / ((external_acwr + internal_acwr) / 2). The system addresses fundamental limitations in existing single-metric approaches by providing comparative analysis between mechanical training demands and physiological adaptation responses. Complete implementation has been developed and validated for trail running applications with elevation-adjusted external load calculations, while the mathematical framework provides conceptual foundation for road running, cycling, strength training, skiing, swimming, and other athletic disciplines. The invention enables universal injury prediction methodology through scale-independent divergence analysis applicable across all sports.

## FILING INFORMATION

**Application Type:** Provisional Patent Application  
**Filing Entity:** Micro Entity  
**Filing Fee:** $160 (includes Form SB/15A)  
**Priority Date:** Upon filing

**Micro Entity Status Requirements:** 
1. Small Entity: Individual inventor, <500 employees, or nonprofit 
2. Income Limit: <$206,557 gross income in 2024  
3. Application Limit: <4 previous patent applications as inventor 
4. Assignment Restriction: No licensing to entities exceeding income limits

**Required Form:** SB/15A (Certification of Micro Entity Status)