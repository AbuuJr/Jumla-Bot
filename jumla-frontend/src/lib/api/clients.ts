// src/lib/api/clients.ts
// Enhanced with session management and new endpoints

import { apiClient, getRefreshToken } from './axios';
import type {
  // Auth types
  LoginRequest,
  LoginResponse,
  RefreshTokenResponse,
  LogoutRequest,
  UserResponse,
  // Session types
  Session,
  SessionsListResponse,
  // User management types
  CreateUserRequest,
  ResetPasswordRequest,
  UsersListResponse,
  // Audit log types
  AuditLogsListResponse,
  // Lead types (existing)
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
// Authentication API (ENHANCED)
// ============================================================================

export const authApi = {
  /**
   * Login with email and password
   * Creates a new session on the backend
   */
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', data);
    return response.data;
  },

  /**
   * Logout current session
   * Revokes the refresh token on the backend
   */
  logout: async (refreshToken?: string): Promise<void> => {
    const token = refreshToken || getRefreshToken();
    await apiClient.post('/api/v1/auth/logout', {
      refresh_token: token,
    });
  },

  /**
   * Logout from all devices
   * Revokes all sessions for the current user
   */
  logoutAll: async (): Promise<void> => {
    await apiClient.post('/api/v1/auth/logout-all');
  },

  /**
   * Refresh access token using refresh token
   * Implements token rotation (old refresh token is revoked, new one issued)
   */
  refreshToken: async (refreshToken: string): Promise<RefreshTokenResponse> => {
    const response = await apiClient.post<RefreshTokenResponse>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  /**
   * Get current authenticated user
   */
  me: async (): Promise<UserResponse> => {
    const response = await apiClient.get<UserResponse>('/api/v1/auth/me');
    return response.data;
  },
};


// ============================================================================
// User Management API (NEW)
// ============================================================================

export const usersApi = {
  /**
   * List users in the organization
   * Admin only - scoped to current user's organization
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    role?: string;
    is_active?: boolean;
  }): Promise<UsersListResponse> => {
    const response = await apiClient.get<UsersListResponse>('/api/v1/admin/users', { params });
    return response.data;
  },

  /**
   * Create a new user
   * Admin only - can only create users in their organization
   */
  create: async (data: CreateUserRequest): Promise<UserResponse> => {
    const response = await apiClient.post<UserResponse>('/api/v1/admin/users', data);
    return response.data;
  },

  /**
   * Deactivate a user
   * Admin only - revokes all user sessions
   */
  deactivate: async (userId: string): Promise<{ message: string; sessions_revoked: boolean }> => {
    const response = await apiClient.patch(`/api/v1/admin/users/${userId}/deactivate`);
    return response.data;
  },

  /**
   * Reset user password
   * Admin can reset non-admin users only
   * System owner can reset any password
   * 
   * @throws {Error} 403 if trying to reset admin password as non-system owner
   */
  resetPassword: async (data: ResetPasswordRequest): Promise<{
    message: string;
    user_email: string;
    sessions_revoked: boolean;
  }> => {
    const response = await apiClient.post('/api/v1/admin/reset-password', data);
    return response.data;
  },
};

// ============================================================================
// Session Management API (NEW)
// ============================================================================

export const sessionsApi = {
  /**
   * List active sessions
   * Admin can see all org sessions, users see only their own
   */
  list: async (params?: {
    user_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<SessionsListResponse> => {
    const response = await apiClient.get<SessionsListResponse>('/api/v1/admin/sessions', { 
      params 
    });
    return response.data;
  },

  /**
   * Revoke a specific session
   * Admin only
   */
  revoke: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/api/v1/admin/sessions/${sessionId}`);
    return response.data;
  },
};

// ============================================================================
// Audit Logs API (NEW)
// ============================================================================

export const auditLogsApi = {
  /**
   * List audit logs for the organization
   * Admin only
   */
  list: async (params?: {
    page?: number;
    page_size?: number;
    entity_type?: string;
    action?: string;
  }): Promise<AuditLogsListResponse> => {
    const response = await apiClient.get<AuditLogsListResponse>('/api/v1/admin/audit-logs', { 
      params 
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