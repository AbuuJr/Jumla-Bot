// ============================================================================
// API Types - All request/response interfaces for MVP endpoints
// ============================================================================

// ===== Authentication =====
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  role: 'admin' | 'agent' | 'viewer';
  created_at: string;
}

// ===== Leads =====
export interface Lead {
  id: string;
  status: 'new' | 'qualifying' | 'qualified' | 'offer_generated' | 'offer_approved' | 'closed';
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
  source: 'chat' | 'form';
  initial_message?: string;
  seller_info?: Partial<SellerInfo>;
  property_info?: Partial<PropertyInfo>;
}

export interface LeadCreateResponse {
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
  lead: Lead;
  conversation?: Conversation;
  offer?: Offer;
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