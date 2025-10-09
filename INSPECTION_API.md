# Inspection Management API Documentation

## Overview
The Inspection Management API allows authorized officers to create, view, and manage inspections of villages within their jurisdiction. The API implements role-based access control to ensure officers can only inspect villages they are authorized to access.

## Authorization & Jurisdiction Rules

### Who Can Inspect
- **CEO (District Collector)**: Can inspect any village in their district
- **BDO (Block Development Officer)**: Can inspect any village in their block
- **WORKER**: Can inspect villages in their assigned area (village/block/district)
- **ADMIN/SUPERADMIN**: Can inspect any village

### Who Cannot Inspect
- **VDO (Village Development Officer)**: VDOs are not authorized to create inspections

## API Endpoints

### 1. Create Inspection
**Endpoint**: `POST /api/v1/inspections/`

**Description**: Create a new inspection for a village within your jurisdiction.

**Request Body**:
```json
{
  "village_id": 1,
  "remarks": "General observations about the inspection",
  "inspection_date": "2025-10-09",
  "start_time": "2025-10-09T10:00:00",
  "lat": "26.9124",
  "long": "75.7873",
  "register_maintenance": true,
  "household_waste": {
    "waste_collection_frequency": "DAILY",
    "dry_wet_vehicle_segregation": true,
    "covered_collection_in_vehicles": true,
    "waste_disposed_at_rrc": true,
    "rrc_waste_collection_and_disposal_arrangement": true,
    "waste_collection_vehicle_functional": true
  },
  "road_and_drain": {
    "road_cleaning_frequency": "WEEKLY",
    "drain_cleaning_frequency": "FORTNIGHTLY",
    "disposal_of_sludge_from_drains": true,
    "drain_waste_colllected_on_roadside": false
  },
  "community_sanitation": {
    "csc_cleaning_frequency": "DAILY",
    "electricity_and_water": true,
    "csc_used_by_community": true,
    "pink_toilets_cleaning": true,
    "pink_toilets_used": true
  },
  "other_items": {
    "firm_paid_regularly": true,
    "cleaning_staff_paid_regularly": true,
    "firm_provided_safety_equipment": true,
    "regular_feedback_register_entry": true,
    "chart_prepared_for_cleaning_work": true,
    "village_visibly_clean": true,
    "rate_chart_displayed": true
  },
  "images": [
    {
      "image_url": "https://s3.amazonaws.com/bucket/inspection-image-1.jpg"
    },
    {
      "image_url": "https://s3.amazonaws.com/bucket/inspection-image-2.jpg"
    }
  ]
}
```

**Required Fields**:
- `village_id`: ID of the village being inspected
- `lat`: Latitude of inspection location
- `long`: Longitude of inspection location

**Optional Fields**:
- `remarks`: General remarks about the inspection
- `inspection_date`: Date of inspection (defaults to today)
- `start_time`: Start time of inspection (defaults to now)
- `register_maintenance`: Whether registers are properly maintained
- `household_waste`: Household waste collection details
- `road_and_drain`: Road and drain cleaning details
- `community_sanitation`: Community sanitation details
- `other_items`: Other inspection items
- `images`: Array of inspection images

**Enum Values**:
- `WasteCollectionFrequency`: DAILY, ONCE_IN_THREE_DAYS, WEEKLY, NONE
- `RoadCleaningFrequency`: WEEKLY, FORTNIGHTLY, MONTHLY, NONE
- `DrainCleaningFrequency`: WEEKLY, FORTNIGHTLY, MONTHLY, NONE
- `CSCCleaningFrequency`: DAILY, ONCE_IN_THREE_DAYS, WEEKLY, NONE

