// src/components/admin/AuditLogTable.tsx
// Audit log table with expandable details

import { useState } from 'react';
import {
  formatEntityType,
  formatAction,
  getActionColor,
  getEntityIcon,
  formatTimeAgo,
  hasChanges,
  getChangeSummary,
} from '@lib/hooks/useAuditLogs';
import Badge from '@components/ui/Badge';
import AuditLogDetail from '@components/admin/AuditLogDetail';
import type { AuditLog } from '@lib/api/types';

// ============================================================================
// Audit Log Table Component
// ============================================================================

interface AuditLogTableProps {
  logs: AuditLog[];
}

export default function AuditLogTable({ logs }: AuditLogTableProps) {
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-neutral-200 text-left text-sm font-medium text-neutral-700">
              <th className="px-6 py-3">Timestamp</th>
              <th className="px-6 py-3">Performed By</th>
              <th className="px-6 py-3">Action</th>
              <th className="px-6 py-3">Entity</th>
              <th className="px-6 py-3">Entity ID</th>
              <th className="px-6 py-3">Changes</th>
              <th className="px-6 py-3">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {logs.map((log) => {
              const isSystemAction = log.performed_by?.includes('script');

              return (
                <tr key={log.id} className="text-sm hover:bg-neutral-50">
                  {/* Timestamp */}
                  <td className="px-6 py-4">
                    <div className="text-neutral-900">
                      {formatTimeAgo(log.created_at)}
                    </div>
                    <div className="text-xs text-neutral-500">
                      {new Date(log.created_at).toLocaleString()}
                    </div>
                  </td>

                  {/* Performed By */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {isSystemAction ? (
                        <div className="flex h-6 w-6 items-center justify-center rounded bg-yellow-100 text-yellow-700 text-xs font-bold">
                          S
                        </div>
                      ) : (
                        <div className="flex h-6 w-6 items-center justify-center rounded bg-primary-100 text-primary-700 text-xs font-bold">
                          {log.performed_by?.charAt(0).toUpperCase() || '?'}
                        </div>
                      )}
                      <div>
                        <div className="font-medium text-neutral-900">
                          {log.performed_by || 'Unknown'}
                        </div>
                        {isSystemAction && (
                          <Badge variant="warning" className="mt-0.5">
                            System
                          </Badge>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Action */}
                  <td className="px-6 py-4">
                    <Badge variant={getActionColor(log.action)}>
                      {formatAction(log.action)}
                    </Badge>
                  </td>

                  {/* Entity Type */}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getEntityIcon(log.entity_type)}</span>
                      <span className="font-medium text-neutral-900">
                        {formatEntityType(log.entity_type)}
                      </span>
                    </div>
                  </td>

                  {/* Entity ID */}
                  <td className="px-6 py-4">
                    <code className="text-xs text-neutral-600 bg-neutral-100 px-2 py-1 rounded">
                      {log.entity_id.slice(0, 8)}...
                    </code>
                  </td>

                  {/* Changes Summary */}
                  <td className="px-6 py-4">
                    {hasChanges(log) ? (
                      <div className="text-neutral-700">
                        {getChangeSummary(log)}
                      </div>
                    ) : (
                      <span className="text-neutral-500">—</span>
                    )}
                  </td>

                  {/* View Details */}
                  <td className="px-6 py-4">
                    <button
                      onClick={() => setSelectedLog(log)}
                      className="text-primary-600 hover:text-primary-700 hover:underline text-sm font-medium"
                    >
                      View
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Detail Modal */}
      {selectedLog && (
        <AuditLogDetail
          log={selectedLog}
          onClose={() => setSelectedLog(null)}
        />
      )}
    </>
  );
}