# In-App Notifications API Documentation (Mobile & Web)

This documentation describes the In-App Notifications API for Swachh Bharat Mission (Gramin) Rajasthan. It covers all endpoints required for notification centers, bell icon badges, read/unread status updates, and deep-linking navigation.

---

## 1. Authentication

The API supports both **Authority Staff Users** (VDO, BDO, CEO, Worker, Admin) and **Public Citizens**:

* **Authority Users (JWT)**:
  ```http
  Authorization: Bearer <jwt_access_token>
  ```
* **Public Users / Citizens (Token)**:
  ```http
  token: <public_user_token>
  ```
  *(or `Authorization: Bearer <public_user_token>`)*

---

## 2. API Endpoints

### A. Get Notifications List (Paginated)
Fetch in-app notifications for the logged-in user. Returns both direct notifications (sent to this user) and global broadcast announcements (events, schemes).

* **Method**: `GET`
* **Path**: `/api/v1/in-app-notifications`
* **Query Parameters**:
  | Parameter | Type | Required | Default | Description |
  | :--- | :--- | :--- | :--- | :--- |
  | `page` | integer | No | `1` | Page number (min: 1) |
  | `page_size` | integer | No | `20` | Items per page (min: 1, max: 100) |
  | `unread_only` | boolean | No | `false` | If `true`, returns only unread notifications |
  | `category` | string | No | `null` | Filter by category: `NOTICE`, `NOTICE_REPLY`, `SLA`, `EVENT_START`, `EVENT_EXPIRE`, `SCHEME_START`, `SCHEME_EXPIRE` |

#### Example Request
```http
GET /api/v1/in-app-notifications?page=1&page_size=20&unread_only=false HTTP/1.1
Host: api.sbmg.rajasthan.gov.in
Authorization: Bearer <token>
```

#### Example Response (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "New Official Notice: Show Cause Notice regarding SWM",
      "message": "You have received an official notice from CEO - Zila Parishad Jaipur (CEO). Please review and submit your reply.",
      "category": "NOTICE",
      "priority": "HIGH",
      "entity_type": "notice",
      "entity_id": 14,
      "action_url": "/notices/received/14",
      "is_read": false,
      "read_at": null,
      "created_at": "2026-11-04T16:30:00Z"
    },
    {
      "id": 102,
      "title": "SLA Warning: Complaint #304 Unresolved (7+ Days)",
      "message": "Complaint #304 has remained unresolved for 7 days. Please take prompt action before it escalates to Block level.",
      "category": "SLA",
      "priority": "WARNING",
      "entity_type": "complaint",
      "entity_id": 304,
      "action_url": "/complaints/304",
      "is_read": false,
      "read_at": null,
      "created_at": "2026-11-04T12:00:00Z"
    },
    {
      "id": 103,
      "title": "Event Started: Swachhata Pakhwada 2026",
      "message": "The event 'Swachhata Pakhwada 2026' is now active! Scheduled from 01 Nov 2026 to 15 Nov 2026.",
      "category": "EVENT_START",
      "priority": "MEDIUM",
      "entity_type": "event",
      "entity_id": 8,
      "action_url": "/events/8",
      "is_read": true,
      "read_at": "2026-11-04T14:10:00Z",
      "created_at": "2026-11-01T00:00:00Z"
    }
  ],
  "total": 3,
  "unread_count": 2,
  "page": 1,
  "page_size": 20
}
```

---

### B. Get Unread Count (Navbar Badge)
Fast lightweight endpoint to fetch only the unread count. Call this on app launch or on polling/refresh to show the badge counter on the bell icon.

* **Method**: `GET`
* **Path**: `/api/v1/in-app-notifications/unread-count`

#### Example Response (`200 OK`)
```json
{
  "unread_count": 2
}
```

---

### C. Mark Single Notification as Read
Call this when the user taps/clicks on a specific notification item.

* **Method**: `PATCH`
* **Path**: `/api/v1/in-app-notifications/{notification_id}/read`
* **Path Parameters**:
  * `notification_id` (integer, required): ID of the notification.

#### Example Response (`200 OK`)
```json
{
  "success": true,
  "marked_count": 1
}
```

#### Error Response (`404 Not Found`)
```json
{
  "detail": "Notification not found or access denied"
}
```

---

### D. Mark All Notifications as Read
Call this when the user taps "Mark all as read" or "Clear All" in the notification center.

* **Method**: `PATCH`
* **Path**: `/api/v1/in-app-notifications/mark-all-read`

#### Example Response (`200 OK`)
```json
{
  "success": true,
  "marked_count": 5
}
```

---

## 3. Categories & Mobile Routing Guide

When the user taps a notification in the notification tray, use `entity_type`, `entity_id`, or `action_url` to navigate to the target screen:

| Category | Description | `entity_type` | `entity_id` | Example `action_url` | Recommended Mobile Screen |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `NOTICE` | Official notice received | `notice` | Notice ID | `/notices/received/{id}` | Notice Details Screen (with Reply button) |
| `NOTICE_REPLY` | Reply received on a notice sent | `notice` | Notice ID | `/notices/sent/{id}` | Sent Notice Details Screen (view reply) |
| `SLA` | Complaint SLA escalation | `complaint` | Complaint ID | `/complaints/{id}` | Complaint Details Screen |
| `EVENT_START` | Community event started | `event` | Event ID | `/events/{id}` | Event Details Screen |
| `EVENT_EXPIRE` | Event ending soon (< 24h) | `event` | Event ID | `/events/{id}` | Event Details Screen / VDO Upload Proof |
| `SCHEME_START` | New government scheme open | `scheme` | Scheme ID | `/schemes/{id}` | Scheme Details / Apply Screen |
| `SCHEME_EXPIRE`| Scheme closing soon (< 7d) | `scheme` | Scheme ID | `/schemes/{id}` | Scheme Details Screen |

---

## 4. Priority Levels & UI Badges

Use the `priority` field to style the notification card in the mobile UI:

* `CRITICAL` / `HIGH`: Red/Amber icon or alert badge (e.g., Notices, SLA Breaches)
* `WARNING`: Yellow/Orange warning icon (e.g., 7-day SLA warning, Scheme closing)
* `MEDIUM` / `LOW`: Blue/Gray neutral info card (e.g., Notice reply, Event announcement)
