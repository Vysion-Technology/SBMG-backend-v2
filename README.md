# SBM Gramin Rajasthan - Complaint Management System

A comprehensive complaint management system for Swachh Bharat Mission (Gramin) in Rajasthan, built with FastAPI, PostgreSQL, and MinIO.

## Features

### 🔐 Authentication & Authorization
- **JWT-based Authentication**: Secure token-based authentication with bcrypt password hashing
- **Role-based Access Control (RBAC)**: Six distinct user roles with hierarchical permissions
- **Geographical Access Control**: Users can only access data within their jurisdiction

### 👥 User Roles & Permissions

| Role | Description | Permissions |
|------|-------------|-------------|
| **ADMIN** | System Administrator | Full system access, can create/manage all users and data |
| **CEO** | District Collector | View/manage all data within their district |
| **BDO** | Block Development Officer | View/manage all data within their block |
| **VDO** | Village Development Officer | View/manage all data within their village, verify completed complaints |
| **WORKER** | Field Worker | View assigned complaints, update status, mark as completed |
| **PUBLIC** | Public Users | Create complaints, view complaint status (no authentication required) |

### 📋 Complaint Management
- **Public Complaint Creation**: Anyone can create complaints without authentication
- **Automatic Assignment**: Complaints get assigned to workers based on location
- **Status Tracking**: Complete workflow from creation to completion and verification
- **Comment System**: Staff can add comments to complaints for better tracking
- **Media Support**: Ready for file upload functionality with S3 integration

### 🏗️ Technical Architecture
- **Backend**: FastAPI with Python 3.12
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Storage**: MinIO (S3-compatible) for file storage
- **Authentication**: JWT tokens with configurable expiration
- **Deployment**: Docker Compose for easy setup

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for containers

### 1. Clone and Start Services

```bash
# Clone the repository
git clone https://github.com/AvanishCodes/SBMGRajasthan.git
cd SBMGRajasthan

# Start all services
docker compose up -d

# Check if services are running
docker compose ps
```

### 2. Initialize Default Data

```bash
# Wait for backend to be ready, then initialize default roles
curl -X POST "http://localhost:8000/api/v1/admin/init-default-data" \
     -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### 3. Access Services

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/minioadmin123)
- **PostgreSQL**: localhost:5432 (sbm_user/sbm_password)

## API Documentation

### Authentication Endpoints

#### Login
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

#### Get Current User
```bash
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Admin Endpoints (Admin Only)

#### Create User
```bash
POST /api/v1/admin/users
Authorization: Bearer <token>
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password",
  "is_active": true
}
```

#### Create Geography
```bash
# Create District
POST /api/v1/admin/districts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jaipur",
  "description": "Jaipur District"
}

# Create Block
POST /api/v1/admin/blocks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jaipur Block",
  "description": "Jaipur Block",
  "district_id": 1
}

# Create Village
POST /api/v1/admin/villages
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Sample Village",
  "description": "Sample Village",
  "block_id": 1,
  "district_id": 1
}
```

### Complaint Endpoints

#### Create Complaint (Public)
```bash
POST /api/v1/complaints/
Content-Type: application/json

{
  "complaint_type_id": 1,
  "village_id": 1,
  "block_id": 1,
  "district_id": 1,
  "description": "Road repair needed"
}
```

#### Update Complaint Status (Staff Only)
```bash
PATCH /api/v1/complaints/{id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status_name": "IN_PROGRESS"
}
```

### Reporting Endpoints

The reporting system provides role-based access to complaint data and task management functionality.

#### Worker Endpoints

##### Get Assigned Complaints
```bash
GET /api/v1/reports/worker/assigned-complaints
Authorization: Bearer <worker_token>
```

##### Upload Before/After Images
```bash
POST /api/v1/reports/worker/complaints/{complaint_id}/media
Authorization: Bearer <worker_token>
Content-Type: multipart/form-data

# Form data with file upload
file: [image file]
```

##### Mark Task as Completed
```bash
PATCH /api/v1/reports/worker/complaints/{complaint_id}/mark-done
Authorization: Bearer <worker_token>
```

#### VDO (Village Development Officer) Endpoints

##### Verify Completed Work
```bash
PATCH /api/v1/reports/vdo/complaints/{complaint_id}/verify
Authorization: Bearer <vdo_token>
```

##### Get Village Complaints
```bash
GET /api/v1/reports/vdo/village-complaints
Authorization: Bearer <vdo_token>
```

#### BDO/CEO/Admin Endpoints

##### Get Complaints by Jurisdiction
```bash
GET /api/v1/reports/complaints?district_id=1&status_name=OPEN&skip=0&limit=50
Authorization: Bearer <staff_token>

# Query Parameters:
# - district_id: Filter by district (optional)
# - block_id: Filter by block (optional)
# - village_id: Filter by village (optional)
# - status_name: Filter by status (optional)
# - skip: Number of records to skip (default: 0)
# - limit: Number of records to return (default: 100, max: 500)
```

##### Get Complaint Details
```bash
GET /api/v1/reports/complaints/{complaint_id}
Authorization: Bearer <staff_token>
```

#### Public Endpoints

##### Get All Complaints Status
```bash
GET /api/v1/reports/public/complaints-status?village_id=1&skip=0&limit=100

# Query Parameters:
# - district_id: Filter by district (optional)
# - block_id: Filter by block (optional)
# - village_id: Filter by village (optional)
# - skip: Number of records to skip (default: 0)
# - limit: Number of records to return (default: 100, max: 500)
```

#### Response Models

##### Worker Assigned Complaint Response
```json
{
  "id": 1,
  "description": "Road repair needed",
  "status_name": "ASSIGNED",
  "village_name": "Sample Village",
  "block_name": "Jaipur Central",
  "district_name": "Jaipur",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z",
  "media_urls": [
    "/media/complaints/1/before.jpg",
    "/media/complaints/1/after.jpg"
  ]
}
```

