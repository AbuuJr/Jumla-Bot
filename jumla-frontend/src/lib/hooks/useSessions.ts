// src/lib/hooks/useSessions.ts
// Session management hooks with React Query

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sessionsApi } from '@lib/api/clients';
import { useToast } from '@lib/hooks/useToast';
import type { Session } from '@lib/api/types';

// ============================================================================
// Query Keys
// ============================================================================

export const sessionKeys = {
  all: ['sessions'] as const,
  lists: () => [...sessionKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...sessionKeys.lists(), filters] as const,
};

// ============================================================================
// List Sessions Hook
// ============================================================================

interface UseSessionsParams {
  user_id?: string;
  page?: number;
  page_size?: number;
}

export function useSessions(params: UseSessionsParams = {}) {
  return useQuery({
    queryKey: sessionKeys.list(params),
    queryFn: () => sessionsApi.list(params),
    staleTime: 10000, // 10 seconds (sessions change frequently)
    refetchInterval: 30000, // Auto-refresh every 30s
  });
}

// ============================================================================
// Revoke Session Hook
// ============================================================================

export function useRevokeSession() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (sessionId: string) => sessionsApi.revoke(sessionId),
    onSuccess: (data, sessionId) => {
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: sessionKeys.lists() });
      
      toast.success('Session revoked successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to revoke session');
    },
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Check if session is current session
 * Compares session ID with the current refresh token
 */
export function isCurrentSession(session: Session): boolean {
  // We can't easily determine current session from refresh token hash
  // Backend should add a flag, or we track session_id in localStorage
  // For now, we'll mark as current if it's the most recent for the user
  return false; // Placeholder - backend should provide this
}

/**
 * Format session device info from user agent
 */
export function formatDevice(userAgent: string | null): string {
  if (!userAgent) return 'Unknown Device';
  
  // Simple parsing - can be enhanced with a library like ua-parser-js
  if (userAgent.includes('Mobile')) return 'Mobile Device';
  if (userAgent.includes('Chrome')) return 'Chrome Browser';
  if (userAgent.includes('Firefox')) return 'Firefox Browser';
  if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) return 'Safari Browser';
  if (userAgent.includes('Edge')) return 'Edge Browser';
  
  return 'Desktop Browser';
}

/**
 * Format time ago (e.g., "2 hours ago")
 */
export function formatTimeAgo(dateString: string | null): string {
  if (!dateString) return 'Never';
  
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;
  
  return date.toLocaleDateString();
}

/**
 * Get session status colors
 */
export function getSessionStatusColor(session: Session): string {
  const now = new Date();
  const expiresAt = new Date(session.expires_at);
  
  // Expired
  if (expiresAt < now) return 'text-neutral-500';
  
  // Expires soon (< 1 day)
  const hoursUntilExpiry = (expiresAt.getTime() - now.getTime()) / (1000 * 60 * 60);
  if (hoursUntilExpiry < 24) return 'text-yellow-600';
  
  // Active
  return 'text-green-600';
}