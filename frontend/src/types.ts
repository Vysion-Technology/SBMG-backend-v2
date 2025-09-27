export interface Complaint {
  id: number;
  description: string;
  mobile_number?: string | null;
  status_name: string;
  village_name: string;
  block_name: string;
  district_name: string;
  created_at: string;
  updated_at: string | null;
  media_urls?: string[];
  assigned_worker?: string | null;
}

export interface CreateComplaintRequest {
  complaint_type_id: number;
  village_id: number;
  block_id: number;
  district_id: number;
  description: string;
  mobile_number?: string | null;
}

export interface ComplaintType {
  id: number;
  name: string;
  description?: string;
}

export interface ComplaintStatus {
  id: number;
  name: string;
  description?: string;
}

export interface Village {
  id: number;
  name: string;
  description?: string;
  block_id: number;
  district_id: number;
  block?: {
    id: number;
    name: string;
    district: {
      id: number;
      name: string;
    };
  };
}

export interface District {
  id: number;
  name: string;
  description?: string;
}

export interface Block {
  id: number;
  name: string;
  description?: string;
  district_id: number;
}

export interface CreateDistrictRequest {
  name: string;
  description?: string;
}

export interface CreateBlockRequest {
  name: string;
  description?: string;
  district_id: number;
}

export interface CreateVillageRequest {
  name: string;
  description?: string;
  block_id: number;
  district_id: number;
}

export interface PositionInfo {
  role: string;
  role_id: number;
  first_name: string;
  middle_name?: string;
  last_name: string;
  district_name?: string;
  block_name?: string;
  village_name?: string;
}

export interface User {
  id: number;
  username: string;
  email?: string;
  is_active: boolean;
  roles: string[];
  positions: PositionInfo[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface AssignedComplaintResponse {
  id: number;
  description: string;
  mobile_number?: string | null;
  status_name: string;
  village_name: string;
  block_name: string;
  district_name: string;
  created_at: string;
  updated_at: string | null;
  media_urls: string[];
}

export interface MediaUploadResponse {
  id: number;
  complaint_id: number;
  media_url: string;
  uploaded_at: string;
}

export interface DashboardStats {
  total_complaints: number;
  total_users?: number;
  total_districts?: number;
  total_blocks?: number;
  complaints_by_status: Record<string, number>;
  complaints_by_type: Record<string, number>;
  complaints_by_district?: Array<{ district: string; count: number }>;
  recent_complaints: ComplaintResponse[];
  geographic_summary: Record<string, unknown>;
  performance_metrics: Record<string, unknown>;
}

// Updated complaint response to match backend
export interface ComplaintResponse {
  id: number;
  description: string;
  status_name: string;
  complaint_type_name?: string | null;
  village_name: string;
  block_name: string;
  district_name: string;
  created_at: string;
  updated_at?: string | null;
  assigned_worker_name?: string | null;
  media_count: number;
  media_urls: string[];
}

export interface ComplaintStatusResponse {
  id: number;
  status_name: string;
  updated_at: string | null;
}

export interface ComplaintDetailsResponse {
  id: number;
  description: string;
  mobile_number?: string | null;
  complaint_type_name: string;
  status_name: string;
  village_name: string;
  block_name: string;
  district_name: string;
  created_at: string;
  updated_at: string | null;
  media_urls: string[];
  comments: ComplaintCommentResponse[];
  assigned_worker?: string | null;
  assignment_date?: string | null;
}

export interface ComplaintCommentResponse {
  id: number;
  complaint_id: number;
  comment: string;
  commented_at: string;
  user_name: string;
}

export interface CitizenStatusUpdateRequest {
  complaint_id: number;
  mobile_number: string;
  new_status: string; // "VERIFIED" or "RESOLVED"
}

export interface CitizenStatusUpdateResponse {
  message: string;
  complaint_id: number;
  new_status: string;
  updated_at: string;
}

export interface VerifyComplaintStatusRequest {
  complaint_id: number;
  mobile_number: string;
}

export interface VerifyComplaintStatusResponse {
  complaint_id: number;
  is_verified: boolean;
  is_resolved: boolean;
  is_completed: boolean;
  current_status: string;
  message: string;
}

// User Management Types

// User Management Types
export interface Role {
  id: number;
  name: string;
  description?: string;
}

export interface CreateRoleRequest {
  name: string;
  description?: string;
}

export interface UpdateRoleRequest {
  name?: string;
  description?: string;
}

export interface PositionHolder {
  id: number;
  user_id: number;
  role_id: number;
  role_name: string;
  first_name: string;
  middle_name?: string;
  last_name: string;
  date_of_joining?: Date;
  start_date?: Date;
  end_date?: Date;
  username: string;
  email?: string;
  district_id?: number;
  district_name?: string;
  block_id?: number;
  block_name?: string;
  village_id?: number;
  village_name?: string;
}

export interface CreateUserWithPositionRequest {
  role_name: string;
  first_name: string;
  last_name: string;
  middle_name?: string;
  date_of_joining?: Date;
  district_id?: number;
  block_id?: number;
  village_id?: number;
  contractor_name?: string;
  password?: string;
  start_date?: Date;
  end_date?: Date;
}

export interface UpdatePositionHolderRequest {
  first_name?: string;
  middle_name?: string;
  last_name?: string;
  date_of_joining?: Date;
  start_date?: Date;
  end_date?: Date;
}

export interface ChangePasswordRequest {
  new_password: string;
}

export interface UserWithPositionResponse {
  user: {
    id: number;
    username: string;
    email?: string;
    is_active: boolean;
  };
  position: PositionHolder;
}

// Worker Task Response (from consolidated reporting)
export interface WorkerTaskResponse {
  id: number;
  description: string;
  status_name: string;
  village_name: string;
  block_name: string;
  district_name: string;
  assigned_date?: string | null;
  due_date?: string | null;
  priority: string;
  media_urls: string[];
  completion_percentage: number;
}

// Admin Analytics Response
export interface AdminAnalyticsResponse {
  total_entities: Record<string, number>;
  performance_trends: Record<string, Array<Record<string, unknown>>>;
  user_productivity: Array<Record<string, unknown>>;
  geographic_distribution: Record<string, unknown>;
  system_health: Record<string, unknown>;
}

// Geography Detail Response Models
export interface DistrictDetailResponse {
  id: number;
  name: string;
  description?: string;
  blocks_count: number;
  villages_count: number;
  complaints_count: number;
}

export interface BlockDetailResponse {
  id: number;
  name: string;
  description?: string;
  district_id: number;
  district_name?: string;
  villages_count: number;
  complaints_count: number;
}

export interface VillageDetailResponse {
  id: number;
  name: string;
  description?: string;
  block_id: number;
  district_id: number;
  block_name?: string;
  district_name?: string;
  complaints_count: number;
}

// Error Response Models
export interface ErrorResponse {
  message: string;
  status_code: number;
  detail?: string;
}

export interface ValidationErrorResponse {
  message: string;
  status_code: number;
  errors: Array<Record<string, string>>;
}

// Pagination Response Models
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Hierarchical Geography Models
export interface DistrictWithBlocksResponse {
  id: number;
  name: string;
  description?: string;
  blocks: Block[];
}

export interface BlockWithVillagesResponse {
  id: number;
  name: string;
  description?: string;
  district_id: number;
  district_name?: string;
  villages: Village[];
}

// Bulk Operation Models
export interface BulkDeleteRequest {
  ids: number[];
}

export interface BulkDeleteResponse {
  deleted_count: number;
  failed_ids: number[];
  errors: string[];
}