##### Complaint List Response
```json
{
  "id": 1,
  "description": "Road repair needed",
  "status_name": "COMPLETED",
  "village_name": "Sample Village",
  "block_name": "Jaipur Central", 
  "district_name": "Jaipur",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T16:45:00Z",
  "assigned_worker": "worker1"
}
```

##### Public Complaint Status Response
```json
{
  "id": 1,
  "description": "Road repair needed",
  "status_name": "VERIFIED",
  "village_name": "Sample Village",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Development Setup

### Local Development (without Docker)

1. **Install Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Setup Environment**
```bash
# Create .env file
DATABASE_URL=sqlite+aiosqlite:///./test.db
SECRET_KEY=your-secret-key
DEBUG=true
```

3. **Run Application**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Management

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations:

```bash
# Initialize Alembic (if needed)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial tables"

# Apply migration
alembic upgrade head
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite+aiosqlite:///./test.db` |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration | `30` |
| `S3_ENDPOINT_URL` | MinIO endpoint | `http://minio:9000` |
| `S3_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `S3_SECRET_KEY` | MinIO secret key | `minioadmin123` |
| `DEBUG` | Debug mode | `false` |

## Project Structure

```
├── backend/
│   ├── controllers/         # API route handlers
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── database/           # Database configuration
│   ├── config.py           # Application settings
│   ├── auth_utils.py       # Authentication utilities
│   ├── main.py             # FastAPI application
│   └── requirements.txt    # Python dependencies
├── docker-compose.yml      # Multi-container setup
├── init-db/               # Database initialization scripts
└── README.md              # This file
```

## Workflow Examples

### 1. Admin Creates Users and Assigns Positions

```bash
# 1. Admin logs in
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'

# 2. Create a VDO user
curl -X POST "http://localhost:8000/api/v1/admin/users" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"username": "vdo1", "email": "vdo@example.com", "password": "password"}'

# 3. Assign VDO position to user
curl -X POST "http://localhost:8000/api/v1/admin/position-holders" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 2,
       "role_name": "VDO",
       "first_name": "John",
       "last_name": "Doe",
       "village_id": 1
     }'
```

### 2. Public User Creates Complaint

```bash
# Public user creates complaint (no authentication needed)
curl -X POST "http://localhost:8000/api/v1/complaints/" \
     -H "Content-Type: application/json" \
     -d '{
       "complaint_type_id": 1,
       "village_id": 1,
       "block_id": 1,
       "district_id": 1,
       "description": "Broken streetlight near school"
     }'
```

### 3. Worker Updates Complaint Status

```bash
# 1. Worker logs in
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "worker1", "password": "password"}'

# 2. Update complaint status
curl -X PATCH "http://localhost:8000/api/v1/complaints/1/status" \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"status_name": "COMPLETED"}'
```

### 4. Worker Complete Task Workflow (New Reporting APIs)

```bash
# 1. Worker logs in and sees assigned complaints
curl -X GET "http://localhost:8000/api/v1/reports/worker/assigned-complaints" \
     -H "Authorization: Bearer <worker_token>"

# 2. Worker uploads before image
curl -X POST "http://localhost:8000/api/v1/reports/worker/complaints/1/media" \
     -H "Authorization: Bearer <worker_token>" \
     -F "file=@before_image.jpg"

# 3. Worker completes the task and uploads after image
curl -X POST "http://localhost:8000/api/v1/reports/worker/complaints/1/media" \
     -H "Authorization: Bearer <worker_token>" \
     -F "file=@after_image.jpg"

# 4. Worker marks task as completed
curl -X PATCH "http://localhost:8000/api/v1/reports/worker/complaints/1/mark-done" \
     -H "Authorization: Bearer <worker_token>"
```

### 5. VDO Verification Workflow

```bash
# 1. VDO logs in and sees all village complaints
curl -X GET "http://localhost:8000/api/v1/reports/vdo/village-complaints" \
     -H "Authorization: Bearer <vdo_token>"

# 2. VDO views specific complaint details with media
curl -X GET "http://localhost:8000/api/v1/reports/complaints/1" \
     -H "Authorization: Bearer <vdo_token>"

# 3. VDO verifies completed work and closes complaint
curl -X PATCH "http://localhost:8000/api/v1/reports/vdo/complaints/1/verify" \
     -H "Authorization: Bearer <vdo_token>"
```

### 6. Management Reporting

```bash
# BDO views all complaints in their block
curl -X GET "http://localhost:8000/api/v1/reports/complaints?block_id=1&limit=50" \
     -H "Authorization: Bearer <bdo_token>"

# CEO views all complaints in their district filtered by status
curl -X GET "http://localhost:8000/api/v1/reports/complaints?district_id=1&status_name=COMPLETED" \
     -H "Authorization: Bearer <ceo_token>"

# Public user checks complaint status
curl -X GET "http://localhost:8000/api/v1/reports/public/complaints-status?village_id=1"
```

## Production Deployment

### Security Considerations

1. **Change Default Credentials**: Update all default passwords and keys
2. **Use HTTPS**: Configure SSL certificates
3. **Network Security**: Use private networks and firewalls
4. **Database Security**: Use strong passwords and connection encryption
5. **Environment Variables**: Use secure secret management

### Scaling Considerations

1. **Database**: Use managed PostgreSQL service
2. **Storage**: Use managed S3 service or distributed MinIO
3. **Application**: Use multiple backend instances with load balancer
4. **Caching**: Add Redis for session management and caching

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper tests
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Contact: avanish.sde@gmail.com

---

**SBM Gramin Rajasthan** - Empowering clean and efficient complaint management for rural development.