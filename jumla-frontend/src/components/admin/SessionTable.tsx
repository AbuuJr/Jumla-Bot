// src/components/admin/SessionTable.tsx
// Session table component - displays sessions with revoke action

import { useState } from 'react';
import { useRevokeSession, formatDevice, formatTimeAgo } from '@lib/hooks/useSessions';
import Badge from '@components/ui/Badge';
import Button from '@components/ui/Button';
import type { Session } from '@lib/api/types';

// ============================================================================
// Session Table Component
// ============================================================================

interface SessionTableProps {
  sessions: Session[];
  currentUserId?: string;
  showUserColumn?: boolean;
  onRevoked?: () => void;
}

export default function SessionTable({
  sessions,
  currentUserId,
  showUserColumn = false,
  onRevoked,
}: SessionTableProps) {
  const { mutate: revokeSession, isPending } = useRevokeSession();
  const [confirmRevoke, setConfirmRevoke] = useState<string | null>(null);

  const handleRevoke = (sessionId: string) => {
    if (confirmRevoke === sessionId) {
      revokeSession(sessionId, {
        onSuccess: () => {
          setConfirmRevoke(null);
          onRevoked?.();
        },
      });
    } else {
      setConfirmRevoke(sessionId);
      // Auto-cancel after 3 seconds
      setTimeout(() => setConfirmRevoke(null), 3000);
    }
  };

  // Determine if this is likely the current session
  // Most recent session for the current user is probably the current one
  const currentSessionId = sessions
    .filter(s => s.user_id === currentUserId && s.is_active)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0]?.id;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-neutral-200 text-left text-sm font-medium text-neutral-700">
            {showUserColumn && <th className="px-6 py-3">User</th>}
            <th className="px-6 py-3">Device</th>
            <th className="px-6 py-3">IP Address</th>
            <th className="px-6 py-3">Created</th>
            <th className="px-6 py-3">Last Used</th>
            <th className="px-6 py-3">Expires</th>
            <th className="px-6 py-3">Status</th>
            <th className="px-6 py-3">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-100">
          {sessions.map((session) => {
            const isCurrentSession = session.id === currentSessionId;
            const isExpired = new Date(session.expires_at) < new Date();
            const expiresIn = getExpiresIn(session.expires_at);

            return (
              <tr
                key={session.id}
                className={`text-sm hover:bg-neutral-50 ${
                  isCurrentSession ? 'bg-green-50' : ''
                }`}
              >
                {/* User Column (admin view only) */}
                {showUserColumn && (
                  <td className="px-6 py-4">
                    <div className="font-medium text-neutral-900">
                      User {session.user_id.slice(0, 8)}
                    </div>
                  </td>
                )}

                {/* Device */}
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <DeviceIcon userAgent={session.user_agent} />
                    <div>
                      <div className="font-medium text-neutral-900">
                        {formatDevice(session.user_agent)}
                      </div>
                      {isCurrentSession && (
                        <Badge variant="success" className="mt-1">
                          Current Session
                        </Badge>
                      )}
                    </div>
                  </div>
                </td>

                {/* IP Address */}
                <td className="px-6 py-4 font-mono text-xs text-neutral-600">
                  {session.ip_address || '—'}
                </td>

                {/* Created */}
                <td className="px-6 py-4 text-neutral-600">
                  <div>{formatTimeAgo(session.created_at)}</div>
                  <div className="text-xs text-neutral-500">
                    {new Date(session.created_at).toLocaleString()}
                  </div>
                </td>

                {/* Last Used */}
                <td className="px-6 py-4 text-neutral-600">
                  <div>{formatTimeAgo(session.last_used_at)}</div>
                  {session.last_used_at && (
                    <div className="text-xs text-neutral-500">
                      {new Date(session.last_used_at).toLocaleString()}
                    </div>
                  )}
                </td>

                {/* Expires */}
                <td className="px-6 py-4">
                  <div className={getExpiresColor(session.expires_at)}>
                    {expiresIn}
                  </div>
                  <div className="text-xs text-neutral-500">
                    {new Date(session.expires_at).toLocaleString()}
                  </div>
                </td>

                {/* Status */}
                <td className="px-6 py-4">
                  <Badge variant={session.is_active && !isExpired ? 'success' : 'default'}>
                    {session.is_active && !isExpired ? 'Active' : 'Revoked'}
                  </Badge>
                </td>

                {/* Actions */}
                <td className="px-6 py-4">
                  {session.is_active && !isExpired ? (
                    <div className="flex items-center gap-2">
                      <Button
                        variant={confirmRevoke === session.id ? 'error' : 'ghost'}
                        size="sm"
                        onClick={() => handleRevoke(session.id)}
                        disabled={isPending}
                      >
                        {confirmRevoke === session.id ? 'Confirm?' : 'Revoke'}
                      </Button>

                      {isCurrentSession && (
                        <span className="text-xs text-neutral-500 italic">
                          (Will logout)
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-neutral-500">
                      Inactive
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ===== Helper Components =====

function DeviceIcon({ userAgent }: { userAgent: string | null }) {
  const isMobile = userAgent?.includes('Mobile');
  
  if (isMobile) {
    return (
      <svg className="h-5 w-5 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
    );
  }
  
  return (
    <svg className="h-5 w-5 text-neutral-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    </svg>
  );
}

// ===== Helper Functions =====

function getExpiresIn(expiresAt: string): string {
  const now = new Date();
  const expires = new Date(expiresAt);
  const diff = expires.getTime() - now.getTime();
  
  if (diff < 0) return 'Expired';
  
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h`;
  
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  return `${minutes}m`;
}

function getExpiresColor(expiresAt: string): string {
  const now = new Date();
  const expires = new Date(expiresAt);
  const hoursUntilExpiry = (expires.getTime() - now.getTime()) / (1000 * 60 * 60);
  
  if (hoursUntilExpiry < 0) return 'text-neutral-500 line-through';
  if (hoursUntilExpiry < 24) return 'text-yellow-600 font-medium';
  return 'text-green-600';
}