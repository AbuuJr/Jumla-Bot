// src/components/admin/UserTable.tsx
// User table with actions

import { useState } from 'react';
import { useDeactivateUser } from '@lib/hooks/useUsers';
import Badge from '@components/ui/Badge';
import Button from '@components/ui/Button';
import type { User } from '@lib/api/types';

// ============================================================================
// User Table Component
// ============================================================================

interface UserTableProps {
  users: User[];
  currentUser: User | null;
  onResetPassword: (user: User) => void;
}

export default function UserTable({ users, currentUser, onResetPassword }: UserTableProps) {
  const { mutate: deactivateUser, isPending: isDeactivating } = useDeactivateUser();
  const [confirmDeactivate, setConfirmDeactivate] = useState<string | null>(null);

  const handleDeactivate = (userId: string) => {
    if (confirmDeactivate === userId) {
      deactivateUser(userId);
      setConfirmDeactivate(null);
    } else {
      setConfirmDeactivate(userId);
      // Auto-cancel after 3 seconds
      setTimeout(() => setConfirmDeactivate(null), 3000);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-neutral-200 text-left text-sm font-medium text-neutral-700">
            <th className="px-6 py-3">User</th>
            <th className="px-6 py-3">Email</th>
            <th className="px-6 py-3">Role</th>
            <th className="px-6 py-3">Status</th>
            <th className="px-6 py-3">Last Login</th>
            <th className="px-6 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-100">
          {users.map((user) => {
            const isCurrentUser = user.id === currentUser?.id;
            const canManage = !isCurrentUser && user.role !== 'admin';
            const isSystemOwner = user.is_system_owner;

            return (
              <tr key={user.id} className="text-sm hover:bg-neutral-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium">
                      {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium text-neutral-900">
                        {user.full_name || 'No name'}
                        {isCurrentUser && (
                          <span className="ml-2 text-xs text-neutral-500">(You)</span>
                        )}
                        {isSystemOwner && (
                          <Badge variant="error" className="ml-2">System Owner</Badge>
                        )}
                      </div>
                      <div className="text-xs text-neutral-500 font-mono">
                        {user.id.slice(0, 8)}...
                      </div>
                    </div>
                  </div>
                </td>

                <td className="px-6 py-4 text-neutral-700">
                  {user.email}
                </td>

                <td className="px-6 py-4">
                  <Badge variant={getRoleBadgeVariant(user.role)}>
                    {formatRole(user.role)}
                  </Badge>
                </td>

                <td className="px-6 py-4">
                  <Badge variant={user.is_active ? 'success' : 'default'}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </td>

                <td className="px-6 py-4 text-neutral-600">
                  {user.last_login_at 
                    ? new Date(user.last_login_at).toLocaleString()
                    : 'Never'
                  }
                </td>

                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    {/* Reset Password Button */}
                    {canManage && user.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onResetPassword(user)}
                      >
                        Reset Password
                      </Button>
                    )}

                    {/* Admin Password Reset Info */}
                    {!canManage && user.role === 'admin' && !isCurrentUser && (
                      <span className="text-xs text-neutral-500 italic">
                        System Owner only
                      </span>
                    )}

                    {/* Deactivate Button */}
                    {canManage && user.is_active && (
                      <Button
                        variant={confirmDeactivate === user.id ? 'error' : 'ghost'}
                        size="sm"
                        onClick={() => handleDeactivate(user.id)}
                        disabled={isDeactivating}
                      >
                        {confirmDeactivate === user.id ? 'Confirm?' : 'Deactivate'}
                      </Button>
                    )}

                    {/* Inactive Badge */}
                    {!user.is_active && (
                      <span className="text-xs text-neutral-500">
                        Deactivated
                      </span>
                    )}

                    {/* Current User */}
                    {isCurrentUser && (
                      <span className="text-xs text-neutral-500">
                        Cannot modify yourself
                      </span>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ===== Helper Functions =====

function getRoleBadgeVariant(role: string): 'default' | 'success' | 'warning' | 'info' {
  const mapping: Record<string, 'default' | 'success' | 'warning' | 'info'> = {
    admin: 'error' as any, // Using error variant for admin to highlight
    agent: 'info',
    integrator: 'warning',
    bot: 'default',
  };
  return mapping[role] || 'default';
}

function formatRole(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1);
}