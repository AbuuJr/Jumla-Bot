//3. src/lib/utils/formatters.ts
import { format, formatDistanceToNow, parseISO } from 'date-fns';

// ============================================================================
// Formatting Utilities - Date, currency, and text formatters
// ============================================================================

// ===== Currency Formatting =====
export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatCurrencyCompact(amount: number): string {
  if (amount >= 1000000) {
    return `$${(amount / 1000000).toFixed(1)}M`;
  }
  if (amount >= 1000) {
    return `$${(amount / 1000).toFixed(0)}K`;
  }
  return `$${amount.toLocaleString()}`;
}

// ===== Date Formatting =====
export function formatDate(date: string | Date, formatString: string = 'MMM dd, yyyy'): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatString);
}

export function formatDateTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, 'MMM dd, yyyy h:mm a');
}

export function formatRelativeTime(date: string | Date): string {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(dateObj, { addSuffix: true });
}

// ===== Number Formatting =====
export function formatNumber(num: number): string {
  return num.toLocaleString('en-US');
}

export function formatPercentage(num: number, decimals: number = 0): string {
  return `${(num * 100).toFixed(decimals)}%`;
}

// ===== Text Formatting =====
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength)}...`;
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

export function titleCase(text: string): string {
  return text
    .split(' ')
    .map((word) => capitalize(word))
    .join(' ');
}

// ===== Address Formatting =====
export function formatAddress(
  address?: string,
  city?: string,
  state?: string,
  zip?: string
): string {
  const parts = [address, city, state, zip].filter(Boolean);
  return parts.join(', ');
}

export function formatShortAddress(address?: string, city?: string): string {
  return [address, city].filter(Boolean).join(', ');
}