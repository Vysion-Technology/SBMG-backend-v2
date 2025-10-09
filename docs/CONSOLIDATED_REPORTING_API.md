# Consolidated Reporting API Documentation

## Overview

The consolidated reporting system provides a unified, optimized API for all user roles (VDO to ADMIN) with perfect Role-Based Access Control (RBAC) and optimized database queries.

## Key Features

- **Perfect RBAC**: Automatic jurisdiction filtering based on user roles
- **Optimized Queries**: Single queries with proper eager loading
- **Unified Interface**: One API serving all access levels
- **Advanced Filtering**: Date ranges, search, sorting, and geographic filters
- **Role-Specific Views**: Tailored data presentation for each user type

## Base URL

All endpoints are prefixed with: `/api/v1/reports/`

## Authentication

All endpoints (except public ones) require a valid JWT Bearer token:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Unified Dashboard
**GET** `/dashboard`

Get role-based dashboard statistics and recent complaints.

**Query Parameters:**
- `limit` (optional): Number of recent complaints (default: 10, max: 50)

**Access Levels:**
- **ADMIN**: System-wide statistics
- **CEO**: District-level statistics
- **BDO**: Block-level statistics  
- **VDO**: Village-level statistics
- **WORKER**: Personal task statistics

**Response:**
```json
{
  "total_complaints": 150,
  "complaints_by_status": {
    "OPEN": 45,
    "IN_PROGRESS": 30,
    "COMPLETED": 25,
    "VERIFIED": 50
  },
  "recent_complaints": [...],
  "geographic_summary": {
    "total_districts": 5,
    "total_blocks": 25,
    "total_villages": 150
  }
}
```

### 2. Advanced Complaint Listing
**GET** `/complaints`

Get complaints with advanced filtering and pagination.

**Query Parameters:**
- `district_id`, `block_id`, `village_id`: Geographic filters
- `status_name`: Filter by complaint status
- `complaint_type_id`: Filter by complaint type
- `assigned_worker_id`: Filter by assigned worker
- `date_from`, `date_to`: Date range filters (YYYY-MM-DD)
- `search`: Search in complaint descriptions
- `sort_by`: Sort field (created_at, updated_at, status)
- `sort_order`: Sort direction (asc, desc)
- `skip`, `limit`: Pagination

**RBAC Filtering:**
- Automatically restricts results based on user's jurisdiction
- ADMIN sees all complaints
- CEO sees district complaints
- BDO sees block complaints
- VDO sees village complaints
- WORKER sees assigned complaints only

### 3. Complaint Details
**GET** `/complaints/{complaint_id}`

Get detailed information about a specific complaint.

**Access Control:**
- Checks if user has permission to view the specific complaint
- Returns full details including media and assignment information

### 4. Worker Task Management
**GET** `/worker/tasks`

Get tasks assigned to the current worker (WORKER role only).

**Query Parameters:**
- `status_filter`: Filter tasks by status

**PATCH** `/worker/tasks/{complaint_id}/complete`

Mark a worker task as completed (WORKER role only).

**POST** `/worker/tasks/{complaint_id}/media`

Upload media for a worker task (WORKER role only).

### 5. VDO Verification
**PATCH** `/vdo/complaints/{complaint_id}/verify`

VDO verifies and closes a completed complaint (VDO role only).

**Requirements:**
- Complaint must be in COMPLETED status
- Complaint must be in VDO's jurisdiction

### 6. Admin Analytics
**GET** `/admin/analytics`

Get comprehensive system analytics (ADMIN role only).

**Response:**
```json
{
  "total_entities": {
    "complaints": 1500,
    "users": 75,
    "districts": 5,
    "blocks": 25,
    "villages": 150
  },
  "user_productivity": [...],
  "system_health": {
    "database_status": "healthy",
    "active_users": 75
  }
}
```

### 7. Public Status
**GET** `/public/status`

Public API to view complaint status (no authentication required).

**Features:**
- Limited information (no worker details, no media)
- Geographic filtering available
- Pagination support

### 8. User Access Information
**GET** `/user/access-info`

Get current user's access information and permissions.

**Response:**
```json
{
  "user_id": 123,
  "username": "john_doe",
  "access_summary": {
    "roles": ["VDO"],
    "jurisdictions": ["Village-45"],
    "is_admin": false,
    "access_level": "VDO"
  },
  "can_access_all_data": false,
  "positions": [...]
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "message": "Error description",
  "status_code": 403
}
```

## Performance Features

1. **Optimized Database Queries**:
   - Single queries with proper JOINs
   - Strategic use of `joinedload` and `selectinload`
   - Jurisdiction filtering at database level

2. **Efficient RBAC**:
   - Role-based filtering in SQL WHERE clauses
   - No application-level data filtering
   - Automatic jurisdiction detection

3. **Smart Caching Ready**:
   - Stateless design allows for easy caching
   - Predictable query patterns

## Migration from Legacy API

The new consolidated API maintains backward compatibility with the same base path `/api/v1/reports/`. Key differences:

1. **Better Performance**: Single optimized queries instead of multiple round trips
2. **Enhanced Filtering**: More filter options and better search capabilities  
3. **Unified Responses**: Consistent response formats across all endpoints
4. **Improved RBAC**: More precise permission checking

## Examples

### Get Dashboard for Current User
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/reports/dashboard
```

### Search Complaints with Filters
```bash
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/v1/reports/complaints?search=road&status_name=OPEN&limit=20"
```

### Worker Complete Task
```bash
curl -X PATCH \
     -H "Authorization: Bearer <worker_token>" \
     http://localhost:8000/api/v1/reports/worker/tasks/123/complete
```

### Public Status Check
```bash
curl http://localhost:8000/api/v1/reports/public/status?district_id=1&limit=10
```