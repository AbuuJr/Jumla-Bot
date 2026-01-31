// src/lib/hooks/useAuth.ts
// Enhanced with session management and token rotation

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '@lib/api/clients';
import { setTokens, clearTokens } from '@lib/api/axios';
import type { User, LoginRequest } from '@lib/api/types';

// ============================================================================
// Auth Store - Zustand store for authentication state
// Enhanced with refresh token and session management
// ============================================================================

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null; // NEW
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>; // NEW
  refreshSession: () => Promise<void>; // NEW
  setUser: (user: User) => void;
  clearError: () => void;
  initialize: () => Promise<void>; // NEW
}

const TOKEN_KEY = import.meta.env.VITE_AUTH_TOKEN_KEY || 'jumla_auth_token';
const REFRESH_TOKEN_KEY = import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY || 'jumla_refresh_token';

export const useAuth = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      /**
       * Login with email and password
       * Stores access token, refresh token, and user data
       */
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(credentials);

          // Store tokens in both localStorage and state
          setTokens(response.access_token, response.refresh_token);

          set({
            user: response.user || null,
            token: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          // Save the enhanced error message (axios enhanceError returns user-friendly message)
          const msg = error?.message || (error?.response?.data?.detail ?? 'Login failed');
          set({
            error: msg,
            isLoading: false,
            isAuthenticated: false,
          });
          // rethrow the original enhanced error so callers can inspect response if needed
          throw error;
        }
      },

      /**
       * Logout from current session
       * Revokes the refresh token on the backend
       */
      logout: async () => {
        const { refreshToken } = get();
        
        try {
          if (refreshToken) {
            await authApi.logout(refreshToken);
          }
        } catch (error) {
          console.error('Logout error:', error);
          // Continue with local logout even if API call fails
        } finally {
          // Clear tokens and state
          clearTokens();
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      /**
       * Logout from all devices
       * Revokes all sessions for the current user
       */
      logoutAll: async () => {
        try {
          await authApi.logoutAll();
        } catch (error) {
          console.error('Logout all error:', error);
        } finally {
          // Clear local tokens and state
          clearTokens();
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: null,
          });
        }
      },

      /**
       * Manually refresh the session
       * Gets new access and refresh tokens
       * Note: This is also handled automatically by axios interceptor
       */
      refreshSession: async () => {
        const { refreshToken } = get();
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await authApi.refreshToken(refreshToken);

          // Update tokens
          setTokens(response.access_token, response.refresh_token);

          set({
            token: response.access_token,
            refreshToken: response.refresh_token,
          });
        } catch (error: any) {
          // Refresh failed, logout
          clearTokens();
          set({
            user: null,
            token: null,
            refreshToken: null,
            isAuthenticated: false,
            error: 'Session expired. Please login again.',
          });
          throw error;
        }
      },

      /**
       * Initialize auth state from stored tokens
       * Fetches current user data if tokens exist
       */
      initialize: async () => {
        const { token, refreshToken } = get();
        
        // If we have tokens but no user, fetch user data
        if (token && refreshToken && !get().user) {
          try {
            const user = await authApi.me();
            set({ user, isAuthenticated: true });
          } catch (error) {
            // Token invalid, clear everything
            clearTokens();
            set({
              user: null,
              token: null,
              refreshToken: null,
              isAuthenticated: false,
            });
          }
        }
      },

      /**
       * Set user data (used when fetching user separately)
       */
      setUser: (user: User) => {
        set({ user });
      },

      /**
       * Clear error state
       */
      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'jumla-auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      // Don't persist error or loading states
      onRehydrateStorage: () => (state) => {
        // Clear error on rehydration
        if (state) {
          state.error = null;
          state.isLoading = false;
        }
      },
    }
  )
);

// ============================================================================
// Utility Hooks
// ============================================================================

/**
 * Hook to check if user has specific role
 */
export const useHasRole = (role: string | string[]): boolean => {
  const user = useAuth((state) => state.user);
  
  if (!user) return false;
  
  const roles = Array.isArray(role) ? role : [role];
  return roles.includes(user.role);
};

/**
 * Hook to check if user is admin
 */
export const useIsAdmin = (): boolean => {
  return useHasRole('admin');
};

/**
 * Hook to check if user is system owner
 */
export const useIsSystemOwner = (): boolean => {
  const user = useAuth((state) => state.user);
  return user?.is_system_owner || false;
};

/**
 * Hook to get current user organization ID
 */
export const useOrganizationId = (): string | null => {
  const user = useAuth((state) => state.user);
  return user?.organization_id || null;
};
