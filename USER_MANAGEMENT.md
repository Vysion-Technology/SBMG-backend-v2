# User Management System Documentation

## Overview

This document describes the comprehensive user management system implemented for the SBM Gramin Rajasthan project. The system allows creating and managing users with different roles and their geographical assignments.

## Key Features

### 1. Role-Based User Creation
The system supports creating users with the following roles:
- **CEO** (District Collector)
- **BDO** (Block Development Officer)  
- **VDO** (Village Development Officer)
- **WORKER** (Contractor Worker)
- **ADMIN** (System Administrator)

### 2. Geography-Based Username Generation
Usernames are automatically generated based on the user's role and geographical assignment:

- **CEO**: `district@example.com`
- **BDO**: `district.block@example.com`
- **VDO**: `district.block.village@example.com`
- **WORKER**: `district.block.village-sbmg-contractor@example.com`

Examples:
- CEO for "Jaipur" district: `jaipur@example.com`
- BDO for "Sanganer" block in "Jaipur" district: `jaipur.sanganer@example.com`
- VDO for "Bagru" village in "Sanganer" block, "Jaipur" district: `jaipur.sanganer.bagru@example.com`
- Worker for contractor "ABC Sanitation" in "Bagru" village: `jaipur.sanganer.bagru-sbmg-abc-sanitation@example.com`

### 3. Permission System
- **ADMIN**: Can create roles and users, update all user fields including critical information (name, date of joining)
- **CEO**: Can create users within their district, update non-critical fields
- **Other roles**: Can view and update limited information based on their geographical scope

## Backend Implementation

### Database Schema

#### Enhanced PositionHolder Model
Added `date_of_joining` field to track when a user joined their position:
```python
class PositionHolder(Base):
    # ... existing fields ...
    date_of_joining: Mapped[Optional[str]] = mapped_column(String, nullable=True)
```

#### Migration
Created Alembic migration to add the `date_of_joining` column:
```sql
ALTER TABLE user_position_holders ADD COLUMN date_of_joining VARCHAR;
```

### API Endpoints

#### Role Management (`/api/v1/user-management/roles`)
- **POST /** - Create new role (Admin only)
- **GET /** - Get all roles
- **GET /{id}** - Get role by ID
- **PUT /{id}** - Update role (Admin only)

#### User Management (`/api/v1/user-management`)
- **POST /users** - Create user with position (Admin/CEO only)
- **GET /position-holders** - Get all position holders (filtered by permissions)
- **GET /position-holders/{id}** - Get specific position holder
- **PUT /position-holders/{id}** - Update position holder

### Services

#### UserManagementService
- `generate_username()` - Automatically generates usernames based on role and geography
- `create_user_with_position()` - Creates user account and position holder in one transaction
- `create_role()`, `update_role()` - Role management
- `update_position_holder()` - Updates position with admin/non-admin field restrictions

### Authorization Rules

#### Field Update Permissions
- **Critical fields** (name, date of joining): Admin only
- **General fields** (start/end dates): All authorized users
- **Geographic access**: Users can only manage positions within their geographical scope

## Frontend Implementation

### UserManagement Component (`/user-management`)

#### Features
1. **Tabbed Interface**:
   - Users & Position Holders tab (available to all authorized users)
   - Roles Management tab (Admin only)

2. **User Creation Form**:
   - Role selection dropdown
   - Personal information (first name, middle name, last name, DOJ)
   - Geographic assignment (district, block, village)
   - Contractor name (for Worker role)
   - Optional password (defaults to system-generated)
   - Position dates (start/end)

3. **Position Holder Management**:
   - View all position holders in tabular format
   - Edit functionality with permission-based field restrictions
   - Geographic filtering based on user permissions

4. **Role Management** (Admin only):
   - Create new roles
   - View existing roles
   - Update role information

### Navigation Integration
- Added "User Management" navigation item for Admin and CEO users
- Integrated with existing authentication and authorization system

## Usage Workflow

### Creating a New User

1. **Admin/CEO** navigates to User Management
2. Clicks "Create New User" button
3. Fills out the form:
   - Selects role from dropdown
   - Enters personal information
   - Selects geographical assignment
   - For Workers: enters contractor name
   - Sets position dates
4. System automatically:
   - Generates appropriate username/email
   - Creates user account with default password
   - Creates position holder record
   - Links to geographical entities

### Managing Existing Users

1. View position holders in the table
2. Click "Edit" on any position
3. Update fields based on permissions:
   - **Admin**: Can edit all fields
   - **Others**: Can only edit start/end dates
4. Changes are saved with appropriate authorization checks

## Security Considerations

1. **Role-based Access Control**: Only authorized users can access user management features
2. **Geographic Scope Limitation**: Users can only manage positions within their assigned geography
3. **Critical Field Protection**: Name and DOJ changes require admin privileges
4. **Automatic Username Generation**: Prevents username conflicts and maintains consistency
5. **Default Password Policy**: System generates secure default passwords that should be changed on first login

## Technical Benefits

1. **Consistency**: Automated username generation ensures consistent naming convention
2. **Scalability**: Geographic-based permissions allow delegation of user management
3. **Auditability**: Tracks position changes and maintains history
4. **Integration**: Seamlessly integrates with existing authentication and complaint management systems
5. **User Experience**: Intuitive interface with clear permission boundaries

## Future Enhancements

1. **Password Reset**: Implement password reset functionality for created users
2. **Bulk Import**: Allow bulk user creation via CSV upload
3. **User Deactivation**: Soft delete functionality for user accounts
4. **Audit Trail**: Detailed logging of user management actions
5. **Email Notifications**: Send credentials to newly created users
6. **Position Transfer**: Allow transferring users between geographical locations