// src/pages/profile/MySessions.tsx
// User's own session management - view and revoke personal sessions

import { useSessions } from '@lib/hooks/useSessions';
import { useAuth } from '@lib/hooks/useAuth';
import { useToast } from '@lib/hooks/useToast';
import { authApi } from '@lib/api/clients';
import { useState } from 'react';
import Card, { CardHeader } from '@components/ui/Card';
import Button from '@components/ui/Button';
import Spinner from '@components/ui/Spinner';
import SessionTable from '@components/admin/SessionTable';

// ============================================================================
// My Sessions Page - User's own session management
// ============================================================================

export default function MySessions() {
  const currentUser = useAuth((state) => state.user);
  const logout = useAuth((state) => state.logout);
  const toast = useToast();
  const [isLoggingOutAll, setIsLoggingOutAll] = useState(false);

  // Fetch only current user's sessions
  const { data: sessionsData, isLoading, refetch } = useSessions({
    user_id: currentUser?.id,
    page: 1,
    page_size: 50, // Show all sessions for current user
  });

  const sessions = sessionsData?.items || [];
  const activeSessions = sessions.filter(s => s.is_active).length;

  const handleLogoutAll = async () => {
    if (!confirm('This will log you out from all devices. Continue?')) {
      return;
    }

    setIsLoggingOutAll(true);
    try {
      await authApi.logoutAll();
      toast.success('Logged out from all devices');
      // Current session is also revoked, so logout locally
      await logout();
    } catch (error: any) {
      toast.error(error.message || 'Failed to logout from all devices');
    } finally {
      setIsLoggingOutAll(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading your sessions..." />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto max-w-5xl">
        {/* Header */}
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">My Sessions</h1>
            <p className="mt-1 text-sm text-neutral-600">
              Manage where you're logged in
            </p>
          </div>

          <Button
            variant="error"
            onClick={handleLogoutAll}
            isLoading={isLoggingOutAll}
            disabled={activeSessions === 0}
          >
            {isLoggingOutAll ? 'Logging out...' : 'Logout All Devices'}
          </Button>
        </div>

        {/* Stats */}
        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <StatCard
            label="Active Sessions"
            value={activeSessions}
            variant="success"
          />
          <StatCard
            label="Total Sessions"
            value={sessions.length}
            variant="default"
          />
          <StatCard
            label="Revoked"
            value={sessions.filter(s => !s.is_active).length}
            variant="default"
          />
        </div>

        {/* Info */}
        <div className="mb-6 rounded-lg bg-blue-50 border border-blue-200 p-4">
          <div className="flex gap-3">
            <svg className="h-5 w-5 flex-shrink-0 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <div className="flex-1 text-sm text-blue-800">
              <p className="font-semibold">Security Tips</p>
              <ul className="mt-2 list-disc list-inside space-y-1">
                <li>Review your active sessions regularly</li>
                <li>If you see an unfamiliar device, revoke it immediately</li>
                <li>Sessions expire after 7 days of inactivity</li>
                <li>Logout from all devices if you suspect unauthorized access</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Current Session Alert */}
        <div className="mb-6 rounded-lg bg-green-50 border border-green-200 p-4">
          <div className="flex gap-3">
            <svg className="h-5 w-5 flex-shrink-0 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <div className="text-sm text-green-800">
              <p className="font-semibold">This Device</p>
              <p className="mt-1">
                Your current session is marked with a green "Current Session" badge below.
                Revoking it will log you out immediately.
              </p>
            </div>
          </div>
        </div>

        {/* Sessions Table */}
        <Card>
          <CardHeader title="Your Sessions" />
          
          {sessions.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              No sessions found. This shouldn't happen - please refresh the page.
            </div>
          ) : (
            <SessionTable
              sessions={sessions}
              currentUserId={currentUser?.id}
              showUserColumn={false}
              onRevoked={refetch}
            />
          )}
        </Card>

        {/* Help */}
        <div className="mt-6 rounded-lg bg-neutral-100 border border-neutral-200 p-4">
          <p className="text-sm text-neutral-700">
            <strong>Need help?</strong> If you notice suspicious activity or have security concerns,
            contact your administrator immediately.
          </p>
        </div>
      </div>
    </div>
  );
}

// ===== Sub-components =====

function StatCard({
  label,
  value,s
  variant,
}: {
  label: string;
  value: number;
  variant: 'default' | 'success';
}) {
  const colors = {
    default: 'border-neutral-200 bg-white',
    success: 'border-green-200 bg-green-50',
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