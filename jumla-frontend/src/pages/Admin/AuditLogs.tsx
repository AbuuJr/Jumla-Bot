// src/pages/admin/AuditLogs.tsx
// Audit logs page - view all organization actions

import { useState } from 'react';
import { useAuditLogs } from '@lib/hooks/useAuditLogs';
import { useAuth, useIsAdmin } from '@lib/hooks/useAuth';
import Card, { CardHeader } from '@components/ui/Card';
import Button from '@components/ui/Button';
import Spinner from '@components/ui/Spinner';
import AuditLogTable from '@components/admin/AuditLogTable';

// ============================================================================
// Audit Logs Page - Organization audit trail
// ============================================================================

export default function AuditLogs() {
  const isAdmin = useIsAdmin();
  
  // Filters
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('');
  const [actionFilter, setActionFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 50; // Show more logs per page

  // Fetch audit logs
  const { data: logsData, isLoading } = useAuditLogs({
    page,
    page_size: pageSize,
    entity_type: entityTypeFilter || undefined,
    action: actionFilter || undefined,
  });

  const logs = logsData?.items || [];
  const total = logsData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  if (!isAdmin) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Card className="max-w-md text-center">
          <div className="py-8">
            <h2 className="text-xl font-bold text-neutral-900">Access Denied</h2>
            <p className="mt-2 text-neutral-600">
              You need admin privileges to view audit logs.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading audit logs..." />
      </div>
    );
  }

  // Calculate stats
  const last24h = logs.filter(log => {
    const logDate = new Date(log.created_at);
    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
    return logDate > yesterday;
  }).length;

  const userActions = logs.filter(log => log.entity_type === 'user').length;
  const systemActions = logs.filter(log => log.performed_by === 'system_owner_script').length;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-neutral-900">Audit Logs</h1>
          <p className="mt-1 text-sm text-neutral-600">
            Complete audit trail of all actions in your organization
          </p>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <StatCard
            label="Total Logs"
            value={total}
            variant="default"
          />
          <StatCard
            label="Last 24 Hours"
            value={last24h}
            variant="info"
          />
          <StatCard
            label="User Actions"
            value={userActions}
            variant="success"
          />
          <StatCard
            label="System Actions"
            value={systemActions}
            variant="warning"
          />
        </div>

        {/* Info Banner */}
        <div className="mb-6 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <div className="flex gap-3">
            <svg className="h-5 w-5 flex-shrink-0 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1 text-sm text-blue-800">
              <p className="font-semibold">About Audit Logs</p>
              <p className="mt-1">
                All actions performed in your organization are logged here with before/after states.
                This provides a complete audit trail for compliance and security monitoring.
              </p>
            </div>
          </div>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <div className="flex flex-wrap items-center gap-4 p-4">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-neutral-700">Entity Type:</label>
              <select
                value={entityTypeFilter}
                onChange={(e) => setEntityTypeFilter(e.target.value)}
                className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">All Types</option>
                <option value="user">User</option>
                <option value="organization">Organization</option>
                <option value="lead">Lead</option>
                <option value="offer">Offer</option>
                <option value="session">Session</option>
                <option value="conversation">Conversation</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-neutral-700">Action:</label>
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="rounded-md border border-neutral-300 px-3 py-1.5 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              >
                <option value="">All Actions</option>
                <option value="create">Create</option>
                <option value="update">Update</option>
                <option value="delete">Delete</option>
                <option value="reset_password">Reset Password</option>
                <option value="deactivate">Deactivate</option>
              </select>
            </div>

            {(entityTypeFilter || actionFilter) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEntityTypeFilter('');
                  setActionFilter('');
                }}
              >
                Clear Filters
              </Button>
            )}

            <div className="ml-auto text-sm text-neutral-600">
              Showing {logs.length} of {total} logs
            </div>
          </div>
        </Card>

        {/* Audit Logs Table */}
        <Card>
          <CardHeader title={`Audit Trail (${total})`} />
          
          {logs.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              {entityTypeFilter || actionFilter
                ? 'No audit logs match the selected filters.'
                : 'No audit logs found.'
              }
            </div>
          ) : (
            <AuditLogTable logs={logs} />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-neutral-200 px-6 py-4">
              <div className="text-sm text-neutral-600">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} logs
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

        {/* Help */}
        <div className="mt-6 rounded-lg bg-neutral-100 border border-neutral-200 p-4">
          <p className="text-sm text-neutral-700">
            <strong>Compliance Note:</strong> Audit logs are immutable and cannot be deleted or modified.
            They are retained for compliance and security purposes. Click on any log entry to view detailed before/after changes.
          </p>
        </div>
      </div>
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