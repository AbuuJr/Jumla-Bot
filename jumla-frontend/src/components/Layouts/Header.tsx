// src/components/Layouts/Header.tsx
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { useAuth } from '@lib/hooks/useAuth';
import { useToast } from '@lib/hooks/useToast';
import Button from '../ui/Button';

// ============================================================================
// Header - Main navigation header
// ============================================================================

export default function Header() {
  const { isAuthenticated, user, logout } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const toast = useToast();


  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Logout failed');
    }
  };


  return (
    <header className="border-b border-neutral-200 bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="text-2xl font-bold text-primary-600">
            Real Estate Wholesaler
          </Link>


          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link to="/" className="text-neutral-600 hover:text-neutral-900 font-medium">
              Home
            </Link>
            <Link to="/sell" className="text-neutral-600 hover:text-neutral-900 font-medium">
              Sell Property
            </Link>
            <Link to="/buyers" className="text-neutral-600 hover:text-neutral-900 font-medium">
              For Buyers
            </Link>
            {isAuthenticated && (
              <Link to="/admin" className="text-neutral-600 hover:text-neutral-900 font-medium">
                Admin
              </Link>
            )}
          </nav>


          {/* User Menu / Login */}
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                {/* Quick Session Access */}
                <Link
                  to="/profile/sessions"
                  className="text-neutral-600 hover:text-neutral-900 p-2 rounded-md hover:bg-neutral-100"
                  title="My Sessions"
                >
                  <SessionsIcon className="h-5 w-5" />
                </Link>


                {/* User Dropdown */}
                <div className="relative">
                  <button
                    onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                    className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-neutral-100 transition-colors"
                  >
                    <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-primary-700">
                        {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                      </span>
                    </div>
                    <span className="text-sm font-medium text-neutral-900 hidden sm:block">
                      {user?.full_name || user?.email?.split('@')[0]}
                    </span>
                    <svg
                      className={`h-4 w-4 text-neutral-500 transition-transform ${
                        isDropdownOpen ? 'rotate-180' : ''
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 9l-7 7-7-7"
                      />
                    </svg>
                  </button>


                  {/* Dropdown Menu */}
                  {isDropdownOpen && (
                    <>
                      {/* Backdrop */}
                      <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsDropdownOpen(false)}
                      />
                      
                      {/* Menu */}
                      <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-20">
                        <div className="py-1">
                          {/* User Info */}
                          <div className="px-4 py-3 border-b border-neutral-200">
                            <p className="text-sm font-medium text-neutral-900">
                              {user?.full_name || 'User'}
                            </p>
                            <p className="text-xs text-neutral-500 truncate">
                              {user?.email}
                            </p>
                            <p className="text-xs text-neutral-400 mt-1">
                              {user?.role === 'system_owner'
                                ? 'System Owner'
                                : user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)}
                            </p>
                          </div>


                          {/* Menu Items */}
                          <Link
                            to="/admin"
                            className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                            onClick={() => setIsDropdownOpen(false)}
                          >
                            <div className="flex items-center gap-2">
                              <DashboardIcon className="h-4 w-4" />
                              <span>Dashboard</span>
                            </div>
                          </Link>


                          <Link
                            to="/profile/sessions"
                            className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                            onClick={() => setIsDropdownOpen(false)}
                          >
                            <div className="flex items-center gap-2">
                              <SessionsIcon className="h-4 w-4" />
                              <span>My Sessions</span>
                            </div>
                          </Link>


                          {/* Admin Menu Items */}
                          {(user?.role === 'admin' || user?.role === 'system_owner') && (
                            <>
                              <div className="border-t border-neutral-200 my-1" />
                              <Link
                                to="/admin/users"
                                className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                                onClick={() => setIsDropdownOpen(false)}
                              >
                                <div className="flex items-center gap-2">
                                  <UsersIcon className="h-4 w-4" />
                                  <span>Manage Users</span>
                                </div>
                              </Link>
                              <Link
                                to="/admin/sessions"
                                className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                                onClick={() => setIsDropdownOpen(false)}
                              >
                                <div className="flex items-center gap-2">
                                  <SessionsIcon className="h-4 w-4" />
                                  <span>All Sessions</span>
                                </div>
                              </Link>
                              <Link
                                to="/admin/audit-logs"
                                className="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100"
                                onClick={() => setIsDropdownOpen(false)}
                              >
                                <div className="flex items-center gap-2">
                                  <AuditIcon className="h-4 w-4" />
                                  <span>Audit Logs</span>
                                </div>
                              </Link>
                            </>
                          )}


                          {/* Logout */}
                          <div className="border-t border-neutral-200 my-1" />
                          <button
                            onClick={() => {
                              setIsDropdownOpen(false);
                              handleLogout();
                            }}
                            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                          >
                            <div className="flex items-center gap-2">
                              <LogoutIcon className="h-4 w-4" />
                              <span>Logout</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </>
            ) : (
              <Link
                to="/auth/login"
                
              >
                <Button variant="outline" size="sm">
                  Login
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}


// Icons
function SessionsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}


function DashboardIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
      />
    </svg>
  );
}


function UsersIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}


function AuditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
      />
    </svg>
  );
}


function LogoutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
      />
    </svg>
  );
}


