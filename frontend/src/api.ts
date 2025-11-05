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
  ComplaintCommentResponse,
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

  // Citizen OTP authentication
  sendOTP: async (mobileNumber: string): Promise<{ detail: string }> => {
    const response = await api.post<{ detail: string }>('/auth/send-otp', null, {
      params: { mobile_number: mobileNumber }
    });
    return response.data;
  },

  verifyOTP: async (mobileNumber: string, otp: string): Promise<{ token: string }> => {
    const response = await api.post<{ token: string }>('/auth/verify-otp', null, {
      params: { mobile_number: mobileNumber, otp: otp }
    });
    return response.data;
  },
};

// Public API (Citizen)
export const publicApi = {
  // Create complaint without media (for backwards compatibility)
  createComplaint: async (complaint: CreateComplaintRequest, citizenToken?: string): Promise<Complaint> => {
    const headers: Record<string, string> = {};
    const token = citizenToken || localStorage.getItem('citizen_token');
    if (token) {
      headers['token'] = token;
    }

    // Use empty FileList for consistency
    const emptyFiles = new DataTransfer().files;
    return publicApi.createComplaintWithMedia(complaint, emptyFiles, citizenToken);
  },

  // Create complaint with media (requires citizen token)
  createComplaintWithMedia: async (
    complaint: CreateComplaintRequest, 
    files: FileList,
    citizenToken?: string
  ): Promise<Complaint> => {
    const formData = new FormData();
    formData.append('complaint_type_id', complaint.complaint_type_id.toString());
    formData.append('village_id', complaint.village_id.toString());
    formData.append('block_id', complaint.block_id.toString());
    formData.append('district_id', complaint.district_id.toString());
    formData.append('description', complaint.description);
    
    // Add files
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const headers: Record<string, string> = { 'Content-Type': 'multipart/form-data' };
    const token = citizenToken || localStorage.getItem('citizen_token');
    if (token) {
      headers['token'] = token;
    }
    
    const response = await api.post('/citizen/with-media', formData, { headers });
    return response.data as Complaint;
  },
  
  // Get complaint status (public)
  getComplaintStatus: async (complaintId: number): Promise<ComplaintStatusResponse> => {
    const response = await api.get(`/complaints/${complaintId}/status`);
    return response.data as ComplaintStatusResponse;
  },

  // Get detailed complaint information (public)
  getComplaintDetails: async (complaintId: number): Promise<ComplaintDetailsResponse> => {
    const response = await api.get(`/public/${complaintId}/details`);
    return response.data as ComplaintDetailsResponse;
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

    const response = await api.get('/reports/public/status', { params });
    return response.data as ComplaintDetailsResponse[];
  },
};

// Admin API
export const adminApi = {
  // Dashboard analytics
  getDashboardStats: async () => {
    const response = await api.get('/reports/dashboard');
    return response.data;
  },

  // Geography Management
  createDistrict: async (district: CreateDistrictRequest): Promise<District> => {
    const response = await api.post('/geography/districts', district);
    return response.data as District;
  },

  createBlock: async (block: CreateBlockRequest): Promise<Block> => {
    const response = await api.post('/geography/blocks', block);
    return response.data as Block;
  },

  createVillage: async (village: CreateVillageRequest): Promise<Village> => {
    const response = await api.post('/geography/villages', village);
    return response.data as Village;
  },

  getComplaintTypes: async (): Promise<ComplaintType[]> => {
    const response = await api.get('/public/complaint-types');
    return response.data as ComplaintType[];
  },
    
  getDistricts: async (): Promise<District[]> => {
    const response = await api.get('/geography/districts');
    return response.data as District[];
  },
    
  getBlocks: async (districtId?: number): Promise<Block[]> => {
    const params = districtId ? { district_id: districtId } : {};
    const response = await api.get('/geography/blocks', { params });
    return response.data as Block[];
  },
    
  getVillages: async (blockId?: number): Promise<Village[]> => {
    const params = blockId ? { block_id: blockId } : {};
    const response = await api.get('/geography/villages', { params });
    return response.data as Village[];
  },
};

// Staff API (BDO, CEO, ADMIN, VDO)
export const staffApi = {
  // Update complaint status
  updateComplaintStatus: async (complaintId: number, statusName: string) => {
    const response = await api.patch(`/complaints/${complaintId}/status`, { status_name: statusName });
    return response.data;
  },
    
  // Get all complaints with filters (consolidated reporting)
  getAllComplaints: async (params?: {
    district_id?: number;
    block_id?: number;
    village_id?: number;
    status_name?: string;
    skip?: number;
    limit?: number;
  }): Promise<Complaint[]> => {
    const response = await api.get('/reports/complaints', { params });
    return response.data as Complaint[];
  },
    
  // Get complaint details
  getComplaintDetails: async (complaintId: number): Promise<AssignedComplaintResponse> => {
    const response = await api.get(`/reports/complaints/${complaintId}`);
    return response.data as AssignedComplaintResponse;
  },

  // Add comment to complaint (Workers and VDOs)
  addComplaintComment: async (
    complaintId: number,
    commentText: string,
    photo?: File
  ): Promise<ComplaintCommentResponse> => {
    const formData = new FormData();
    formData.append('comment_text', commentText);
    if (photo) {
      formData.append('photo', photo);
    }

    const response = await api.post(`/complaints/${complaintId}/comments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as ComplaintCommentResponse;
  },

  // VDO verify complaint
  verifyComplaint: async (
    complaintId: number,
    comment: string,
    media?: File
  ): Promise<{ message: string; complaint_id: number; error?: string }> => {
    const formData = new FormData();
    formData.append('comment', comment);
    if (media) {
      formData.append('media', media);
    }

    const response = await api.patch<{ message: string; complaint_id: number; error?: string }>(
      `/complaints/vdo/complaints/${complaintId}/verify`, 
      formData, 
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    );
    return response.data;
  },
};

// Worker API
export const workerApi = {
  // Get assigned tasks/complaints (consolidated reporting)
  getAssignedComplaints: async (): Promise<AssignedComplaintResponse[]> => {
    const response = await api.get('/reports/worker/tasks');
    return response.data as AssignedComplaintResponse[];
  },
    
  // Upload media for complaint
  uploadComplaintMedia: async (complaintId: number, file: File): Promise<MediaUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post(`/complaints/${complaintId}/media`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data as MediaUploadResponse;
  },
  
  // Mark complaint as done
  markComplaintDone: async (complaintId: number, resolutionComment?: string) => {
    const response = await api.patch(`/complaints/${complaintId}/resolve`, { 
      resolution_comment: resolutionComment 
    });
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