# SBM Gramin Rajasthan Frontend

A modern React TypeScript frontend application for the Swachh Bharat Mission (Gramin) Rajasthan complaint management system.

## Features

- **Public Access**: Anyone can create complaints and track their status
- **Image Upload**: Support for uploading images when creating complaints
- **Role-based Authentication**: Different interfaces for Admin, CEO, BDO, VDO, Workers, and Public users
- **Responsive Design**: Built with Tailwind CSS for mobile-first responsive design
- **Real-time Updates**: Dynamic status tracking and complaint management

## Technology Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Form Management**: React Hook Form
- **Routing**: React Router DOM
- **Icons**: Lucide React

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Build for production:
```bash
npm run build
```

## Application Structure

### Pages and Components

- **HomePage**: Landing page with feature overview and quick actions
- **CreateComplaint**: Form for creating new complaints with image upload support
- **ComplaintStatus**: Public complaint tracking interface
- **Login**: Staff authentication with demo credentials
- **Dashboard**: Staff interface for complaint management
- **WorkerDashboard**: Worker-specific interface for assigned tasks

### API Integration

The application connects to the backend API with the following endpoints:

- **Public APIs**: Complaint creation, status checking
- **Admin APIs**: Manage complaint types, districts, blocks, villages  
- **Staff APIs**: Update complaint status, view all complaints
- **Worker APIs**: View assigned complaints, upload images, mark as done/invalid

### Authentication Flow

1. Public users can access complaint creation and status checking without login
2. Staff members login with credentials to access role-specific dashboards
3. Workers can mark complaints as completed or invalid
4. All roles have appropriate permissions and interface customizations

### Key Features Implemented

✅ **Public Complaint Creation** - Anyone can submit complaints with optional images  
✅ **Image Upload Support** - Drag-and-drop interface for attaching files  
✅ **Status Tracking** - Real-time complaint status checking  
✅ **Role-based Access** - Different dashboards for different user roles  
✅ **Worker Task Management** - Interface for workers to manage assigned complaints  
✅ **Invalid Complaint Marking** - Workers can mark complaints as invalid  
✅ **Responsive Design** - Works on desktop, tablet, and mobile devices  

## Demo Credentials

For testing the staff interfaces:

- **Admin**: admin / admin123
- **Worker**: worker1 / worker123  
- **VDO**: vdo1 / vdo123

## Environment Configuration

The application expects the backend API to be running on `http://localhost:8000`. To change this, update the `API_BASE_URL` in `src/api.ts`.

## Build and Deployment

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

The built files will be in the `dist` directory, ready for deployment to any static hosting service.
