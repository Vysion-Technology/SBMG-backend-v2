# Segregated User Management System

This document describes the segregated user management architecture implemented in the SBM Gramin Rajasthan backend system.

## Architecture Overview

The system has been architected to separate **Login User Management** from **Person User Management** while maintaining the existing database structure. This segregation provides clear separation of concerns and better maintainability.

### Key Concepts

1. **Login User Management**: Handles authentication, credentials, and login-related operations
2. **Person User Management**: Handles person profiles, roles, designations, and position assignments
3. **Position Transfer**: Allows transferring designations between different persons while maintaining historical records

## Database Design (Existing Structure Maintained)

The system uses the existing database tables without any schema changes:

- `users` - Login credentials and authentication
- `position_holders` (renamed from `user_position_holders`) - Person profiles with position assignments
- `roles` - Role definitions (VDO, BDO, CEO, Worker, Admin)

### Key Relationships

- Each `User` record represents a login account
- Each `PositionHolder` record represents a person holding a specific designation
- One User can have multiple PositionHolder records (historical positions)
- Position transfers are tracked by ending one PositionHolder record and creating a new one

## API Endpoints

### Login User Management (`/api/v1/login-management`)

#### Authentication
- `POST /login` - Authenticate and get JWT token
- `GET /me` - Get current user info

#### User Account Management (Admin only)
- `POST /users` - Create login user
- `GET /users` - List all login users
- `GET /users/{user_id}` - Get specific user
- `PUT /users/{user_id}` - Update login credentials
- `POST /users/{user_id}/activate` - Activate user
- `POST /users/{user_id}/deactivate` - Deactivate user

#### Password Management
- `POST /change-password` - Change own password
- `POST /users/{user_id}/reset-password` - Admin reset password

### Person Management (`/api/v1/person-management`)

#### Role Management
- `POST /roles` - Create role (Admin only)
- `GET /roles` - List all roles
- `GET /roles/{role_id}` - Get specific role
- `PUT /roles/{role_id}` - Update role (Admin only)

#### Person Management
- `POST /persons` - Create person with position and login
- `GET /persons` - List persons with filters
- `GET /persons/{person_id}` - Get specific person
- `PUT /persons/{person_id}` - Update person info
- `GET /persons/search` - Search persons by name

#### Position Management & History
- `POST /persons/{person_id}/transfer` - Transfer position to another person
- `GET /positions/history` - Get historical position assignments
- `GET /users/{user_id}/positions` - Get all positions held by a user

## Usage Examples

### 1. Create a New Person with Position

```http
POST /api/v1/person-management/persons
Content-Type: application/json
Authorization: Bearer {token}

{
  "role_name": "VDO",
  "first_name": "John",
  "last_name": "Doe",
  "middle_name": "Kumar",
  "start_date": "2024-01-01",
  "district_id": 1,
  "block_id": 5,
  "village_id": 25,
  "password": "initial_password"
}
```

### 2. Transfer a Position

```http
POST /api/v1/person-management/persons/123/transfer
Content-Type: application/json
Authorization: Bearer {token}

{
  "new_user_id": 456,
  "transfer_date": "2024-06-01",
  "new_first_name": "Jane",
  "new_last_name": "Smith",
  "new_middle_name": "Kumari"
}
```

### 3. Get Position History

```http
GET /api/v1/person-management/positions/history?role_id=2&district_id=1&from_date=2024-01-01
Authorization: Bearer {token}
```

### 4. Login and Authentication

```http
POST /api/v1/login-management/login
Content-Type: application/json

{
  "username": "district1.block5.village25@example.com",
  "password": "user_password"
}
```

## Service Layer Architecture

### LoginUserService
- **Purpose**: Handle authentication and login credentials
- **Key Methods**:
  - `authenticate_user()` - Validate credentials
  - `create_access_token()` - Generate JWT tokens
  - `create_login_user()` - Create login accounts
  - `update_login_credentials()` - Update username/password/email
  - `change_password()` - Change user password

### PersonManagementService
- **Purpose**: Handle person profiles and position management
- **Key Methods**:
  - `create_position_holder()` - Create person with position
  - `transfer_position()` - Transfer position between persons
  - `get_position_history()` - Get historical assignments
  - `search_persons_by_name()` - Search functionality
  - `generate_username()` - Create location-based usernames

## Benefits of Segregated Architecture

### 1. **Clear Separation of Concerns**
- Authentication logic separated from business logic
- Login management independent of person profiles
- Better maintainability and testability

### 2. **Historical Tracking**
- Complete history of who held which position when
- Position transfers maintain audit trail
- Easy reporting on position assignments over time

### 3. **Flexible Assignment**
- Same login can hold different positions over time
- Positions can be transferred between different persons
- Support for temporary assignments and role changes

### 4. **Better Security**
- Login credentials managed separately from profile data
- Granular permissions for different operations
- Separate endpoints for authentication vs. profile management

### 5. **Scalability**
- Services can be scaled independently
- Clear API boundaries for different concerns
- Easier to add new features to specific domains

## Security Considerations

### Authentication
- JWT tokens for stateless authentication
- Password hashing using Argon2
- Token expiration and refresh mechanisms

### Authorization
- Role-based access control maintained
- Admin-only operations clearly marked
- Geographic-based permissions where applicable

### Data Protection
- Login credentials encrypted
- Audit trails for position changes
- Secure password reset functionality

## Migration from Legacy System

The system maintains backward compatibility by:

1. **Keeping existing database schema** - No structural changes required
2. **Legacy endpoints available** - Old `/api/v1/user-management` still works
3. **Gradual migration path** - Can migrate endpoints one by one
4. **Same authentication** - Existing JWT tokens continue to work

## Future Enhancements

### Planned Features
1. **Email notifications** for position transfers
2. **Bulk import/export** of person data
3. **Advanced reporting** dashboard
4. **Mobile app integration** with segregated APIs
5. **Audit logging** for all changes

### Technical Improvements
1. **Caching layer** for frequently accessed data
2. **Database optimization** for historical queries
3. **API versioning** for backward compatibility
4. **Automated testing** suite for all endpoints

## Frontend Integration

The segregated APIs are designed to support clear frontend separation:

### Login Management Frontend
- Login/logout screens
- Password management
- User account administration
- Session management

### Person Management Frontend
- Person profile management
- Role assignment interfaces
- Position transfer workflows
- Historical reporting views
- Search and filtering capabilities

### Shared Components
- Navigation and routing
- Common UI components
- Authentication state management
- Error handling and notifications

This architecture provides a solid foundation for building a maintainable, scalable user management system that clearly separates authentication from business logic while maintaining complete historical tracking of organizational changes.