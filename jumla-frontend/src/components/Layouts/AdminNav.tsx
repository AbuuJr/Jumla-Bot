import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '@lib/hooks/useAuth';


export default function AdminNav() {
  const location = useLocation();
  const user = useAuth((state) => state.user);
  const isAdmin = user?.role === 'admin' || user?.role === 'system_owner';


  const navItems = [
    {
      name: 'Dashboard',
      path: '/admin',
      icon: DashboardIcon,
      exact: true,
    },
    {
      name: 'Leads',
      path: '/admin/leads',
      icon: LeadsIcon,
    },
    {
      name: 'Users',
      path: '/admin/users',
      icon: UsersIcon,
      adminOnly: true,
    },
    {
      name: 'Sessions',
      path: '/admin/sessions',
      icon: SessionsIcon,
      adminOnly: true,
    },
    {
      name: 'Audit Logs',
      path: '/admin/audit-logs',
      icon: AuditIcon,
      adminOnly: true,
    },
  ];


  return (
    <nav className="w-64 bg-white border-r border-neutral-200 min-h-screen flex flex-col">
      {/* Header */}
      <div className="px-4 py-5 border-b border-neutral-200">
        <h2 className="text-lg font-semibold text-neutral-900">Admin Panel</h2>
        <p className="text-sm text-neutral-500 mt-1">{user?.full_name || user?.email}</p>
      </div>


      {/* Navigation Items */}
      <div className="flex-1 px-2 py-4 space-y-1">
        {navItems.map((item) => {
          // Hide admin-only items from non-admins
          if (item.adminOnly && !isAdmin) return null;


          const isActive = item.exact
            ? location.pathname === item.path
            : location.pathname.startsWith(item.path);


          return (
            <Link
              key={item.path}
              to={item.path}
              className={`
                flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors
                ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-neutral-700 hover:bg-neutral-100 hover:text-neutral-900'
                }
              `}
            >
              <item.icon className="h-5 w-5" />
              <span className="flex-1">{item.name}</span>
              {item.adminOnly && (
                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                  Admin
                </span>
              )}
            </Link>
          );
        })}
      </div>


      {/* User Info Footer */}
      <div className="px-4 py-4 border-t border-neutral-200">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center">
            <span className="text-sm font-medium text-primary-700">
              {user?.full_name?.charAt(0) || user?.email?.charAt(0) || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-neutral-900 truncate">
              {user?.full_name || 'User'}
            </p>
            <p className="text-xs text-neutral-500 truncate">
              {user?.role === 'system_owner' ? 'System Owner' : user?.role || 'User'}
            </p>
          </div>
        </div>
      </div>
    </nav>
  );
}


// Icons
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


function LeadsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
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



