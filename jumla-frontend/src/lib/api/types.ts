// ============================================================================
// API Types - All request/response interfaces for MVP endpoints
// Fixed: Changed 'status' to 'stage' to match backend model
// ============================================================================

// ============================================================================
// User & Auth Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'agent' | 'integrator' | 'bot';
  organization_id: string | null; // null for system owner
  is_active: boolean;
  is_system_owner: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

// ===== Auth Requests =====

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token?: string;
}

// ===== Auth Responses =====
export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string; // "bearer"
  expires_in: number; // seconds
  user?: User; // Optional - some endpoints might not return user
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  organization_id: string | null;
  is_active: boolean;
  is_system_owner: boolean;
  last_login_at: string | null;
  created_at: string;
  updated_at: string;
}

// ============================================================================
// Session Types (NEW)
// ============================================================================

export interface Session {
  id: string;
  user_id: string;
  user_agent: string | null;
  ip_address: string | null;
  created_at: string;
  last_used_at: string | null;
  expires_at: string;
  is_active: boolean;
}

export interface SessionsListResponse {
  items: Session[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// User Management Types (NEW)
// ============================================================================

export interface CreateUserRequest {
  email: string;
  password: string;
  full_name?: string;
  role: 'admin' | 'agent' | 'integrator' | 'bot';
  organization_id: string;
}

export interface UpdateUserRequest {
  full_name?: string;
  role?: 'admin' | 'agent' | 'integrator' | 'bot';
  is_active?: boolean;
}

export interface ResetPasswordRequest {
  email: string;
  new_password: string;
}

export interface UsersListResponse {
  items: User[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================================
// Audit Log Types (NEW)
// ============================================================================

export interface AuditLog {
  id: string;
  performed_by: string;
  entity_type: string;
  entity_id: string;
  action: string;
  before: any;
  after: any;
  created_at: string;
  ip_address: string | null;
}

export interface AuditLogsListResponse {
  items: AuditLog[];
  total: number;
  skip: number;
  limit: number;
}


// ===== Leads =====
export interface Lead {
  id: string;
  stage: 'new' | 'contacted' | 'qualified' | 'offer_made' | 'closed_won' | 'closed_lost';  // Fixed: renamed from 'status' to 'stage'
  source: 'chat' | 'form' | 'api';
  created_at: string;
  updated_at: string;
  seller_info?: SellerInfo;
  property_info?: PropertyInfo;
  conversation_id?: string;
  offer_id?: string;
}

export interface SellerInfo {
  name?: string;
  email?: string;
  phone?: string;
  motivation?: string;
  timeline?: string;
}

export interface PropertyInfo {
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  property_type?: string;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  year_built?: number;
  condition?: string;
  asking_price?: number;
}

export interface LeadCreateRequest {
  // ... your existing lead types
  seller_info?: {
    name?: string;
    email?: string;
    phone?: string;
  };
  property_info?: {
    address?: string;
    city?: string;
    state?: string;
    zip?: string;
  };
  source?: string;
  metadata?: Record<string, any>;
}

export interface LeadCreateResponse {
  id: string;
  message: string;
  lead: Lead;
  conversation_id: string;
}

export interface LeadsListResponse {
  leads: Lead[];
  total: number;
  page: number;
  page_size: number;
}

export interface LeadDetailResponse {
  id: string;
  organization_id: string;
  status: string;
  seller_info: any;
  property_info: any;
  conversations: any[];
  offers: any[];
  created_at: string;
  updated_at: string;
}

// ===== Conversations =====
export interface Conversation {
  id: string;
  lead_id: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  metadata?: {
    extracted_fields?: Record<string, any>;
    confidence_scores?: Record<string, number>;
  };
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  url: string;
  uploaded_at: string;
}

export interface SendMessageRequest {
  content: string;
  attachments?: string[]; // Array of attachment IDs after upload
}

export interface SendMessageResponse {
  user_message: Message;
  bot_message: Message;
  extracted_data?: {
    seller_info?: Partial<SellerInfo>;
    property_info?: Partial<PropertyInfo>;
  };
}

// ===== File Upload =====
export interface FileUploadRequest {
  filename: string;
  file_type: string;
  file_size: number;
}

export interface FileUploadResponse {
  upload_id: string;
  signed_url: string;
  file_url: string; // Final URL after upload
  expires_at: string;
}

// ===== Offers =====
export interface Offer {
  id: string;
  lead_id: string;
  status: 'draft' | 'pending' | 'approved' | 'rejected' | 'expired';
  offer_amount: number;
  earnest_money: number;
  closing_days: number;
  contingencies: string[];
  terms: string;
  generated_at: string;
  approved_at?: string;
  approved_by?: string;
  expires_at: string;
}

export interface OfferGenerateRequest {
  lead_id: string;
  override_params?: {
    offer_amount?: number;
    earnest_money?: number;
    closing_days?: number;
  };
}

export interface OfferApproveRequest {
  offer_id: string;
  notes?: string;
}

export interface OfferApproveResponse {
  offer: Offer;
  notification_sent: boolean;
}

// ===== Error Response =====
export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
  status_code: number;
}


// ============================================================================
// Common Types
// ============================================================================

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
  error_code?: string;
}
