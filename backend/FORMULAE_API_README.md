# Formulae API Documentation

## Overview
This API endpoint returns all mathematical formulae used across the SBMG Rajasthan backend application. The formulae are returned as key-value pairs where keys are formula names in CAPITAL_LETTERS and values are markdown-formatted descriptions.

## Endpoint

### Get All Formulae
**URL:** `/api/v1/formulae/`  
**Method:** `GET`  
**Authentication:** Not required (public endpoint)

#### Response Format
```json
{
  "status": "success",
  "data": {
    "FORMULA_NAME_1": "markdown formatted formula description",
    "FORMULA_NAME_2": "markdown formatted formula description",
    ...
  }
}
```

#### Example Request
```bash
curl -X GET "http://localhost:8000/api/v1/formulae/"
```

#### Example Response (excerpt)
```json
{
  "status": "success",
  "data": {
    "COVERAGE_PERCENTAGE": "\n**Formula:** `(GPs with Data / Total GPs) × 100`\n\n**Description:** Calculates the percentage of Gram Panchayats (GPs) that have master data available.\n\n**Used in:** Annual Survey Analytics (State, District, Block levels)\n\n**Example:** If 800 GPs have data out of 1000 total GPs:\n```\nCoverage = (800 / 1000) × 100 = 80%\n```\n",
    "SBMG_TARGET_ACHIEVEMENT_RATE": "\n**Formula:** `(Total Achievement / Total Target) × 100`\n\n**Description:** Calculates the overall achievement rate for SBMG (Swachh Bharat Mission - Gramin) schemes across all categories.\n\n**Used in:** Annual Survey Analytics\n\n**Calculation Steps:**\n1. Sum all scheme targets (IHHL, CSC, RRC, PWMU, Soak pit, Magic pit, Leach pit, WSP, DEWATS)\n2. Sum all scheme achievements\n3. Calculate percentage: `(Total Achievement / Total Target) × 100`\n\n**Example:** If Total Target = 10,000 units and Total Achievement = 8,500 units:\n```\nAchievement Rate = (8,500 / 10,000) × 100 = 85%\n```\n"
  }
}
```

## Formula Categories

The API returns formulae for the following categories:

### 1. Annual Survey Analytics
- `COVERAGE_PERCENTAGE` - GP master data coverage
- `SBMG_TARGET_ACHIEVEMENT_RATE` - Overall SBMG achievement rate
- `SCHEME_ACHIEVEMENT_PERCENTAGE` - Individual scheme achievement
- `FUND_UTILIZATION_RATE` - Fund utilization percentage
- `AVERAGE_COST_PER_HOUSEHOLD_D2D` - Average D2D cost per household
- `AMOUNT_IN_CRORES_CONVERSION` - Rupees to Crores conversion
- `TOTAL_SCHEME_TARGET` - Aggregated scheme targets
- `TOTAL_SCHEME_ACHIEVEMENT` - Aggregated scheme achievements

### 2. Complaint Analytics
- `COMPLAINT_SCORE` - Complaint management performance score (0-100)
- `AVERAGE_RESOLUTION_TIME` - Average complaint resolution time

### 3. Inspection Analytics
- `INSPECTION_OVERALL_SCORE` - Overall inspection score
- `INSPECTION_HOUSEHOLD_WASTE_SCORE` - Household waste management score
- `INSPECTION_ROAD_CLEANING_SCORE` - Road cleaning score
- `INSPECTION_DRAIN_CLEANING_SCORE` - Drain cleaning score
- `INSPECTION_COMMUNITY_SANITATION_SCORE` - Community sanitation score
- `INSPECTION_OTHER_SCORE` - Other inspection parameters score
- `INSPECTION_COVERAGE_PERCENTAGE` - Inspection coverage

## Formula Structure

Each formula entry contains the following information in markdown format:

1. **Formula:** The mathematical formula using mathematical notation
2. **Description:** What the formula calculates
3. **Used in:** Where in the application this formula is used
4. **Components/Points Distribution:** (if applicable) Breakdown of scoring components
5. **Example:** A practical calculation example with sample data

## Use Cases

### Frontend Display
Frontend applications can parse the markdown text to display formulae with proper formatting, including:
- Mathematical expressions in code blocks
- Bullet points for components
- Examples with calculations

### Documentation Generation
The formulae can be used to automatically generate documentation about the application's calculation methods.

### API Integration
Third-party applications can retrieve and understand the calculation logic used in various analytics endpoints.

### Audit and Compliance
Provides transparency into calculation methods for auditing and compliance purposes.

## Notes

- All formula names are in CAPITAL_LETTERS with underscores
- Values are in markdown format for rich text display
- The endpoint returns all formulae in a single response
- No pagination is implemented as the total size is manageable
- Formula descriptions include practical examples for better understanding

## Technical Details

**Controller:** `controllers/formulae.py`  
**Route Registration:** `main.py`  
**Tag:** `Formulae`  
**Response Type:** JSON

## Related Endpoints

- `/api/v1/annual-surveys/` - Uses Annual Survey Analytics formulae
- `/api/v1/complaints/` - Uses Complaint Analytics formulae
- `/api/v1/inspections/` - Uses Inspection Analytics formulae

## Version History

- **v1.0.0** - Initial release with 18 formulae across 3 categories
