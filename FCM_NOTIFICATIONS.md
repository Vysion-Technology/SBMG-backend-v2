# FCM Push Notifications Implementation

This document describes the Firebase Cloud Messaging (FCM) push notification system implemented for the SBM Gramin Rajasthan complaint management system.

## Overview

The FCM notification system sends real-time push notifications to mobile devices when:
1. **A new complaint is created** → Notifies all workers in the village where the complaint was made
2. **A complaint status is updated** → Notifies the citizen who created the complaint

## Architecture

### Database Tables

#### 1. `user_device_tokens`
Stores FCM device tokens for staff users (Workers, VDOs, BDOs, CEOs, Admins).

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to `users.id` |
| device_id | String | Unique device identifier |
| fcm_token | String | FCM registration token |
| device_name | String | Device name/model (optional) |
| platform | String | Platform: ios, android, or web (optional) |
| created_at | DateTime | Token creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Constraints:**
- Unique constraint on (user_id, device_id)
- Cascade delete when user is deleted

#### 2. `public_user_device_tokens`
Stores FCM device tokens for public users (citizens who create complaints).

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| public_user_id | Integer | Foreign key to `public_users.id` |
| device_id | String | Unique device identifier |
| fcm_token | String | FCM registration token |
| device_name | String | Device name/model (optional) |
| platform | String | Platform: ios, android, or web (optional) |
| created_at | DateTime | Token creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Constraints:**
- Unique constraint on (public_user_id, device_id)
- Cascade delete when public_user is deleted

### Components

```
backend/
├── models/
│   ├── database/
│   │   └── fcm_device.py              # Database models for FCM tokens
│   └── requests/
│       └── fcm_device.py              # Request/Response models
├── services/
│   ├── fcm_service.py                 # Core FCM service for sending notifications
│   └── fcm_notification_service.py    # Business logic for notifications
└── controllers/
    └── fcm_device.py                  # API endpoints for device registration
```

## Setup Instructions

### 1. Firebase Project Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Go to Project Settings → Service Accounts
3. Click "Generate new private key" to download the JSON credentials file
4. Save the file securely (e.g., `sbmg-firebase-adminsdk.json`)

### 2. Environment Configuration

Add the following to your `.env` file:

```bash
# FCM Configuration
FCM_CREDENTIAL_PATH=/path/to/your/firebase-credentials.json
```

### 3. Install Dependencies

```bash
pip install firebase-admin>=6.0.0
```

Or install from requirements.txt:

```bash
pip install -r requirements.txt
```

### 4. Run Database Migration

```bash
alembic upgrade head
```

This creates the `user_device_tokens` and `public_user_device_tokens` tables.

## API Endpoints

### Staff User Device Registration

**POST** `/api/v1/notifications/staff/register-device`

Register or update an FCM device token for authenticated staff users.

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Request Body:**
```json
{
  "device_id": "mobile_001",
  "fcm_token": "fcm_token_from_firebase_sdk",
  "device_name": "iPhone 14 Pro",
  "platform": "ios"
}
```

**Response:**
```json
{
  "message": "Device token registered successfully",
  "device_id": "mobile_001"
}
```

### Public User Device Registration

**POST** `/api/v1/notifications/public/register-device`

Register or update an FCM device token for public users (citizens).

**Headers:**
- `token: <public_user_token>`

**Request Body:**
```json
{
  "device_id": "android_device_123",
  "fcm_token": "fcm_token_from_firebase_sdk",
  "device_name": "Samsung Galaxy S23",
  "platform": "android"
}
```

**Response:**
```json
{
  "message": "Device token registered successfully",
  "device_id": "android_device_123"
}
```

### Remove Staff Device

**DELETE** `/api/v1/notifications/staff/remove-device/{device_id}`

Remove an FCM device token for the authenticated staff user.

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "message": "Device token removed successfully"
}
```

## Notification Flow

### 1. New Complaint Notification (to Workers)

**Trigger:** When a new complaint is created via `/api/v1/citizen/with-media`

**Process:**
1. Complaint is created and saved to database
2. System finds all workers assigned to the complaint's village
3. Retrieves all FCM tokens for those workers
4. Sends multicast notification via FCM
5. Removes any invalid/expired tokens from database

**Notification Payload:**
```json
{
  "notification": {
    "title": "New Complaint Assigned",
    "body": "A new complaint has been registered in Village Name. Please review and take action."
  },
  "data": {
    "type": "new_complaint",
    "complaint_id": "123",
    "village_id": "45",
    "village_name": "Village Name"
  }
}
```

### 2. Status Update Notification (to Citizens)

**Trigger:** When complaint status is updated via `/api/v1/complaints/{complaint_id}/status`

**Process:**
1. Complaint status is updated
2. System finds the public user who created the complaint (via mobile number)
3. Retrieves all FCM tokens for that public user
4. Sends multicast notification via FCM
5. Removes any invalid/expired tokens from database

**Notification Payload:**
```json
{
  "notification": {
    "title": "Complaint Status Updated",
    "body": "Your complaint #123 status has been updated to: In Progress"
  },
  "data": {
    "type": "status_update",
    "complaint_id": "123",
    "new_status": "In Progress"
  }
}
```

## Client-Side Integration

### Mobile App (Flutter/React Native/Native)

1. **Install Firebase SDK** in your mobile app
2. **Request FCM token** when user logs in
3. **Register the token** with the backend API
4. **Handle notifications** in foreground and background

#### Example (Flutter):
```dart
import 'package:firebase_messaging/firebase_messaging.dart';

