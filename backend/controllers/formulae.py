"""
Formulae Controller
API endpoint to return all formulae used across the application
"""

from typing import Dict, Any
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/", response_class=JSONResponse)
async def get_all_formulae() -> Dict[str, Any]:
    """
    Get all formulae used across the application in markdown format.
    Returns a dictionary with formula names as keys and their descriptions in markdown as values.
    """
    
    formulae = {
        "COVERAGE_PERCENTAGE": """
**Formula:** `(GPs with Data / Total GPs) × 100`

**Description:** Calculates the percentage of Gram Panchayats (GPs) that have master data available.

**Used in:** Annual Survey Analytics (State, District, Block levels)

**Example:** If 800 GPs have data out of 1000 total GPs:
```
Coverage = (800 / 1000) × 100 = 80%
```
""",

        "SBMG_TARGET_ACHIEVEMENT_RATE": """
**Formula:** `(Total Achievement / Total Target) × 100`

**Description:** Calculates the overall achievement rate for SBMG (Swachh Bharat Mission - Gramin) schemes across all categories.

**Used in:** Annual Survey Analytics

**Calculation Steps:**
1. Sum all scheme targets (IHHL, CSC, RRC, PWMU, Soak pit, Magic pit, Leach pit, WSP, DEWATS)
2. Sum all scheme achievements
3. Calculate percentage: `(Total Achievement / Total Target) × 100`

**Example:** If Total Target = 10,000 units and Total Achievement = 8,500 units:
```
Achievement Rate = (8,500 / 10,000) × 100 = 85%
```
""",

        "SCHEME_ACHIEVEMENT_PERCENTAGE": """
**Formula:** `(Scheme Achievement / Scheme Target) × 100`

**Description:** Calculates achievement percentage for individual SBMG schemes.

**Used in:** Annual Survey Analytics for each scheme

**Applicable Schemes:**
- IHHL (Individual Household Latrine)
- CSC (Community Sanitary Complex)
- RRC (Resource Recovery Centre)
- PWMU (Plastic Waste Management Unit)
- Soak pit
- Magic pit
- Leach pit
- WSP (Waste Stabilization Pond)
- DEWATS (Decentralized Wastewater Treatment System)

**Example:** For IHHL with Target = 5,000 and Achievement = 4,200:
```
IHHL Achievement = (4,200 / 5,000) × 100 = 84%
```
""",

        "FUND_UTILIZATION_RATE": """
**Formula:** `(Total Work Order Amount / Total Funds Sanctioned) × 100`

**Description:** Calculates the percentage of sanctioned funds that have been utilized through work orders.

**Used in:** Annual Survey Analytics - Annual Overview

**Example:** If Funds Sanctioned = ₹100 Crores and Work Order Amount = ₹75 Crores:
```
Utilization Rate = (75 / 100) × 100 = 75%
```
""",

        "AVERAGE_COST_PER_HOUSEHOLD_D2D": """
**Formula:** `Total Work Order Amount / Total Households Covered (D2D)`

**Description:** Calculates the average cost per household for Door-to-Door (D2D) waste collection services.

**Used in:** Annual Survey Analytics - Annual Overview

**Example:** If Total Work Order = ₹50,00,000 and Households Covered = 10,000:
```
Average Cost = 50,00,000 / 10,000 = ₹500 per household
```
""",

        "AMOUNT_IN_CRORES_CONVERSION": """
**Formula:** `Amount in Rupees / 10,000,000`

**Description:** Converts monetary amounts from Rupees to Crores for better readability.

**Used in:** Annual Survey Analytics for all financial metrics

**Example:** If Amount = ₹150,000,000:
```
Amount in Crores = 150,000,000 / 10,000,000 = 15 Crores
```
""",

        "COMPLAINT_SCORE": """
**Formula:** `Score = Score1 + Score2`

Where:
- **Score1:** `max(0, (604,800 - Average Resolution Time) / 604,800) × 50`
- **Score2:** `max(0, (Total Resolved Complaints / Total Complaints) × 50)`

**Description:** Calculates a performance score (0-100) for complaint management based on resolution time and resolution rate.

**Components:**
1. **Score1 (50 points max):** Rewards faster resolution (SLA = 7 days = 604,800 seconds)
2. **Score2 (50 points max):** Rewards higher resolution rate

**Used in:** Complaint Analytics for ranking geographies

**Example:**
- Total Complaints = 100
- Resolved Complaints = 85
- Average Resolution Time = 302,400 seconds (3.5 days)

```
Score1 = max(0, (604,800 - 302,400) / 604,800) × 50 = 25 points
Score2 = max(0, (85 / 100) × 50) = 42.5 points
Total Score = 25 + 42.5 = 67.5
```

**Note:** 604,800 seconds = 7 days (7 × 24 × 60 × 60)
""",

        "INSPECTION_OVERALL_SCORE": """
**Formula:** `(Total Points Earned / Maximum Points) × 100`

Where **Maximum Points = 180**

**Description:** Calculates the overall inspection score as a percentage based on points earned across all inspection categories.

**Category Breakdown:**
1. **Household Waste (50 points max)**
2. **Road Cleaning (10 points max)**
3. **Drain Cleaning (30 points max)**
4. **Community Sanitation (40 points max)**
5. **Other Inspections (50 points max)**

**Used in:** Inspection Analytics

**Example:** If Total Points Earned = 135 out of 180:
```
Overall Score = (135 / 180) × 100 = 75%
```
""",

        "INSPECTION_HOUSEHOLD_WASTE_SCORE": """
**Formula:** `(Household Waste Points / 50) × 100`

**Points Distribution (Total: 50 points):**

1. **Waste Collection Frequency (10 points max):**
   - Daily: 10 points
   - Once in 3 days: 7 points
   - Weekly: 3 points
   - Other: 0 points

2. **Dry/Wet Vehicle Segregation:** 10 points (if YES)
3. **Covered Collection in Vehicles:** 10 points (if YES)
4. **Waste Disposed at RRC:** 10 points (if YES)
5. **Waste Collection Vehicle Functional:** 10 points (if YES)

**Used in:** Inspection Scoring System

**Example:** Daily collection (10) + Segregation (10) + Covered (10) + RRC disposal (10) + Vehicle functional (10) = 50 points
```
Score = (50 / 50) × 100 = 100%
```
""",

        "INSPECTION_ROAD_CLEANING_SCORE": """
**Formula:** `(Road Cleaning Points / 10) × 100`

**Points Distribution (Total: 10 points):**

**Road Cleaning Frequency:**
- Weekly: 10 points
- Fortnightly: 5 points
- Monthly: 2 points
- Other: 0 points

**Used in:** Inspection Scoring System

**Example:** Weekly cleaning = 10 points
```
Score = (10 / 10) × 100 = 100%
```
""",

        "INSPECTION_DRAIN_CLEANING_SCORE": """
**Formula:** `(Drain Cleaning Points / 30) × 100`

**Points Distribution (Total: 30 points):**

1. **Drain Cleaning Frequency (10 points max):**
   - Weekly: 10 points
   - Fortnightly: 5 points
   - Monthly: 2 points
   - Other: 0 points

2. **Disposal of Sludge from Drains:** 10 points (if YES)
3. **Drain Waste NOT Collected on Roadside:** 10 points (if NO - inverted scoring)

**Used in:** Inspection Scoring System

**Example:** Weekly cleaning (10) + Sludge disposal (10) + No roadside waste (10) = 30 points
```
Score = (30 / 30) × 100 = 100%
```
""",

        "INSPECTION_COMMUNITY_SANITATION_SCORE": """
**Formula:** `(Community Sanitation Points / 40) × 100`

**Points Distribution (Total: 40 points):**

1. **CSC Cleaning Frequency (10 points max):**
   - Daily: 10 points
   - Once in 3 days: 7 points
   - Weekly: 3 points
   - Other: 0 points

2. **Electricity and Water Available:** 10 points (if YES)
3. **CSC Used by Community:** 10 points (if YES)
4. **Pink Toilets Cleaning:** 10 points (if YES)

**Used in:** Inspection Scoring System

**Example:** Daily cleaning (10) + Electricity/Water (10) + Used by community (10) + Pink toilets (10) = 40 points
```
Score = (40 / 40) × 100 = 100%
```
""",

        "INSPECTION_OTHER_SCORE": """
**Formula:** `(Other Inspection Points / 50) × 100`

**Points Distribution (Total: 50 points):**

1. **Firm Paid Regularly:** 10 points (if YES)
2. **Cleaning Staff Paid Regularly:** 10 points (if YES)
3. **Firm Provided Safety Equipment:** 10 points (if YES)
4. **Village Visibly Clean:** 10 points (if YES)
5. **Rate Chart Displayed:** 10 points (if YES)

**Used in:** Inspection Scoring System

**Example:** All criteria met = 50 points
```
Score = (50 / 50) × 100 = 100%
```
""",

        "INSPECTION_COVERAGE_PERCENTAGE": """
**Formula:** `(Number of Inspected Entities / Total Entities) × 100`

**Description:** Calculates inspection coverage at various geographic levels (Village, GP, Block, District).

**Special Case:** For individual village with inspections = 100%, without = 0%

**Used in:** Inspection Analytics

**Example:** If 45 out of 60 GPs have been inspected:
```
Coverage = (45 / 60) × 100 = 75%
```
""",

        "AVERAGE_RESOLUTION_TIME": """
**Formula:** `Average((Resolved_At - Created_At) in seconds)`

**Description:** Calculates the average time taken to resolve complaints in seconds. If complaint is not resolved, uses current time as reference.

**Conversion:** Result is in seconds (divide by 86,400 for days)

**Used in:** Complaint Analytics and Scoring

**Example:** If complaints were resolved in 259,200 sec, 432,000 sec, and 172,800 sec:
```
Average = (259,200 + 432,000 + 172,800) / 3 = 288,000 seconds = 3.33 days
```
""",

        "TOTAL_SCHEME_TARGET": """
**Formula:** `Sum of all individual scheme targets`

**Components:**
```
Total Target = IHHL_target + CSC_target + RRC_target + PWMU_target + 
               Soak_pit_target + Magic_pit_target + Leach_pit_target + 
               WSP_target + DEWATS_target
```

**Description:** Aggregates all scheme-specific targets to get overall SBMG target.

**Used in:** Annual Survey Analytics

**Example:**
```
Total = 5000 + 50 + 20 + 10 + 1000 + 500 + 300 + 5 + 2 = 6,887 units
```
""",

        "TOTAL_SCHEME_ACHIEVEMENT": """
**Formula:** `Sum of all individual scheme achievements`

**Components:**
```
Total Achievement = IHHL_achievement + CSC_achievement + RRC_achievement + 
                    PWMU_achievement + Soak_pit_achievement + 
                    Magic_pit_achievement + Leach_pit_achievement + 
                    WSP_achievement + DEWATS_achievement
```

**Description:** Aggregates all scheme-specific achievements to get overall SBMG achievement.

**Sources:**
- IHHL, CSC: From SBMG Assets
- Soak pit, Magic pit, Leach pit, WSP, DEWATS: From GWM Assets

**Used in:** Annual Survey Analytics

**Example:**
```
Total = 4200 + 48 + 18 + 8 + 950 + 480 + 290 + 5 + 2 = 6,001 units
```
""",
    }
    
    return {"status": "success", "data": formulae}
