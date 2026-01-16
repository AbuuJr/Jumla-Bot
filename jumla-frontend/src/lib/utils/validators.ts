import { z } from 'zod';

// ============================================================================
// Validation Utilities - Common validation schemas and helpers
// ============================================================================

export const emailSchema = z.string().email('Invalid email address');

export const phoneSchema = z
  .string()
  .regex(/^\d{10}$/, 'Phone must be 10 digits')
  .or(z.string().regex(/^\d{3}-\d{3}-\d{4}$/, 'Phone must be in format XXX-XXX-XXXX'));

export const zipCodeSchema = z
  .string()
  .regex(/^\d{5}$/, 'ZIP code must be 5 digits')
  .or(z.string().regex(/^\d{5}-\d{4}$/, 'ZIP code must be in format XXXXX or XXXXX-XXXX'));

export const currencySchema = z.coerce
  .number()
  .positive('Amount must be positive')
  .max(100000000, 'Amount too large');

// Helper to validate email
export function isValidEmail(email: string): boolean {
  return emailSchema.safeParse(email).success;
}

// Helper to format phone number
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  return phone;
}

// Helper to validate required fields
export function validateRequired<T>(value: T | null | undefined, fieldName: string): T {
  if (value === null || value === undefined || value === '') {
    throw new Error(`${fieldName} is required`);
  }
  return value;
}