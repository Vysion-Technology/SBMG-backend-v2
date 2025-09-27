# RBAC Implementation Guide - SBMG Frontend v2

## Overview

This document describes the Role-Based Access Control (RBAC) implementation in the updated frontend application for the Swachh Bharat Mission - Gramin Rajasthan complaint management system.

## User Roles and Permissions

### 1. Public Users (Citizens)
- **No authentication required**
- **Capabilities:**
  - Create complaints with or without media
  - Track complaint status using complaint ID
  - Verify complaint resolution status
  - Access all public information

### 2. ADMIN
- **Highest level access**
- **Capabilities:**
  - Full system administration
  - User management (create, update, delete users)
  - Role management
  - System configuration
  - Access to advanced analytics
  - View all complaints across the system
  - Geography management (districts, blocks, villages)

### 3. CEO (Chief Executive Officer)
- **District-level management**
- **Capabilities:**
  - View all complaints within their district
  - User management within district
  - District-level analytics and reporting
  - Monitor performance across blocks

### 4. BDO (Block Development Officer)
- **Block-level management**
- **Capabilities:**
  - View all complaints within their block
  - Monitor VDO and Worker performance
  - Block-level analytics
  - Assign complaints to workers

### 5. VDO (Village Development Officer)
- **Village-level management**
- **Capabilities:**
  - View complaints within their village
  - Verify completed complaints
  - Close complaints with resolution comments
  - Upload resolution media
  - Manage worker assignments in their village

### 6. WORKER
- **Task execution level**
- **Capabilities:**
  - View assigned complaints only
  - Update complaint status (start work, mark completed)
  - Upload progress images
  - Add comments to complaints
  - Cannot resolve or close complaints

## RBAC UI Controls

### Navigation Menu
- **Dynamic menu items** based on user role
- **Role-specific dashboards:**
  - Admin → Admin Dashboard, Admin Panel, User Management
  - CEO/BDO → Admin Dashboard, User Management
  - VDO → VDO Dashboard
  - Worker → Worker Tasks
- **Public items** always visible (Create Complaint, Check Status)

### HomePage Personalization
- **Authenticated users** see role-specific quick actions
- **Guest users** see public service options
- **Welcome message** shows username and role
- **Contextual guidance** based on user permissions

### Component-Level RBAC

#### WorkerDashboard
- **Permission checks** for each action:
  - `canUploadMedia()` - Workers/VDOs for IN_PROGRESS/ASSIGNED tasks
  - `canMarkCompleted()` - Workers for ASSIGNED/IN_PROGRESS tasks  
  - `canResolveComplaint()` - VDOs for COMPLETED tasks
- **Dynamic action buttons** based on permissions
- **Status-based controls** prevent invalid state transitions

#### Dashboard
- **Data scoping** based on user jurisdiction
- **Role-based statistics** showing relevant metrics
- **Filtered complaint lists** respecting access boundaries

#### UserManagement
- **Admin/CEO only** access control
- **Hierarchical user creation** within jurisdiction
- **Role assignment** restrictions based on current user role

## API Integration

### Consolidated Reporting Endpoints
- **`/reports/dashboard`** - Role-scoped dashboard statistics
- **`/reports/complaints`** - Advanced filtering with automatic jurisdiction filtering
- **`/reports/worker/tasks`** - Worker-specific task management
- **`/reports/admin/analytics`** - Admin-only advanced analytics

### Permission Validation
- **Client-side prevention** of invalid actions
- **Server-side enforcement** as backup
- **User-friendly error messages** when actions are blocked

## Combined Operations

### Complaint Resolution with Media
- **Single-page workflow** for VDOs to resolve complaints
- **Optional media upload** with resolution comments
- **Atomic operation** ensures data consistency

### Comment with Image
- **Workers can add progress comments** with optional images
- **Combined API call** reduces network overhead
- **Real-time status updates** after successful operations

## User Experience Enhancements

### Better Validation
- **Client-side validation** prevents server errors
- **Mobile number format** validation (Indian format)
- **Location hierarchy** validation (District → Block → Village)
- **Minimum description length** requirements

### Improved Feedback
- **Success messages** with complaint IDs and next steps
- **SMS notification** guidance when mobile number provided
- **Progress tracking** with visual indicators
- **Recent searches** for quick access

### Status Visualization
- **Color-coded status** indicators
- **Progress bars** showing completion percentage
- **Status icons** for quick visual identification
- **Timeline representation** of complaint lifecycle

## Security Features

### Authentication Flow Separation
- **Public access** for citizen services
- **Staff authentication** for internal operations
- **Role-based routing** after login
- **Token-based session** management

### Data Protection
- **Jurisdiction filtering** prevents data leakage
- **Permission checks** before sensitive operations
- **Input sanitization** and validation
- **Error message** sanitization to prevent information disclosure

## Development Guidelines

### Adding New RBAC Controls
1. **Define permission check functions** in component
2. **Use role information** from user context
3. **Implement server-side validation** as backup
4. **Provide clear user feedback** when access is denied

### Testing RBAC
1. **Test with different user roles** (ADMIN, CEO, BDO, VDO, WORKER)
2. **Verify jurisdiction boundaries** are respected
3. **Confirm UI elements** show/hide correctly
4. **Test error scenarios** and user feedback

### Best Practices
- **Always validate on server** - client-side is UX only
- **Graceful degradation** when permissions are insufficient
- **Clear error messages** explaining why action is blocked
- **Consistent UI patterns** across role-based features

## Configuration

### User Role Hierarchy
```
ADMIN (System-wide)
├── CEO (District-level)
│   ├── BDO (Block-level)
│   │   ├── VDO (Village-level)
│   │   │   └── WORKER (Task-level)
```

### Permission Matrix
| Action | ADMIN | CEO | BDO | VDO | WORKER | PUBLIC |
|--------|--------|-----|-----|-----|---------|---------|
| Create Complaint | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Complaints | ✅ | District | Block | Village | Assigned | ❌ |
| Manage Users | ✅ | District | ❌ | ❌ | ❌ | ❌ |
| Assign Complaints | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Upload Media | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Resolve Complaints | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| System Analytics | ✅ | District | Block | Village | ❌ | ❌ |

## Troubleshooting

### Common Issues
1. **User sees "Access Denied"** - Check role assignments and jurisdiction
2. **Missing UI elements** - Verify RBAC component logic
3. **Data not loading** - Confirm API permissions and filters
4. **Actions disabled** - Check permission functions and user state

### Debug Steps
1. **Check user object** in browser console
2. **Verify API responses** in Network tab
3. **Test permission functions** with different user roles
4. **Review server logs** for authorization errors

## Future Enhancements

### Planned Features
- **Granular permissions** beyond role-based
- **Time-based access** controls
- **Delegation mechanisms** for temporary permissions
- **Audit trail** for all RBAC decisions
- **Role-based dashboards** with configurable widgets