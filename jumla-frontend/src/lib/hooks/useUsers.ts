// src/lib/hooks/useUsers.ts
// User management hook with React Query

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi } from '@lib/api/clients';
import { useToast } from '@lib/hooks/useToast';
import type { User, CreateUserRequest, ResetPasswordRequest } from '@lib/api/types';

// ============================================================================
// Query Keys
// ============================================================================

export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...userKeys.lists(), filters] as const,
};

// ============================================================================
// List Users Hook
// ============================================================================

interface UseUsersParams {
  page?: number;
  page_size?: number;
  role?: string;
  is_active?: boolean;
}

export function useUsers(params: UseUsersParams = {}) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: () => usersApi.list(params),
    staleTime: 30000, // 30 seconds
  });
}

// ============================================================================
// Create User Hook
// ============================================================================

export function useCreateUser() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (data: CreateUserRequest) => usersApi.create(data),
    onSuccess: (data) => {
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      
      toast.success(`User ${data.email} created successfully`);
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to create user');
    },
  });
}

// ============================================================================
// Deactivate User Hook
// ============================================================================

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation({
    mutationFn: (userId: string) => usersApi.deactivate(userId),
    onSuccess: (data, userId) => {
      // Invalidate users list
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      
      toast.success('User deactivated successfully');
    },
    onError: (error: any) => {
      toast.error(error.message || 'Failed to deactivate user');
    },
  });
}

// ============================================================================
// Reset Password Hook
// ============================================================================

export function useResetPassword() {
  const toast = useToast();

  return useMutation({
    mutationFn: (data: ResetPasswordRequest) => usersApi.resetPassword(data),
    onSuccess: (data) => {
      toast.success(`Password reset for ${data.user_email}. All sessions revoked.`);
    },
    onError: (error: any) => {
      // Special handling for admin password reset restriction
      if (error.status === 403 && error.message?.includes('System Owner')) {
        toast.error('Admin passwords can only be reset by System Owner. Please contact support.', 7000);
      } else {
        toast.error(error.message || 'Failed to reset password');
      }
    },
  });
}

// ============================================================================
// Helper Hook - Check if user can be managed
// ============================================================================

export function useCanManageUser(targetUser: User | null, currentUserRole: string) {
  if (!targetUser) return false;

  // Admin can manage non-admin users
  if (currentUserRole === 'admin' && targetUser.role !== 'admin') {
    return true;
  }

  // System owner can manage anyone
  if (currentUserRole === 'system_owner') {
    return true;
  }

  return false;
}