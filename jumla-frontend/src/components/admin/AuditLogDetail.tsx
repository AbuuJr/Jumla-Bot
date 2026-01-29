// src/components/admin/AuditLogDetail.tsx
// Detailed view of audit log with before/after comparison

import {
  formatEntityType,
  formatAction,
  getActionColor,
  getEntityIcon,
  getChangedFields,
  formatFieldValue,
} from '@lib/hooks/useAuditLogs';
import Modal from '@components/ui/Modal';
import Badge from '@components/ui/Badge';
import type { AuditLog } from '@lib/api/types';

// ============================================================================
// Audit Log Detail Modal
// ============================================================================

interface AuditLogDetailProps {
  log: AuditLog;
  onClose: () => void;
}

export default function AuditLogDetail({ log, onClose }: AuditLogDetailProps) {
  const changedFields = getChangedFields(log.before, log.after);
  const isSystemAction = log.performed_by?.includes('script');

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Audit Log Details"
      size="xl"
    >
      <div className="space-y-6">
        {/* Header Info */}
        <div className="rounded-lg bg-neutral-50 border border-neutral-200 p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-neutral-600">Performed By</p>
              <div className="mt-1 flex items-center gap-2">
                {isSystemAction ? (
                  <div className="flex h-8 w-8 items-center justify-center rounded bg-yellow-100 text-yellow-700 font-bold">
                    S
                  </div>
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded bg-primary-100 text-primary-700 font-bold">
                    {log.performed_by?.charAt(0).toUpperCase() || '?'}
                  </div>
                )}
                <div>
                  <p className="font-medium text-neutral-900">{log.performed_by}</p>
                  {isSystemAction && <Badge variant="warning">System Script</Badge>}
                </div>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-neutral-600">Timestamp</p>
              <p className="mt-1 text-neutral-900">
                {new Date(log.created_at).toLocaleString()}
              </p>
            </div>

            <div>
              <p className="text-sm font-medium text-neutral-600">Action</p>
              <div className="mt-1">
                <Badge variant={getActionColor(log.action)}>
                  {formatAction(log.action)}
                </Badge>
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-neutral-600">Entity</p>
              <div className="mt-1 flex items-center gap-2">
                <span className="text-xl">{getEntityIcon(log.entity_type)}</span>
                <p className="font-medium text-neutral-900">
                  {formatEntityType(log.entity_type)}
                </p>
              </div>
            </div>

            <div className="col-span-2">
              <p className="text-sm font-medium text-neutral-600">Entity ID</p>
              <code className="mt-1 text-xs text-neutral-900 bg-neutral-100 px-2 py-1 rounded block font-mono">
                {log.entity_id}
              </code>
            </div>

            {log.ip_address && (
              <div className="col-span-2">
                <p className="text-sm font-medium text-neutral-600">IP Address</p>
                <code className="mt-1 text-xs text-neutral-900 bg-neutral-100 px-2 py-1 rounded font-mono">
                  {log.ip_address}
                </code>
              </div>
            )}
          </div>
        </div>

        {/* Before/After Comparison */}
        {(log.before || log.after) ? (
          <div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">
              State Changes
            </h3>

            {changedFields.length > 0 ? (
              <div className="space-y-4">
                {changedFields.map((field) => (
                  <div key={field} className="rounded-lg border border-neutral-200">
                    <div className="bg-neutral-50 px-4 py-2 border-b border-neutral-200">
                      <p className="font-medium text-neutral-900">{field}</p>
                    </div>
                    <div className="grid grid-cols-2 divide-x divide-neutral-200">
                      {/* Before */}
                      <div className="p-4">
                        <p className="text-xs font-medium text-neutral-600 uppercase mb-2">
                          Before
                        </p>
                        <div className="bg-red-50 border border-red-200 rounded p-3">
                          <pre className="text-sm text-red-900 whitespace-pre-wrap break-words">
                            {formatFieldValue(log.before?.[field])}
                          </pre>
                        </div>
                      </div>

                      {/* After */}
                      <div className="p-4">
                        <p className="text-xs font-medium text-neutral-600 uppercase mb-2">
                          After
                        </p>
                        <div className="bg-green-50 border border-green-200 rounded p-3">
                          <pre className="text-sm text-green-900 whitespace-pre-wrap break-words">
                            {formatFieldValue(log.after?.[field])}
                          </pre>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              // No changes (create or delete)
              <div>
                {log.action === 'create' && log.after && (
                  <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                    <p className="text-sm font-medium text-green-900 mb-2">
                      Created with the following data:
                    </p>
                    <pre className="text-xs text-green-800 whitespace-pre-wrap bg-white rounded p-3 overflow-auto max-h-96">
                      {JSON.stringify(log.after, null, 2)}
                    </pre>
                  </div>
                )}

                {log.action === 'delete' && log.before && (
                  <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                    <p className="text-sm font-medium text-red-900 mb-2">
                      Deleted the following data:
                    </p>
                    <pre className="text-xs text-red-800 whitespace-pre-wrap bg-white rounded p-3 overflow-auto max-h-96">
                      {JSON.stringify(log.before, null, 2)}
                    </pre>
                  </div>
                )}

                {!log.before && !log.after && (
                  <div className="rounded-lg bg-neutral-50 border border-neutral-200 p-4 text-center text-neutral-600">
                    No state changes recorded
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-lg bg-neutral-50 border border-neutral-200 p-6 text-center">
            <p className="text-neutral-600">
              No before/after state data available for this log entry.
            </p>
          </div>
        )}

        {/* Raw JSON View (Collapsible) */}
        <details className="rounded-lg border border-neutral-200">
          <summary className="cursor-pointer bg-neutral-50 px-4 py-2 font-medium text-neutral-900 hover:bg-neutral-100">
            View Raw JSON
          </summary>
          <div className="p-4">
            <pre className="text-xs text-neutral-800 whitespace-pre-wrap bg-neutral-900 text-neutral-100 rounded p-4 overflow-auto max-h-96">
              {JSON.stringify(
                {
                  id: log.id,
                  performed_by: log.performed_by,
                  entity_type: log.entity_type,
                  entity_id: log.entity_id,
                  action: log.action,
                  before: log.before,
                  after: log.after,
                  ip_address: log.ip_address,
                  created_at: log.created_at,
                },
                null,
                2
              )}
            </pre>
          </div>
        </details>

        {/* Close Button */}
        <div className="flex justify-end pt-4">
          <button
            onClick={onClose}
            className="rounded-md bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-200"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}