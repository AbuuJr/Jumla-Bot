import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { ApiError } from './types';

// ============================================================================
// Axios Instance Configuration
// Handles auth tokens, request/response interceptors, and error formatting
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000', 10);
const TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || 'jumla_auth_token';

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

// ===== Response Interceptor =====
// Handle token refresh and format errors consistently
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config;

    // If 401 and not already retrying, attempt token refresh
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('jumla_refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          localStorage.setItem(TOKEN_KEY, access_token);

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem('jumla_refresh_token');
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      }
    }

    // Format error for consistent handling
    const formattedError: ApiError = {
      error: error.response?.data?.error || 'API Error',
      message: error.response?.data?.message || error.message || 'An unexpected error occurred',
      details: error.response?.data?.details,
      status_code: error.response?.status || 500,
    };

    return Promise.reject(formattedError);
  }
);

// Helper to check if error is ApiError
export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'error' in error &&
    'message' in error &&
    'status_code' in error
  );
}