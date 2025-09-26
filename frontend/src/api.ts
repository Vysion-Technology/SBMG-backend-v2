import axios from 'axios';
import type { 
  Complaint, 
  CreateComplaintRequest, 
  ComplaintType,
  Village, 
  District,
  Block,
  CreateDistrictRequest,
  CreateBlockRequest,
  CreateVillageRequest,
  AuthResponse,
  LoginRequest,
  AssignedComplaintResponse,
  MediaUploadResponse,
  ComplaintStatusResponse,
  ComplaintDetailsResponse,
  CitizenStatusUpdateRequest,
  CitizenStatusUpdateResponse,
  VerifyComplaintStatusRequest,
  VerifyComplaintStatusResponse,
  Role,
  CreateRoleRequest,
  UpdateRoleRequest,
  PositionHolder,
  UpdatePositionHolderRequest,
  CreateUserWithPositionRequest,
  UserWithPositionResponse,
  ChangePasswordRequest
} from './types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authApi = {
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data as AuthResponse;
  },
    
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Public API
export const publicApi = {
  // Create complaint without media
  createComplaint: async (complaint: CreateComplaintRequest): Promise<Complaint> => {
    const response = await api.post('/complaints/', complaint);
    return response.data as Complaint;
  },
  
  // Create complaint with media
  createComplaintWithMedia: async (
    complaint: CreateComplaintRequest, 
    files: FileList
  ): Promise<Complaint> => {
    const formData = new FormData();
    formData.append('complaint_type_id', complaint.complaint_type_id.toString());
    formData.append('village_id', complaint.village_id.toString());
    formData.append('block_id', complaint.block_id.toString());
    formData.append('district_id', complaint.district_id.toString());
    formData.append('description', complaint.description);
    
    // Add mobile number if provided
    if (complaint.mobile_number) {
      formData.append('mobile_number', complaint.mobile_number);
    }
    
    // Add files
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });
    
    const response = await api.post('/complaints/with-media', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as Complaint;
  },
  
  // Get complaint status (public)
  getComplaintStatus: async (complaintId: number): Promise<ComplaintStatusResponse> => {
    const response = await api.get(`/public/complaints/${complaintId}/status`);
    return response.data as ComplaintStatusResponse;
  },

  // Get detailed complaint information (public)
  getComplaintDetails: async (complaintId: number): Promise<ComplaintDetailsResponse> => {
    const response = await api.get(`/complaints/${complaintId}/details`);
    return response.data as ComplaintDetailsResponse;
  },

  // Citizen update complaint status (public)
  citizenUpdateComplaintStatus: async (request: CitizenStatusUpdateRequest): Promise<CitizenStatusUpdateResponse> => {
    const response = await api.post('/complaints/citizen/update-status', request);
    return response.data as CitizenStatusUpdateResponse;
  },

  // Verify complaint status (public) - NEW API
  verifyComplaintStatus: async (request: VerifyComplaintStatusRequest): Promise<VerifyComplaintStatusResponse> => {
    const response = await api.post('/complaints/citizen/verify-status', request);
    return response.data as VerifyComplaintStatusResponse;
  },

  // Get public complaints list with details (for aggregated data)
  getPublicComplaints: async (
    districtId?: number,
    blockId?: number,
    villageId?: number,
    skip?: number,
    limit?: number
  ): Promise<ComplaintDetailsResponse[]> => {
    const params: Record<string, any> = {};
    if (districtId) params.district_id = districtId;
    if (blockId) params.block_id = blockId;
    if (villageId) params.village_id = villageId;
    if (skip !== undefined) params.skip = skip;
    if (limit !== undefined) params.limit = limit;

    const response = await api.get('/reports/public/complaints-status', { params });
    return response.data as ComplaintDetailsResponse[];
  },
};

