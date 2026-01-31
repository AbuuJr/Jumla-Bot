// src/lib/api/axios.ts
// Enhanced with token rotation and improved error handling
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
//import { ApiError } from './types';

// ============================================================================
// Axios Instance Configuration
// Handles auth tokens, request/response interceptors, and error formatting
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10);
const TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || 'jumla_auth_token';
const REFRESH_TOKEN_KEY = import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY || 'jumla_refresh_token';

// Create axios instance with defaults
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ===== Request Interceptor =====
// Automatically attach auth token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================================
// Response Interceptor - Handle token refresh and errors
// ============================================================================

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: any) => void;
  reject: (reason?: any) => void;
}> = [];

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      // Don't attempt token refresh for login or refresh endpoints, but return the enhanced error
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return Promise.reject(enhanceError(error));
      }

      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);

      if (!refreshToken) {
        // No refresh token, clear everything and redirect to login
        isRefreshing = false;
        processQueue(error, null);
        clearAuthAndRedirect();
        return Promise.reject(enhanceError(error));
      }

      try {
        // Attempt to refresh the token
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token, refresh_token: new_refresh_token } = response.data;

        // Update stored tokens
        localStorage.setItem(TOKEN_KEY, access_token);
        localStorage.setItem(REFRESH_TOKEN_KEY, new_refresh_token);

        // Update authorization header
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
        }

        // Process queued requests
        processQueue(null, access_token);

        // Retry original request
        return apiClient(originalRequest);
      } catch (refreshError: any) {
        // Refresh failed, clear everything and redirect to login
        processQueue(refreshError, null);
        clearAuthAndRedirect();
        return Promise.reject(enhanceError(refreshError));
      } finally {
        isRefreshing = false;
      }
    }

    // Handle 403 errors (forbidden)
    if (error.response?.status === 403) {
      // Special handling for admin password reset
      if (originalRequest.url?.includes('/admin/reset-password')) {
        const customError = new Error(
          'Admin passwords can only be reset by System Owner. Please contact support.'
        ) as any;
        customError.response = error.response;
        customError.status = 403;
        return Promise.reject(customError);
      }

      // General 403 error
      const customError = new Error(
        'You do not have permission to perform this action.'
      ) as any;
      customError.response = error.response;
      customError.status = 403;
      return Promise.reject(customError);
    }

    // Handle network errors
    if (!error.response) {
      const customError = new Error(
        'Network error. Please check your connection and try again.'
      ) as any;
      customError.status = 0;
      return Promise.reject(customError);
    }

    // Handle other errors with user-friendly messages
    const enhancedError = enhanceError(error);
    return Promise.reject(enhancedError);
  }
);

// ============================================================================
// Helper Functions
// ============================================================================

function clearAuthAndRedirect() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  
  // Only redirect if not already on login page
  if (!window.location.pathname.includes('/login')) {
    window.location.href = '/login?session_expired=true';
  }
}

function enhanceError(error: AxiosError): Error {
  const status = error.response?.status;
  const data = (error.response?.data ?? {}) as any;

  // Use backend error message if available (FastAPI uses `detail`)
  const backendMessage = data?.detail || data?.message || data?.error || null;

  let userMessage: string;

  switch (status) {
    case 400:
      userMessage = backendMessage || 'Invalid request. Please check your input.';
      break;
    case 401:
      // Prefer backend-provided message for 401 (useful for incorrect credentials)
      userMessage = backendMessage || 'Your session has expired. Please login again.';
      break;
    case 403:
      userMessage = backendMessage || 'You do not have permission to perform this action.';
      break;
    case 404:
      userMessage = 'The requested resource was not found.';
      break;
    case 409:
      userMessage = backendMessage || 'This action conflicts with existing data.';
      break;
    case 422:
      userMessage = backendMessage || 'Validation error. Please check your input.';
      break;
    case 429:
      userMessage = 'Too many requests. Please try again later.';
      break;
    case 500:
      userMessage = 'An unexpected server error occurred. Please try again.';
      break;
    case 503:
      userMessage = 'Service temporarily unavailable. Please try again later.';
      break;
    default:
      userMessage = backendMessage || 'An unexpected error occurred. Please try again.';
  }

  const enhancedError = new Error(userMessage) as any;
  enhancedError.response = error.response;
  enhancedError.status = status;
  enhancedError.originalError = error;
  
  return enhancedError;
}

// ============================================================================
// Export utility functions for manual token management
// ============================================================================

export const getAccessToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
};

export const clearTokens = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

// ============================================================================
// Export default
// ============================================================================

export default apiClient;
