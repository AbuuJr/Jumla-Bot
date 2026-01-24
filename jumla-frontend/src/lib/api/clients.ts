import { apiClient } from './axios';
import type {
  LoginRequest,
  LoginResponse,
  LeadCreateRequest,
  LeadCreateResponse,
  LeadsListResponse,
  LeadDetailResponse,
  SendMessageRequest,
  SendMessageResponse,
  FileUploadRequest,
  FileUploadResponse,
  OfferGenerateRequest,
  Offer,
  OfferApproveRequest,
  OfferApproveResponse,
} from './types';

// ============================================================================
// API Client Functions - Typed wrappers for all MVP endpoints
// ============================================================================

// ===== Authentication =====
export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout');
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string }> => {
    const response = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};

// ===== Leads =====
export const leadsApi = {
  create: async (data: LeadCreateRequest): Promise<LeadCreateResponse> => {
    const response = await apiClient.post<LeadCreateResponse>('/api/v1/leads', data);
    return response.data;
  },

  list: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }): Promise<LeadsListResponse> => {
    const response = await apiClient.get<LeadsListResponse>('/api/v1/leads', { params });
    return response.data;
  },

  get: async (id: string): Promise<LeadDetailResponse> => {
    const response = await apiClient.get<LeadDetailResponse>(`/api/v1/leads/${id}`);
    return response.data;
  },

  update: async (id: string, data: Partial<LeadCreateRequest>): Promise<LeadDetailResponse> => {
    const response = await apiClient.patch<LeadDetailResponse>(`/api/v1/leads/${id}`, data);
    return response.data;
  },
};

// ===== Conversations =====
export const conversationsApi = {
  // Send message (using lead_id, not conversation_id)
  sendMessage: async (
    leadId: string,
    data: SendMessageRequest
  ): Promise<SendMessageResponse> => {
    const response = await apiClient.post<SendMessageResponse>(
      `/api/v1/conversations/${leadId}/message`,
      data
    );
    return response.data;
  },

  // Get messages for a lead
  getMessages: async (leadId: string) => {
    const response = await apiClient.get(`/api/v1/conversations/lead/${leadId}`);
    return response.data;
  },
};

// ===== File Upload =====
export const fileApi = {
  // Step 1: Request signed upload URL
  requestUpload: async (data: FileUploadRequest): Promise<FileUploadResponse> => {
    const response = await apiClient.post<FileUploadResponse>('/api/v1/files/upload', data);
    return response.data;
  },

  // Step 2: Upload file to signed URL (direct to S3/storage, not through API)
  uploadToSignedUrl: async (signedUrl: string, file: File): Promise<void> => {
    await fetch(signedUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    });
  },
};

// ===== Offers =====
export const offersApi = {
  generate: async (data: OfferGenerateRequest): Promise<Offer> => {
    const response = await apiClient.post<Offer>('/api/v1/offers/generate', data);
    return response.data;
  },

  get: async (leadId: string): Promise<Offer> => {
    const response = await apiClient.get<Offer>(`/api/v1/leads/${leadId}/offer`);
    return response.data;
  },

  approve: async (data: OfferApproveRequest): Promise<OfferApproveResponse> => {
    const response = await apiClient.post<OfferApproveResponse>('/api/v1/offers/approve', data);
    return response.data;
  },

  reject: async (offerId: string, reason?: string): Promise<void> => {
    await apiClient.post(`/api/v1/offers/${offerId}/reject`, { reason });
  },
};