# FCM Push Notifications - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
cd backend
pip install firebase-admin>=6.0.0
```

### 2. Get Firebase Credentials
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create/Select your project
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate new private key**
5. Save the JSON file (e.g., `firebase-credentials.json`)

### 3. Configure Environment
```bash
# Add to backend/.env file
FCM_CREDENTIAL_PATH=/path/to/firebase-credentials.json
```

### 4. Run Database Migration
```bash
cd backend
alembic upgrade head
```

### 5. Start Server
```bash
uvicorn main:app --reload
```

## 📱 API Endpoints

### Register Staff Device
```bash
POST /api/v1/notifications/staff/register-device
Authorization: Bearer <jwt_token>

{
  "device_id": "device_001",
  "fcm_token": "fcm_token_from_firebase_sdk",
  "device_name": "iPhone 14",
  "platform": "ios"
}
```

### Register Public User Device
```bash
POST /api/v1/notifications/public/register-device
token: <public_user_token>

{
  "device_id": "device_001",
  "fcm_token": "fcm_token_from_firebase_sdk",
  "device_name": "Samsung S23",
  "platform": "android"
}
```

### Remove Device
```bash
DELETE /api/v1/notifications/staff/remove-device/{device_id}
Authorization: Bearer <jwt_token>
```

## 🔔 Notification Triggers

### 1. New Complaint → Notifies Workers
**Trigger:** Citizen creates complaint via `/api/v1/citizen/with-media`

**Recipients:** All workers in the village where complaint was made

**Message:** "A new complaint has been registered in {village_name}. Please review and take action."

### 2. Status Update → Notifies Citizen
**Trigger:** Worker updates status via `/api/v1/complaints/{id}/status`

**Recipients:** Citizen who created the complaint

**Message:** "Your complaint #{id} status has been updated to: {status}"

## 🛠️ Mobile App Integration

### Flutter Example
```dart
// Get FCM token
String? token = await FirebaseMessaging.instance.getToken();

// Register with backend
await http.post(
  Uri.parse('http://your-api/api/v1/notifications/staff/register-device'),
  headers: {'Authorization': 'Bearer $jwtToken'},
  body: jsonEncode({
    'device_id': deviceId,
    'fcm_token': token,
    'platform': 'android'
  }),
);

// Handle notifications
FirebaseMessaging.onMessage.listen((message) {
  print('Notification: ${message.notification?.title}');
  if (message.data['type'] == 'new_complaint') {
    navigateToComplaint(message.data['complaint_id']);
  }
});
```

### React Native Example
```javascript
import messaging from '@react-native-firebase/messaging';

// Get FCM token
const token = await messaging().getToken();

// Register with backend
await fetch('http://your-api/api/v1/notifications/staff/register-device', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    device_id: deviceId,
    fcm_token: token,
    platform: 'android'
  }),
});

// Handle notifications
messaging().onMessage(async remoteMessage => {
  console.log('Notification:', remoteMessage);
});
```

## 🧪 Testing

### 1. Test FCM Service
```bash
cd backend
python test_fcm.py
```

### 2. Test Device Registration
```bash
# Staff user
curl -X POST "http://localhost:8000/api/v1/notifications/staff/register-device" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test_001",
    "fcm_token": "YOUR_FCM_TOKEN",
    "platform": "android"
  }'
```

### 3. Trigger Notifications
```bash
# Create complaint (triggers worker notification)
curl -X POST "http://localhost:8000/api/v1/citizen/with-media" \
  -H "token: PUBLIC_USER_TOKEN" \
  -F "complaint_type_id=1" \
  -F "village_id=1" \
  -F "description=Test complaint"

# Update status (triggers citizen notification)
curl -X PATCH "http://localhost:8000/api/v1/complaints/1/status" \
  -H "Authorization: Bearer STAFF_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status_name": "In Progress"}'
```

## 📊 Database Tables

### user_device_tokens
- Stores FCM tokens for staff users (Workers, VDOs, BDOs, etc.)
- One user can have multiple devices
- Unique constraint on (user_id, device_id)

### public_user_device_tokens
- Stores FCM tokens for public users (citizens)
- One user can have multiple devices
- Unique constraint on (public_user_id, device_id)

## 🔍 Troubleshooting

### Notifications not sending?
1. Check `FCM_CREDENTIAL_PATH` is set correctly
2. Verify Firebase credentials file exists
3. Check logs for FCM initialization errors
4. Ensure devices are registered in database

### Invalid token errors?
- Tokens may expire - refresh from Firebase SDK
- User may have uninstalled app
- Invalid tokens are automatically cleaned up

### Workers not receiving notifications?
- Verify worker is assigned to the village
- Check worker's role is "WORKER"
- Ensure worker has registered device tokens

### Citizens not receiving notifications?
- Verify complaint has `mobile_number` field
- Check public user with that mobile exists
- Ensure public user has registered device tokens

## 📚 Full Documentation

See [FCM_NOTIFICATIONS.md](../FCM_NOTIFICATIONS.md) for complete documentation.

## 🏗️ Architecture

```
┌─────────────┐
│   Mobile    │ ──register──▶ ┌──────────────────┐
│   Device    │               │  FCM Controller  │
└─────────────┘               └──────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │  Device Token DB    │
                              └─────────────────────┘

┌─────────────┐               ┌──────────────────┐
│  Complaint  │ ──create──▶   │  Notification    │
│  Created    │               │  Service         │
└─────────────┘               └──────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │   FCM Service       │
                              │  (Firebase Admin)   │
                              └─────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │  Push to Devices    │
                              └─────────────────────┘
```

## 📝 Files Created

```
backend/
├── models/
│   ├── database/fcm_device.py          # Database models
│   └── requests/fcm_device.py          # Request/Response models
├── services/
│   ├── fcm_service.py                  # Core FCM service
│   └── fcm_notification_service.py     # Business logic
├── controllers/
│   └── fcm_device.py                   # API endpoints
├── alembic/versions/
│   └── 13dc0a61a8bf_add_fcm_device_tokens.py  # Migration
├── test_fcm.py                         # Test script
└── setup_fcm.sh                        # Setup script

FCM_NOTIFICATIONS.md                    # Full documentation
FCM_QUICKSTART.md                       # This file
```

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Configure Firebase credentials
3. ✅ Run database migration
4. ✅ Test API endpoints
5. ✅ Integrate in mobile app
6. ✅ Test end-to-end notifications
7. 📈 Monitor and optimize

## 📞 Support

For issues or questions:
1. Check [FCM_NOTIFICATIONS.md](../FCM_NOTIFICATIONS.md)
2. Review server logs
3. Test with `test_fcm.py`
4. Check Firebase Console for errors
