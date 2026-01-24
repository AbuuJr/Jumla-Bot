// 4. src/lib/constants/routes.ts
// ============================================================================
// Route Constants - Centralized route definitions
// ============================================================================

export const ROUTES = {
  HOME: '/',
  SELL: '/sell',
  BUYERS: '/buyers',
  
  // Auth
  LOGIN: '/auth/login',
  
  // Admin
  ADMIN_DASHBOARD: '/admin',
  ADMIN_LEADS: '/admin/leads',
  ADMIN_LEAD_DETAIL: (id: string) => `/admin/leads/${id}`,
} as const;

// Helper to check if route is admin route
export function isAdminRoute(path: string): boolean {
  return path.startsWith('/admin');
}

// Helper to check if route is public
export function isPublicRoute(path: string): boolean {
  const publicRoutes = [ROUTES.HOME, ROUTES.SELL, ROUTES.BUYERS, ROUTES.LOGIN];
  return publicRoutes.includes(path);
}