// Get FCM token
String? token = await FirebaseMessaging.instance.getToken();

// Register with backend
await registerDevice(
  deviceId: deviceId,
  fcmToken: token!,
  deviceName: 'User Device',
  platform: 'android'
);

// Handle foreground messages
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  print('Notification: ${message.notification?.title}');
  print('Data: ${message.data}');
  
  // Navigate to complaint details if needed
  if (message.data['type'] == 'new_complaint') {
    navigateToComplaint(message.data['complaint_id']);
  }
});
```

#### Example (React Native):
```javascript
import messaging from '@react-native-firebase/messaging';

// Request permission
await messaging().requestPermission();

// Get FCM token
const token = await messaging().getToken();

// Register with backend
await registerDevice({
  deviceId: deviceId,
  fcmToken: token,
  deviceName: 'User Device',
  platform: 'android'
});

// Handle foreground messages
messaging().onMessage(async remoteMessage => {
  console.log('Notification:', remoteMessage.notification);
  console.log('Data:', remoteMessage.data);
  
  // Show local notification or navigate
});
```

## Error Handling & Token Cleanup

The system automatically handles invalid or expired FCM tokens:

1. When sending notifications, FCM returns error codes for invalid tokens
2. The system identifies tokens with `UNREGISTERED` or `NOT_FOUND` errors
3. These tokens are automatically deleted from the database
4. This prevents sending to dead endpoints and keeps the database clean

## Security Considerations

1. **Token Storage:** FCM tokens are stored securely in the database with proper encryption
2. **Authentication:** Device registration requires valid JWT token (staff) or public user token (citizens)
3. **Authorization:** Users can only register/remove their own devices
4. **Credential Security:** Firebase service account credentials should never be committed to version control
5. **HTTPS Only:** All API endpoints should be served over HTTPS in production

## Testing

### Manual Testing

1. **Register a device:**
```bash
curl -X POST "http://localhost:8000/api/v1/notifications/staff/register-device" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test_device_001",
    "fcm_token": "YOUR_FCM_TOKEN_FROM_MOBILE_APP",
    "device_name": "Test Device",
    "platform": "android"
  }'
```

2. **Create a complaint** to trigger notification to workers

3. **Update complaint status** to trigger notification to citizen

### Monitoring

Monitor FCM notifications in your application logs:
- Successful sends are logged with count
- Failed sends are logged with error details
- Invalid tokens are logged when cleaned up

Example log output:
```
INFO: Registered new FCM token for user 5, device mobile_001
INFO: Sent FCM notification: 3 successful, 1 failed
WARNING: Invalid token detected: fcm_token_123...
INFO: Deleted invalid FCM token: fcm_token_123...
```

## Troubleshooting

### Notifications Not Sending

1. **Check Firebase credentials:**
   - Verify `FCM_CREDENTIAL_PATH` environment variable is set
   - Ensure the credentials file exists and is readable
   - Check Firebase Admin SDK initialization logs

2. **Check device tokens:**
   - Verify tokens are registered in the database
   - Ensure tokens are fresh (request new token from Firebase SDK if needed)

3. **Check user assignments:**
   - For new complaint notifications: Verify workers are assigned to the village
   - For status updates: Verify complaint has a valid mobile_number

### Invalid Token Errors

If you see many invalid token errors:
- Mobile app may not be refreshing tokens properly
- Users may have uninstalled the app
- Tokens expire after certain period (handled automatically)

## Performance Considerations

1. **Multicast Messages:** The system uses FCM multicast to send to multiple devices efficiently
2. **Async Operations:** Notifications are sent asynchronously and don't block the main request
3. **Error Handling:** Failed notifications don't cause the main operation (create/update complaint) to fail
4. **Token Cleanup:** Automatic cleanup prevents accumulation of dead tokens

## Future Enhancements

1. **Notification Preferences:** Allow users to configure which notifications they want to receive
2. **Notification History:** Store notification history in database
3. **Scheduled Notifications:** Support for scheduled/delayed notifications
4. **Rich Notifications:** Support for images, actions buttons, etc.
5. **Topic-Based Notifications:** Subscribe devices to topics for broadcast messages
6. **Analytics:** Track notification delivery rates and user engagement

## References

- [Firebase Cloud Messaging Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Firebase Admin Python SDK](https://firebase.google.com/docs/admin/setup)
- [FCM Server Reference](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)
