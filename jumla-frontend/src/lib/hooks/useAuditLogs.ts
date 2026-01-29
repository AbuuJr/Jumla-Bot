// src/lib/hooks/useAuditLogs.ts
// Audit logs hooks with React Query

import { useQuery } from '@tanstack/react-query';
import { auditLogsApi } from '@lib/api/clients';
import type { AuditLog } from '@lib/api/types';

// ============================================================================
// Query Keys
// ============================================================================

export const auditLogKeys = {
  all: ['audit-logs'] as const,
  lists: () => [...auditLogKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...auditLogKeys.lists(), filters] as const,
};

// ============================================================================
// List Audit Logs Hook
// ============================================================================

interface UseAuditLogsParams {
  page?: number;
  page_size?: number;
  entity_type?: string;
  action?: string;
}

export function useAuditLogs(params: UseAuditLogsParams = {}) {
  return useQuery({
    queryKey: auditLogKeys.list(params),
    queryFn: () => auditLogsApi.list(params),
    staleTime: 60000, // 60 seconds - audit logs don't change often
  });
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Format entity type for display
 */
export function formatEntityType(entityType: string): string {
  const mapping: Record<string, string> = {
    user: 'User',
    organization: 'Organization',
    lead: 'Lead',
    offer: 'Offer',
    session: 'Session',
    conversation: 'Conversation',
  };
  return mapping[entityType] || entityType.charAt(0).toUpperCase() + entityType.slice(1);
}

/**
 * Format action for display
 */
export function formatAction(action: string): string {
  return action
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Get action badge color
 */
export function getActionColor(action: string): 'success' | 'warning' | 'error' | 'info' | 'default' {
  const lowerAction = action.toLowerCase();
  
  if (lowerAction.includes('create')) return 'success';
  if (lowerAction.includes('update')) return 'info';
  if (lowerAction.includes('delete') || lowerAction.includes('revoke')) return 'error';
  if (lowerAction.includes('reset')) return 'warning';
  
  return 'default';
}

/**
 * Get entity type icon
 */
export function getEntityIcon(entityType: string): string {
  const icons: Record<string, string> = {
    user: '👤',
    organization: '🏢',
    lead: '📋',
    offer: '💰',
    session: '🔐',
    conversation: '💬',
  };
  return icons[entityType] || '📄';
}

/**
 * Format time ago
 */
export function formatTimeAgo(dateString: string): string {
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
 * Extract changed fields from before/after
 */
export function getChangedFields(before: any, after: any): string[] {
  if (!before || !after) return [];
  
  const changed: string[] = [];
  const allKeys = new Set([...Object.keys(before), ...Object.keys(after)]);
  
  allKeys.forEach(key => {
    if (JSON.stringify(before[key]) !== JSON.stringify(after[key])) {
      changed.push(key);
    }
  });
  
  return changed;
}

/**
 * Format field value for display
 */
export function formatFieldValue(value: any): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
}

/**
 * Check if log has changes to display
 */
export function hasChanges(log: AuditLog): boolean {
  return !!(log.before || log.after);
}

/**
 * Get summary of changes
 */
export function getChangeSummary(log: AuditLog): string {
  const changedFields = getChangedFields(log.before, log.after);
  
  if (changedFields.length === 0) {
    if (log.action === 'create') return 'Created';
    if (log.action === 'delete') return 'Deleted';
    return 'No changes';
  }
  
  if (changedFields.length === 1) {
    return `Changed ${changedFields[0]}`;
  }
  
  return `Changed ${changedFields.length} fields`;
}