// Admin API
export const adminApi = {
  // Dashboard analytics
  getDashboardStats: async () => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },

  // Geography Management
  createDistrict: async (district: CreateDistrictRequest): Promise<District> => {
    const response = await api.post('/admin/districts', district);
    return response.data as District;
  },

  createBlock: async (block: CreateBlockRequest): Promise<Block> => {
    const response = await api.post('/admin/blocks', block);
    return response.data as Block;
  },

  createVillage: async (village: CreateVillageRequest): Promise<Village> => {
    const response = await api.post('/admin/villages', village);
    return response.data as Village;
  },

  getComplaintTypes: async (): Promise<ComplaintType[]> => {
    const response = await api.get('/public/complaint-types');
    return response.data as ComplaintType[];
  },
    
  getDistricts: async (): Promise<District[]> => {
    const response = await api.get('/public/districts');
    return response.data as District[];
  },
    
  getBlocks: async (districtId?: number): Promise<Block[]> => {
    const params = districtId ? { district_id: districtId } : {};
    const response = await api.get('/public/blocks', { params });
    return response.data as Block[];
  },
    
  getVillages: async (blockId?: number): Promise<Village[]> => {
    const params = blockId ? { block_id: blockId } : {};
    const response = await api.get('/public/villages', { params });
    return response.data as Village[];
  },
};

// Staff API
export const staffApi = {
  // Update complaint status
  updateComplaintStatus: async (complaintId: number, statusName: string) => {
    const response = await api.patch(`/complaints/${complaintId}/status`, { status_name: statusName });
    return response.data;
  },
    
  // Get all complaints
  getAllComplaints: async (): Promise<Complaint[]> => {
    const response = await api.get('/reports/complaints');
    return response.data as Complaint[];
  },
    
  // Get complaint details
  getComplaintDetails: async (complaintId: number): Promise<AssignedComplaintResponse> => {
    const response = await api.get(`/reports/complaints/${complaintId}`);
    return response.data as AssignedComplaintResponse;
  },
};

// Worker API
export const workerApi = {
  // Get assigned complaints
  getAssignedComplaints: async (): Promise<AssignedComplaintResponse[]> => {
    const response = await api.get('/reports/worker/assigned-complaints');
    return response.data as AssignedComplaintResponse[];
  },
    
  // Upload media for complaint
  uploadComplaintMedia: async (complaintId: number, file: File): Promise<MediaUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/reports/worker/complaints/${complaintId}/media`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as MediaUploadResponse;
  },
  
  // Mark complaint as done
  markComplaintDone: async (complaintId: number) => {
    const response = await api.patch(`/reports/worker/complaints/${complaintId}/mark-done`);
    return response.data;
  },
};

// User Management API
export const userManagementApi = {
  // Role management
  createRole: async (roleData: CreateRoleRequest): Promise<Role> => {
    const response = await api.post('/user-management/roles', roleData);
    return response.data as Role;
  },

  getAllRoles: async (): Promise<Role[]> => {
    const response = await api.get('/user-management/roles');
    return response.data as Role[];
  },

  getRole: async (roleId: number): Promise<Role> => {
    const response = await api.get(`/user-management/roles/${roleId}`);
    return response.data as Role;
  },

  updateRole: async (roleId: number, updateData: UpdateRoleRequest): Promise<Role> => {
    const response = await api.put(`/user-management/roles/${roleId}`, updateData);
    return response.data as Role;
  },

  // User and Position Holder management
  createUserWithPosition: async (userData: CreateUserWithPositionRequest): Promise<UserWithPositionResponse> => {
    const response = await api.post('/user-management/users', userData);
    return response.data as UserWithPositionResponse;
  },

  getAllPositionHolders: async (skip: number = 0, limit: number = 100, roleName?: string): Promise<PositionHolder[]> => {
    const params: any = { skip, limit };
    if (roleName) params.role_name = roleName;
    const response = await api.get('/user-management/position-holders', { params });
    return response.data as PositionHolder[];
  },

  getPositionHolder: async (positionId: number): Promise<PositionHolder> => {
    const response = await api.get(`/user-management/position-holders/${positionId}`);
    return response.data as PositionHolder;
  },

  updatePositionHolder: async (positionId: number, updateData: UpdatePositionHolderRequest): Promise<PositionHolder> => {
    const response = await api.put(`/user-management/position-holders/${positionId}`, updateData);
    return response.data as PositionHolder;
  },

  // Change user password (Admin only)
  changeUserPassword: async (userId: number, passwordData: ChangePasswordRequest): Promise<{ message: string }> => {
    const response = await api.put(`/user-management/users/${userId}/password`, passwordData);
    return response.data as { message: string };
  },
};

export default api;