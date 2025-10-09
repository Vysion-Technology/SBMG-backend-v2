# SUPERADMIN Role Implementation

## Overview
A new **SUPERADMIN** role has been added to the system with the highest level of privileges. SUPERADMIN can do everything that ADMIN can do and is positioned at the top of the role hierarchy.

## Changes Made

### 1. Backend - Role Enum (`backend/auth_utils.py`)
- Added `SUPERADMIN = "SUPERADMIN"` to the `UserRole` enum as the first role (highest priority)
- Updated role hierarchy: `SUPERADMIN > ADMIN > CEO > BDO > VDO > WORKER > PUBLIC`

### 2. Backend - Permission Functions (`backend/auth_utils.py`)
Created new permission function:
- `require_superadmin()` - Requires only SUPERADMIN role

Updated existing permission functions to include SUPERADMIN:
- `require_admin()` - Now accepts both SUPERADMIN and ADMIN
- `require_admin_or_ceo()` - Now accepts SUPERADMIN, ADMIN, and CEO
- `require_admin_or_ceo_or_bdo()` - Now accepts SUPERADMIN, ADMIN, CEO, and BDO
- `require_staff_role()` - Now includes SUPERADMIN in staff roles

### 3. Backend - Init Data API (`backend/controllers/admin.py`)
- Added `UserRole.SUPERADMIN` to the `default_roles` list in the `/init-default-data` endpoint
- The SUPERADMIN role will be automatically created when initializing the system

### 4. Backend - Init Script (`init_app.py`)
- Added SUPERADMIN role to the default roles list: `("SUPERADMIN", "Super Administrator with full system access")`
- SUPERADMIN role will be created when running the initialization script

### 5. Frontend - Role Precedence (`frontend/src/utils.ts`)
- Updated `ROLE_PRECEDENCE` array to: `['SUPERADMIN', 'ADMIN', 'CEO', 'BDO', 'VDO']`
- Updated `userHasAdminPrivileges()` to include SUPERADMIN in admin privileges check

### 6. Documentation Updates
- **README.md**: Updated user roles table to include SUPERADMIN with 7 distinct roles (was 6)
- **USER_MANAGEMENT.md**: Added SUPERADMIN to the list of supported roles

## Role Hierarchy

```
SUPERADMIN (Highest)
    ↓
  ADMIN
    ↓
   CEO
    ↓
   BDO
    ↓
   VDO
    ↓
  WORKER
    ↓
  PUBLIC (Lowest)
```

## Creating a SUPERADMIN User

### Option 1: Using the Init Data API
```bash
# Call the init endpoint (creates SUPERADMIN role if it doesn't exist)
curl -X POST http://localhost:8000/api/v1/admin/init-default-data
```

### Option 2: Using the Init Script
```bash
# Run the initialization script
cd /path/to/project
python init_app.py
```

### Option 3: Manual Creation via API
1. First, ensure SUPERADMIN role exists (via init endpoints)
2. Create user via User Management API with `role_name: "SUPERADMIN"`

## API Endpoints Using SUPERADMIN

All endpoints that previously required `@require_admin` now accept both SUPERADMIN and ADMIN roles automatically. No changes needed to existing API endpoints.

### Example Protected Endpoints:
- `POST /api/v1/admin/roles` - Create new role (SUPERADMIN or ADMIN)
- `POST /api/v1/admin/users` - Create new user (SUPERADMIN or ADMIN)
- `POST /api/v1/user-management/roles` - Role management (SUPERADMIN or ADMIN)
- All admin endpoints automatically grant access to SUPERADMIN

## Frontend Changes

The frontend role precedence system now recognizes SUPERADMIN as the highest priority role:
- When a user has multiple roles, SUPERADMIN will be selected as their primary role
- Admin privilege checks now include SUPERADMIN
- All admin UI features are available to SUPERADMIN users

## Testing

To verify SUPERADMIN implementation:

1. **Initialize the database**:
   ```bash
   python init_app.py
   # OR
   curl -X POST http://localhost:8000/api/v1/admin/init-default-data
   ```

2. **Verify SUPERADMIN role exists**:
   ```bash
   curl -H "Authorization: Bearer <token>" \
        http://localhost:8000/api/v1/user-management/roles
   ```

3. **Create a SUPERADMIN user**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/user-management/users \
        -H "Authorization: Bearer <admin-token>" \
        -H "Content-Type: application/json" \
        -d '{
          "role_name": "SUPERADMIN",
          "first_name": "Super",
          "last_name": "Admin",
          "password": "secure_password"
        }'
   ```

4. **Test SUPERADMIN permissions**:
   - Login with SUPERADMIN credentials
   - Verify access to all admin endpoints
   - Verify access to all admin UI features

## Backward Compatibility

✅ All existing functionality remains unchanged
✅ Existing ADMIN users retain all their permissions
✅ SUPERADMIN simply adds a higher tier with the same permissions as ADMIN
✅ No breaking changes to existing code or APIs
