# Quick Start Guide - Inspection APIs

## For Developers

### Running the Application
```bash
cd backend
python main.py
```

The inspection APIs will be available at: `http://localhost:8000/api/v1/inspections/`

### API Documentation
Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing the APIs

### 1. Login First
```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# Response will include:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer"
# }
```

### 2. Create an Inspection
```bash
# Use the token from login
export TOKEN="your_access_token_here"

# Create minimal inspection
curl -X POST "http://localhost:8000/api/v1/inspections/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "village_id": 1,
    "lat": "26.9124",
    "long": "75.7873",
    "remarks": "Test inspection"
  }'
```

### 3. Get Inspections List
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/?page=1&page_size=20" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Get Inspection Details
```bash
# Replace {id} with actual inspection ID
curl -X GET "http://localhost:8000/api/v1/inspections/1" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Get Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/stats/summary" \
  -H "Authorization: Bearer $TOKEN"
```

## Common Use Cases

### Filter by District
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/?district_id=1" \
  -H "Authorization: Bearer $TOKEN"
```

### Filter by Date Range
```bash
curl -X GET "http://localhost:8000/api/v1/inspections/?start_date=2025-10-01&end_date=2025-10-31" \
  -H "Authorization: Bearer $TOKEN"
```

### Create Complete Inspection
```bash
curl -X POST "http://localhost:8000/api/v1/inspections/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "village_id": 1,
    "lat": "26.9124",
    "long": "75.7873",
    "remarks": "Comprehensive inspection",
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
    }
  }'
```

## Expected Responses

### Success (Create)
Status Code: 201 Created
```json
{
  "id": 1,
  "village_id": 1,
  "village_name": "Rampur",
  "block_name": "Jaipur Rural",
  "district_name": "Jaipur",
  "officer_name": "Rajesh Kumar",
  "officer_role": "CEO",
  ...
}
```

### Error (Forbidden - VDO trying to create)
Status Code: 403 Forbidden
```json
{
  "detail": "VDO cannot create inspections"
}
```

### Error (No Jurisdiction)
Status Code: 400 Bad Request
```json
{
  "detail": "User does not have jurisdiction to inspect this village"
}
```

## Role-Based Testing

### CEO (District Collector)
- Can create inspections in any village in their district
- Can view all inspections in their district

### BDO (Block Development Officer)
- Can create inspections in any village in their block
- Can view all inspections in their block

### VDO (Village Development Officer)
- **Cannot** create inspections
- Can view inspections in their village

### WORKER
- Can create inspections in assigned area
- Can view inspections in assigned area

### ADMIN/SUPERADMIN
- Can create inspections anywhere
- Can view all inspections

## Database Setup

If inspections table doesn't exist, run migrations:
```bash
cd backend
alembic upgrade head
```

## Troubleshooting

### "Village not found" Error
- Ensure the village_id exists in the villages table
- Check that villages are properly loaded in the database

### "Authentication required" Error
- Ensure you're sending the Authorization header
- Token format: `Bearer <token>`
- Check token hasn't expired

### "No jurisdiction" Error
- Verify your user's position assignment
- Check the position has the correct district/block/village set
- Ensure you're not logged in as VDO

### Type Errors in Response
- These are mostly Pylance warnings and can be ignored
- The API will work correctly at runtime

## Code Organization

```
backend/
├── models/
│   ├── requests/
│   │   └── inspection.py          # Request models
│   ├── response/
│   │   └── inspection.py          # Response models
│   └── database/
│       └── inspection.py          # Database models (existing)
├── services/
│   └── inspection.py              # Business logic
├── controllers/
│   └── inspection.py              # API endpoints
└── main.py                        # Router registration
```

## Next Steps

1. Test with actual user accounts
2. Verify jurisdiction rules work correctly
3. Test pagination with large datasets
4. Add frontend integration
5. Consider adding update/delete operations
6. Implement analytics/reporting features

## Support

For issues or questions:
1. Check the comprehensive documentation in `INSPECTION_API.md`
2. Review implementation details in `INSPECTION_IMPLEMENTATION.md`
3. Check existing similar patterns in `complaints.py` controller
