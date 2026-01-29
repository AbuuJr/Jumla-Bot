// src/pages/admin/Users.tsx
// User management page

import { useState } from 'react';
import { useUsers } from '@lib/hooks/useUsers';
import { useAuth, useIsAdmin } from '@lib/hooks/useAuth';
import Card, { CardHeader } from '@components/ui/Card';
import Button from '@components/ui/Button';
import Spinner from '@components/ui/Spinner';
import Badge from '@components/ui/Badge';
import UserTable from '@components/admin/UserTable';
import CreateUserModal from '@components/admin/CreateUserModal';
import ResetPasswordModal from '@components/admin/ResetPasswordModal';
import type { User } from '@lib/api/types';

// ============================================================================
// Users Page - User management interface
// ============================================================================

export default function Users() {
  const isAdmin = useIsAdmin();
  const currentUser = useAuth((state) => state.user);
  
  // Filters
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [resetPasswordUser, setResetPasswordUser] = useState<User | null>(null);

  // Fetch users
  const { data: usersData, isLoading } = useUsers({
    page,
    page_size: pageSize,
    role: roleFilter || undefined,
    is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
  });

  const users = usersData?.items || [];
  const total = usersData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  if (!isAdmin) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Card className="max-w-md text-center">
          <div className="py-8">
            <h2 className="text-xl font-bold text-neutral-900">Access Denied</h2>
            <p className="mt-2 text-neutral-600">
              You need admin privileges to access user management.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading users..." />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">User Management</h1>
            <p className="mt-1 text-sm text-neutral-600">
              Manage users in your organization
            </p>
          </div>
          
          <Button
            variant="primary"
            onClick={() => setShowCreateModal(true)}
          >
            + Create User
          </Button>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <StatCard
            label="Total Users"
            value={total}
            variant="default"
          />
          <StatCard
            label="Active"
            value={users.filter((u) => u.is_active).length}
            variant="success"
          />
          <StatCard
            label="Inactive"
            value={users.filter((u) => !u.is_active).length}
            variant="warning"
          />
          <StatCard
            label="Admins"
            value={users.filter((u) => u.role === 'admin').length}
            variant="info"
          />
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <div className="flex flex-wrap items-center gap-4 p-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-neutral-700">Role:</label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">All Roles</option>
                <option value="admin">Admin</option>
                <option value="agent">Agent</option>
                <option value="integrator">Integrator</option>
                <option value="bot">Bot</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-neutral-700">Status:</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>

            {(roleFilter || statusFilter !== 'all') && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setRoleFilter('');
                  setStatusFilter('all');
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        </Card>

        {/* Users Table */}
        <Card>
          <CardHeader title={`Users (${total})`} />
          
          {users.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              {roleFilter || statusFilter !== 'all' 
                ? 'No users match the selected filters.'
                : 'No users found. Create your first user to get started.'
              }
            </div>
          ) : (
            <UserTable
              users={users}
              currentUser={currentUser}
              onResetPassword={(user) => setResetPasswordUser(user)}
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-neutral-200 px-6 py-4">
              <div className="text-sm text-neutral-600">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} users
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const pageNum = i + 1;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPage(pageNum)}
                        className={`rounded px-3 py-1 text-sm ${
                          page === pageNum
                            ? 'bg-primary-600 text-white'
                            : 'text-neutral-700 hover:bg-neutral-100'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Modals */}
      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          organizationId={currentUser?.organization_id || ''}
        />
      )}

      {resetPasswordUser && (
        <ResetPasswordModal
          user={resetPasswordUser}
          onClose={() => setResetPasswordUser(null)}
        />
      )}
    </div>
  );
}

// ===== Sub-components =====

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant: 'default' | 'success' | 'warning' | 'info';
}) {
  const colors = {
    default: 'border-neutral-200 bg-white',
    success: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
    info: 'border-blue-200 bg-blue-50',
  };

  return (
    <Card className={colors[variant]}>
      <div className="p-4">
        <p className="text-sm font-medium text-neutral-600">{label}</p>
        <p className="mt-2 text-2xl font-bold text-neutral-900">{value}</p>
      </div>
    </Card>
  );
}