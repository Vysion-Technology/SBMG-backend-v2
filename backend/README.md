# Swachchha Bharat Mission (Gramin) - Rajasthan

# Access Levels
- Admin
- District Collector (CEO)
- Block Development Officer (BDO)
- Village Development Officer (VDO)
- Worker
- Public

## Explanation of Access Levels
- ADMIN can change any data.
- CEO can see the data of their district.
- BDO can see the data of their block.
- VDO can see the data of their village.
- WORKER can see the data related to their work.
- PUBLIC can create any complaint and see the status of any complaint.
- Each complaint gets assigned to a worker based on the location of the complaint.
- Each worker can see the complaints assigned to them and update the status of those complaints.
- Each worker can see the data related to their work.
- Worker can mark the complaint as completed.
- Each VDO can check the status of complaints in their village.
- VDO can mark the complaint as verified after the worker marks it as completed.
- VDO can also comment on the complaint.
- Each BDO can check the status of complaints in their block.
- Each CEO can check the status of complaints in their district.

## Authentication
- The system uses JWT (JSON Web Tokens) for authentication.
- Each user gets a token after logging in, which they must use to access protected routes.
- The token contains the user's role and location information, which is used to determine access levels.
- The token is verified on each request to ensure the user has the necessary permissions to access the requested resource.
- The token is set to expire after a certain period, requiring users to log in again to obtain a new token.
- Passwords are hashed using bcrypt before being stored in the database to ensure security.
- The system includes a password reset feature, allowing users to reset their passwords if they forget them

## Authorization
- The system uses role-based access control (RBAC) to manage user permissions.
- Each user is assigned a role (Admin, CEO, BDO, VDO, Worker, Public) that determines their access level.
- Middleware functions are used to check the user's role and location before allowing access to protected routes.
- The middleware checks the user's token to verify their identity and permissions.
- If the user does not have the necessary permissions, they receive a 403 Forbidden response.
- The system also includes logging and auditing features to track user activity and changes made to the data