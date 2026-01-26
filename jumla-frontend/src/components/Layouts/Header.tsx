import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@lib/hooks/useAuth';
import Button from '@components/ui/Button';
import { clsx } from 'clsx';

// ============================================================================
// Header - Main navigation header
// ============================================================================

export default function Header() {
  const location = useLocation();
  const { isAuthenticated, logout, user } = useAuth();

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header className="border-b border-neutral-200 bg-white shadow-sm">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link to="/" className="text-2xl font-bold text-primary-600">
          Real estate wholesaler
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-6">
          {!isAuthenticated ? (
            <>
              <Link
                to="/sell"
                className={clsx(
                  'text-sm font-medium transition-colors',
                  isActive('/sell')
                    ? 'text-primary-600'
                    : 'text-neutral-700 hover:text-primary-600'
                )}
              >
                Sell Your Home
              </Link>
              <Link
                to="/buyers"
                className={clsx(
                  'text-sm font-medium transition-colors',
                  isActive('/buyers')
                    ? 'text-primary-600'
                    : 'text-neutral-700 hover:text-primary-600'
                )}
              >
                For Buyers
              </Link>
              <Link to="/auth/login">
                <Button variant="outline" size="sm">
                  Admin Login
                </Button>
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/admin"
                className={clsx(
                  'text-sm font-medium transition-colors',
                  isActive('/admin')
                    ? 'text-primary-600'
                    : 'text-neutral-700 hover:text-primary-600'
                )}
              >
                Dashboard
              </Link>
              <Link
                to="/admin/leads"
                className={clsx(
                  'text-sm font-medium transition-colors',
                  location.pathname.startsWith('/admin/leads')
                    ? 'text-primary-600'
                    : 'text-neutral-700 hover:text-primary-600'
                )}
              >
                Leads
              </Link>
              <div className="flex items-center gap-3">
                <span className="text-sm text-neutral-600">{user?.email}</span>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </div>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}