**Response** (201 Created):
```json
{
  "id": 1,
  "remarks": "General observations about the inspection",
  "position_holder_id": 5,
  "village_id": 1,
  "date": "2025-10-09",
  "start_time": "2025-10-09T10:00:00",
  "lat": "26.9124",
  "long": "75.7873",
  "register_maintenance": true,
  "officer_name": "Rajesh Kumar",
  "officer_role": "CEO",
  "village_name": "Rampur",
  "block_name": "Jaipur Rural",
  "district_name": "Jaipur",
  "household_waste": {
    "id": 1,
    "waste_collection_frequency": "DAILY",
    "dry_wet_vehicle_segregation": true,
    "covered_collection_in_vehicles": true,
    "waste_disposed_at_rrc": true,
    "rrc_waste_collection_and_disposal_arrangement": true,
    "waste_collection_vehicle_functional": true
  },
  "road_and_drain": {
    "id": 1,
    "road_cleaning_frequency": "WEEKLY",
    "drain_cleaning_frequency": "FORTNIGHTLY",
    "disposal_of_sludge_from_drains": true,
    "drain_waste_colllected_on_roadside": false
  },
  "community_sanitation": {
    "id": 1,
    "csc_cleaning_frequency": "DAILY",
    "electricity_and_water": true,
    "csc_used_by_community": true,
    "pink_toilets_cleaning": true,
    "pink_toilets_used": true
  },
  "other_items": {
    "id": 1,
    "firm_paid_regularly": true,
    "cleaning_staff_paid_regularly": true,
    "firm_provided_safety_equipment": true,
    "regular_feedback_register_entry": true,
    "chart_prepared_for_cleaning_work": true,
    "village_visibly_clean": true,
    "rate_chart_displayed": true
  },
  "images": [
    {
      "id": 1,
      "inspection_id": 1,
      "image_url": "https://s3.amazonaws.com/bucket/inspection-image-1.jpg"
    },
    {
      "id": 2,
      "inspection_id": 1,
      "image_url": "https://s3.amazonaws.com/bucket/inspection-image-2.jpg"
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request data or village not found
- `403 Forbidden`: VDO trying to create inspection or user lacks jurisdiction
- `401 Unauthorized`: User not authenticated

---

### 2. Get Inspection Details
**Endpoint**: `GET /api/v1/inspections/{inspection_id}`

**Description**: Get detailed information about a specific inspection.

**Path Parameters**:
- `inspection_id`: ID of the inspection

**Response** (200 OK):
Same as Create Inspection response

**Error Responses**:
- `403 Forbidden`: User doesn't have access to this inspection
- `404 Not Found`: Inspection not found

---

### 3. Get Inspections List (Paginated)
**Endpoint**: `GET /api/v1/inspections/`

**Description**: Get paginated list of inspections within user's jurisdiction.

**Query Parameters**:
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Number of items per page
- `village_id` (optional): Filter by specific village
- `block_id` (optional): Filter by specific block
- `district_id` (optional): Filter by specific district
- `start_date` (optional): Filter inspections from this date onwards (format: YYYY-MM-DD)
- `end_date` (optional): Filter inspections up to this date (format: YYYY-MM-DD)

**Example Request**:
```
GET /api/v1/inspections/?page=1&page_size=20&district_id=1&start_date=2025-10-01&end_date=2025-10-09
```

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "village_id": 1,
      "village_name": "Rampur",
      "block_name": "Jaipur Rural",
      "district_name": "Jaipur",
      "date": "2025-10-09",
      "officer_name": "Rajesh Kumar",
      "officer_role": "CEO",
      "remarks": "General observations",
      "image_count": 2
    },
    {
      "id": 2,
      "village_id": 2,
      "village_name": "Khandela",
      "block_name": "Jaipur Rural",
      "district_name": "Jaipur",
      "date": "2025-10-08",
      "officer_name": "Priya Sharma",
      "officer_role": "BDO",
      "remarks": "Good cleanliness observed",
      "image_count": 3
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

**Error Responses**:
- `400 Bad Request`: Invalid page or page_size parameters

---

### 4. Get Inspection Statistics
**Endpoint**: `GET /api/v1/inspections/stats/summary`

**Description**: Get inspection statistics for the user's jurisdiction.

**Response** (200 OK):
```json
{
  "total_inspections": 145,
  "inspections_this_month": 23,
  "inspections_this_week": 0,
  "inspections_today": 5,
  "villages_inspected": 45
}
```

---

## Access Control Matrix

| Role        | Can Create | View Own | View All in District | View All in Block | View All in Village |
|-------------|------------|----------|---------------------|-------------------|-------------------|
| SUPERADMIN  | ✓          | ✓        | ✓                   | ✓                 | ✓                 |
| ADMIN       | ✓          | ✓        | ✓                   | ✓                 | ✓                 |
| CEO         | ✓          | ✓        | ✓                   | ✓                 | ✓                 |
| BDO         | ✓          | ✓        | ✗                   | ✓                 | ✓                 |
| VDO         | ✗          | ✗        | ✗                   | ✗                 | ✓                 |
| WORKER      | ✓          | ✓        | Assigned only       | Assigned only     | Assigned only     |

## Implementation Notes

1. **Jurisdiction Validation**: The API automatically validates that the officer has jurisdiction over the village before allowing inspection creation.

2. **Geography Relationships**: District and block information is automatically derived from the village relationship - no need to specify them separately.

3. **Optional Sections**: All inspection item sections (household waste, road and drain, community sanitation, other items) are optional. You can include only the sections relevant to your inspection.

4. **Images**: Images should be uploaded to S3 first (using the S3 upload API), then the URLs should be included in the inspection request.

5. **Pagination**: Default page size is 20, maximum is 100 to prevent performance issues.

6. **Date Filtering**: When using date filters, both start_date and end_date are inclusive.

## Example Usage

### Create a Basic Inspection (Minimal Data)
```bash
curl -X POST "http://localhost:8000/api/v1/inspections/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "village_id": 1,
    "lat": "26.9124",
    "long": "75.7873",
    "remarks": "Quick inspection - all good"
  }'
```

### Get Inspections for Current Month
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/?start_date=2025-10-01&end_date=2025-10-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/stats/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```
