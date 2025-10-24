# Annual Survey Analytics APIs

## Overview
Created comprehensive analytics APIs for the Annual Survey (Village Master Data) module based on the dashboard requirements shown in the screenshots.

## Files Created

### 1. Response Models (`models/response/annual_survey_analytics.py`)
Defines Pydantic response models for analytics data:
- `SchemeTargetAchievement` - Scheme-wise target vs achievement data
- `VillageMasterDataCoverage` - Coverage metrics by geography
- `AnnualOverview` - Annual overview metrics
- `StateAnalytics` - State-level comprehensive analytics
- `DistrictAnalytics` - District-level comprehensive analytics
- `BlockAnalytics` - Block-level comprehensive analytics  
- `GPAnalytics` - GP-level analytics

### 2. Analytics Service (`services/annual_survey_analytics.py`)
Business logic for calculating analytics:
- `AnnualSurveyAnalyticsService` - Main service class
  - `get_state_analytics()` - State-level analytics
  - `get_district_analytics()` - District-level analytics
  - `get_block_analytics()` - Block-level analytics
  - `get_gp_analytics()` - GP-level analytics
  - Helper methods for calculations and aggregations

### 3. Controller Endpoints (`controllers/annual_survey.py`)
Added new analytics API endpoints:

## API Endpoints

### 1. State-Level Analytics
```
GET /api/v1/annual-surveys/analytics/state?fy_id={optional}
```

**Response includes:**
- Total village master data count (total GP surveys)
- Village master data coverage percentage
- Total funds sanctioned (in Crores)
- Total work order amount (in Crores)
- SBMG target achievement rate (overall percentage)
- Scheme-wise target vs achievement (IHHL, CSC, RRC, PWMU, Soak pit, Magic pit, Leach pit, WSP, DEWATS)
- Annual overview:
  - Fund utilization rate
  - Average cost per household (D2D)
  - Households covered (D2D)
  - GPs with identified asset gaps
  - Active sanitation bidders count
- District-wise coverage breakdown

### 2. District-Level Analytics
```
GET /api/v1/annual-surveys/analytics/district/{district_id}?fy_id={optional}
```

**Response includes:**
- District information
- Total village master data count for district
- Coverage percentage
- Financial metrics (funds sanctioned, work order amounts)
- SBMG target achievement rate
- Scheme-wise target vs achievement
- Annual overview metrics
- Block-wise coverage within the district

**Authorization:** Users can only view analytics for their jurisdiction

### 3. Block-Level Analytics
```
GET /api/v1/annual-surveys/analytics/block/{block_id}?fy_id={optional}
```

**Response includes:**
- Block and district information
- Total village master data count for block
- Coverage percentage
- Financial metrics
- SBMG target achievement rate
- Scheme-wise target vs achievement
- Annual overview metrics
- GP-wise coverage within the block

**Authorization:** Users can only view analytics for their jurisdiction

### 4. GP-Level Analytics
```
GET /api/v1/annual-surveys/analytics/gp/{gp_id}?fy_id={optional}
```

**Response includes:**
- GP, block, and district information
- Master data availability status ("Available" or "Not Available")
- Survey details (if available):
  - Survey ID and date
  - Financial metrics
  - Scheme-wise target vs achievement
  - Fund utilization rate
  - Households covered (D2D)
  - Number of villages
  - Active agency/bidder name

**Authorization:** Users can only view analytics for their jurisdiction

## Key Features

### Scheme Coverage
All APIs track the following SBMG schemes:
- IHHL (Individual Household Latrine)
- CSC (Community Sanitary Complex)
- RRC (Resource Recovery Centre)
- PWMU (Plastic Waste Management Unit)
- Soak pit
- Magic pit
- Leach pit
- WSP (Waste Stabilization Pond)
- DEWATS (Decentralized Wastewater Treatment System)

### Metrics Calculated
- **Coverage:** Percentage of GPs with master data
- **Financial:** Funds sanctioned and work order amounts (in Crores)
- **Achievement:** Target vs actual achievement percentages
- **Utilization:** Fund utilization rate
- **Households:** D2D collection coverage
- **Asset Gaps:** GPs where targets exceed achievements

### Filtering
- Optional `fy_id` parameter to filter by financial year
- If not provided, analytics include all financial years

### Authorization
- All endpoints require staff role (`require_staff_role` dependency)
- Users can only access analytics within their jurisdiction:
  - District users: their district and below
  - Block users: their block and below
  - GP users: only their GP
  - Admin users: all data

## Database Queries
The service efficiently uses:
- SQLAlchemy async queries
- Eager loading with `selectinload()` for related data
- Aggregation functions for counting and summing
- Distinct counts for coverage calculations

## Response Format
All responses return JSON with proper typing via Pydantic models, ensuring:
- Type safety
- Automatic validation
- Clear API documentation via FastAPI's automatic OpenAPI generation

## Usage Example

```python
# Get state-level analytics for current FY
GET /api/v1/annual-surveys/analytics/state?fy_id=1

# Get district analytics
GET /api/v1/annual-surveys/analytics/district/5

# Get block analytics for specific FY
GET /api/v1/annual-surveys/analytics/block/12?fy_id=1

# Get GP analytics
GET /api/v1/annual-surveys/analytics/gp/45
```

## Dashboard Mapping

The screenshots show two main views:

### State View
- Maps to: `GET /api/v1/annual-surveys/analytics/state`
- Shows: Total stats, coverage %, financial metrics, scheme charts, annual overview, district coverage table

### Block View  
- Maps to: `GET /api/v1/annual-surveys/analytics/block/{block_id}`
- Shows: Block stats, scheme charts, annual overview, GP coverage table

All metrics shown in the dashboards are provided by these APIs.
