# Frontend Application v2 - Updates Documentation

## Overview
This document describes the updates made to the frontend application to integrate with the v2 backend APIs.

## Major Changes

### 1. API Layer Updates (`src/api.ts`)

#### New Authentication Endpoints
- `authApi.sendOTP(mobileNumber)` - Send OTP to citizen's mobile
- `authApi.verifyOTP(mobileNumber, otp)` - Verify OTP and get citizen token

#### Updated Endpoints
All endpoints have been updated to match the v2 backend structure:

- **Geography APIs**: Now use `/api/v1/geography/*` instead of `/api/v1/public/*`
- **Dashboard**: Uses `/api/v1/reports/dashboard` (consolidated reporting)
- **Staff Complaints**: Uses `/api/v1/reports/complaints` with advanced filtering
- **Worker Tasks**: Uses `/api/v1/reports/worker/tasks`
- **Citizen Complaints**: Uses `/api/v1/citizen/with-media` with token header

#### New APIs Added
- `staffApi.addComplaintComment()` - Workers/VDOs can add comments with optional photo
- `staffApi.verifyComplaint()` - VDO can verify completed complaints with comment and media

### 2. Citizen Authentication Flow

#### New Component: `CitizenLogin.tsx`
- OTP-based authentication for citizens
- Step 1: Enter mobile number and send OTP
- Step 2: Enter OTP and verify
- Stores citizen token in localStorage as `citizen_token`
- Stores mobile number in localStorage as `citizen_mobile`

#### Updated Component: `CreateComplaint.tsx`
- Now requires citizen authentication before creating complaints
- Shows login prompt if user is not authenticated
- Automatically includes citizen token in API requests

### 3. Type System Updates (`src/types.ts`)

#### Updated Types
- `Complaint` - Added fields: `complaint_type_name`, `assigned_worker_name`, `media_count`
- `DashboardStats` - Completely restructured to match v2 API:
  - Changed `complaints_by_status` from array to dictionary
  - Added optional `geographic_summary` and `performance_metrics`
  - Removed individual counters (now in sub-objects)

### 4. Dashboard Updates (`src/components/Dashboard.tsx`)

Updated to work with new consolidated reporting API structure:
- Uses dictionary-based `complaints_by_status` instead of array
- Geographic data now comes from `geographic_summary` object
- Handles optional fields gracefully
- No breaking changes for non-admin users

### 5. Component Updates

#### `CitizenComplaintVerification.tsx`
- Removed mobile verification feature (not in backend)
- Simplified to just fetch and display complaint details
- Removed unused imports

## Authentication Flow

### Citizen (Public User)
1. Navigate to `/citizen-login`
2. Enter mobile number
3. Receive and enter OTP
4. Get authenticated with citizen token
5. Can create complaints at `/create-complaint`

### Staff Member (VDO, Worker, BDO, CEO, Admin)
1. Navigate to `/login`
2. Enter username and password
3. Get authenticated with JWT token
4. Redirected to appropriate dashboard based on role

## API Authentication

### Public/Citizen APIs
Use custom header `token` with citizen token:
```typescript
headers: { 'token': citizenToken }
```

### Staff APIs
Use standard Bearer token in Authorization header:
```typescript
headers: { 'Authorization': `Bearer ${jwtToken}` }
```

## RBAC in Frontend

The frontend enforces RBAC through:
1. Route guards in `App.tsx`
2. Conditional rendering based on user roles
3. API-level authentication

### Role-based Routes
- `/dashboard` - Admin, CEO, BDO only
- `/worker-dashboard` - Workers only
- `/user-dashboard` - VDOs and other staff
- `/admin` - Admin only
- `/user-management` - Admin and CEO only

## Pending Enhancements

### VDO Verification Workflow
While the API endpoint exists (`staffApi.verifyComplaint()`), the UI workflow for VDO verification of completed complaints can be further enhanced:

1. Add filter in UserDashboard for "COMPLETED" status complaints
2. Show "Verify" button for VDO role users
3. Verification form with:
   - Comment field (required)
   - Media upload (optional)
   - Submit button

Example implementation:
```typescript
const handleVerify = async (complaintId: number, comment: string, media?: File) => {
  try {
    await staffApi.verifyComplaint(complaintId, comment, media);
    // Refresh complaint list
  } catch (error) {
    // Handle error
  }
};
```

### Worker Comment/Photo Workflow
The `staffApi.addComplaintComment()` API is available but not yet integrated in the WorkerDashboard UI. Can be added as:

1. "Add Comment" button on each complaint
2. Modal/form with comment text area and photo upload
3. Submit to update complaint with comment

## Testing Recommendations

### Manual Testing
1. **Citizen Flow**
   - Test OTP send and verify
   - Create complaint with authentication
   - Track complaint status

2. **Worker Flow**
   - Login as worker
   - View assigned tasks
   - Upload media
   - Mark complaint as done

3. **VDO Flow**
   - Login as VDO
   - View complaints in village
   - Verify completed complaints

4. **Admin Flow**
   - View dashboard statistics
   - Access all complaints
   - Manage users

### API Testing
Test all endpoints with correct authentication headers and verify responses match expected types.

## Migration Notes

### Breaking Changes
1. `DashboardStats` interface changed - update any code using this type
2. Citizen complaints now require authentication - users must login first
3. Geography endpoints moved from `/public/*` to `/geography/*`

### Backward Compatibility
- Existing complaint tracking still works via public endpoints
- Staff authentication remains unchanged
- No data migration needed

## Environment Configuration

Update `.env` or configuration if API base URL changes:
```typescript
const API_BASE_URL = 'http://localhost:8000/api/v1';
```

For production, update to production backend URL.

## Build and Deploy

```bash
# Install dependencies
npm install

# Development
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## Conclusion

The frontend is now fully compatible with the v2 backend APIs with:
- ✅ Citizen OTP authentication
- ✅ Updated API endpoints
- ✅ Consolidated reporting integration
- ✅ Type safety maintained
- ✅ RBAC enforcement
- ✅ Builds without errors

The application is production-ready with clear paths for future enhancements.
