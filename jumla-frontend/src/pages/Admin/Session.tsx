// src/pages/admin/Sessions.tsx
// Admin session management page - view and revoke all org sessions

import { useState } from 'react';
import { useSessions } from '@lib/hooks/useSessions';
import { useAuth, useIsAdmin } from '@lib/hooks/useAuth';
import Card, { CardHeader } from '@components/ui/Card';
import Spinner from '@components/ui/Spinner';
import SessionTable from '@components/admin/SessionTable';

// ============================================================================
// Admin Sessions Page - View all organization sessions
// ============================================================================

export default function Sessions() {
  const isAdmin = useIsAdmin();
  const currentUser = useAuth((state) => state.user);
  
  // Filters
  const [userFilter, setUserFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Fetch sessions
  const { data: sessionsData, isLoading } = useSessions({
    user_id: userFilter || undefined,
    page,
    page_size: pageSize,
  });

  const sessions = sessionsData?.items || [];
  const total = sessionsData?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  if (!isAdmin) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Card className="max-w-md text-center">
          <div className="py-8">
            <h2 className="text-xl font-bold text-neutral-900">Access Denied</h2>
            <p className="mt-2 text-neutral-600">
              You need admin privileges to view all sessions.
            </p>
            <p className="mt-4 text-sm text-neutral-500">
              To view your own sessions, visit your profile settings.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading sessions..." />
      </div>
    );
  }

  // Calculate stats
  const activeSessions = sessions.filter(s => s.is_active).length;
  const expiringSoon = sessions.filter(s => {
    if (!s.is_active) return false;
    const hoursUntilExpiry = (new Date(s.expires_at).getTime() - new Date().getTime()) / (1000 * 60 * 60);
    return hoursUntilExpiry < 24;
  }).length;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-neutral-900">Active Sessions</h1>
          <p className="mt-1 text-sm text-neutral-600">
            View and manage active sessions across your organization
          </p>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          <StatCard
            label="Total Sessions"
            value={total}
            variant="default"
          />
          <StatCard
            label="Active"
            value={activeSessions}
            variant="success"
          />
          <StatCard
            label="Expiring Soon"
            value={expiringSoon}
            variant="warning"
            helpText="< 24 hours"
          />
          <StatCard
            label="Inactive"
            value={total - activeSessions}
            variant="default"
          />
        </div>

        {/* Info Banner */}
        <div className="mb-6 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <div className="flex gap-3">
            <svg className="h-5 w-5 flex-shrink-0 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1 text-sm text-blue-800">
              <p className="font-semibold">About Sessions</p>
              <p className="mt-1">
                Each login creates a new session with a refresh token. Sessions expire after 7 days of inactivity.
                Revoking a session will force the user to login again.
              </p>
            </div>
          </div>
        </div>

        {/* Sessions Table */}
        <Card>
          <CardHeader title={`Sessions (${total})`} />
          
          {sessions.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              No active sessions found.
            </div>
          ) : (
            <SessionTable
              sessions={sessions}
              currentUserId={currentUser?.id}
              showUserColumn={true}
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-neutral-200 px-6 py-4">
              <div className="text-sm text-neutral-600">
                Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} sessions
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                  className="rounded-md border border-neutral-300 px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
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
                
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                  className="rounded-md border border-neutral-300 px-3 py-1 text-sm text-neutral-700 hover:bg-neutral-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

// ===== Sub-components =====

function StatCard({
  label,
  value,
  variant,
  helpText,
}: {
  label: string;
  value: number;
  variant: 'default' | 'success' | 'warning';
  helpText?: string;
}) {
  const colors = {
    default: 'border-neutral-200 bg-white',
    success: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
  };

  return (
    <Card className={colors[variant]}>
      <div className="p-4">
        <p className="text-sm font-medium text-neutral-600">{label}</p>
        <p className="mt-2 text-2xl font-bold text-neutral-900">{value}</p>
        {helpText && (
          <p className="mt-1 text-xs text-neutral-500">{helpText}</p>
        )}
      </div>
    </Card>
  );
}