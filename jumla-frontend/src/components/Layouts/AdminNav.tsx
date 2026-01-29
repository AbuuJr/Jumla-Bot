// ============================================================================
// 1. Update AdminNav.tsx - Add Sessions Link
// ============================================================================

// src/components/layout/AdminNav.tsx
import { Link, useLocation } from 'react-router-dom';
import { useAuth, useIsAdmin } from '@lib/hooks/useAuth';

export default function AdminNav() {
  const location = useLocation();
  const isAdmin = useIsAdmin();
  const user = useAuth((state) => state.user);

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
    // NEW: Sessions (Phase 3)
    {
      name: 'Sessions',
      path: '/admin/sessions',
      icon: SessionsIcon,
      adminOnly: true, // Admin only
    },
    // FUTURE: Audit Logs (Phase 4)
    // {
    //   name: 'Audit Logs',
    //   path: '/admin/audit-logs',
    //   icon: AuditIcon,
    //   adminOnly: true,
    // },
  ];

  return (
    <nav className="w-64 bg-white border-r border-neutral-200 min-h-screen">
      {/* ... existing header ... */}

      <div className="px-2 py-4">
        {navItems.map((item) => {
          if (item.adminOnly && !isAdmin) return null;

          const isActive = item.exact
            ? location.pathname === item.path
            : location.pathname.startsWith(item.path);

          return (
            <Link key={item.path} to={item.path} className={/* ... */}>
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
              {item.adminOnly && <span className="ml-auto text-xs">Admin</span>}
            </Link>
          );
        })}
      </div>

      {/* ... existing user info ... */}
    </nav>
  );
}

// NEW: Sessions Icon
function SessionsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

// ============================================================================
// 2. Add User Profile Nav (for MySessions)
// ============================================================================

// src/components/layout/UserNav.tsx (if you have a user dropdown)
export function UserDropdown() {
  const user = useAuth((state) => state.user);
  const logout = useAuth((state) => state.logout);
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="...">
        {user?.full_name || user?.email}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 rounded-md bg-white shadow-lg border">
          <Link
            to="/profile"
            className="block px-4 py-2 text-sm hover:bg-neutral-100"
          >
            Profile
          </Link>
          
          {/* NEW: My Sessions Link */}
          <Link
            to="/profile/sessions"
            className="block px-4 py-2 text-sm hover:bg-neutral-100"
          >
            My Sessions
          </Link>

          <button
            onClick={logout}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-neutral-100"
          >
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 3. Update App.tsx - Add Routes
// ============================================================================

// src/App.tsx
import { Routes, Route } from 'react-router-dom';
import Sessions from '@pages/admin/Sessions';
import MySessions from '@pages/profile/MySessions';

function App() {
  return (
    <>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />

        {/* Protected Admin Routes */}
        <Route path="/admin" element={<ProtectedRoute />}>
          <Route index element={<AdminDashboard />} />
          <Route path="leads" element={<Leads />} />
          <Route path="users" element={<Users />} />
          
          {/* NEW: Sessions (Phase 3) */}
          <Route path="sessions" element={<Sessions />} />
          
          {/* FUTURE: Phase 4 */}
          {/* <Route path="audit-logs" element={<AuditLogs />} /> */}
        </Route>

        {/* NEW: User Profile Routes */}
        <Route path="/profile" element={<ProtectedRoute />}>
          <Route path="sessions" element={<MySessions />} />
        </Route>

        <Route path="/" element={<Navigate to="/admin" replace />} />
      </Routes>

      <ToastContainer />
    </>
  );
}

// ============================================================================
// 4. Optional: Add Session Count to Nav Badge
// ============================================================================

// Show active session count in navigation
import { useSessions } from '@lib/hooks/useSessions';

function SessionsNavItem() {
  const user = useAuth((state) => state.user);
  const { data } = useSessions({ user_id: user?.id });
  const activeCount = data?.items.filter(s => s.is_active).length || 0;

  return (
    <Link to="/admin/sessions" className="...">
      <SessionsIcon />
      <span>Sessions</span>
      {activeCount > 0 && (
        <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
          {activeCount}
        </span>
      )}
    </Link>
  );
}

// ============================================================================
// 5. Optional: Add to User Menu in Header
// ============================================================================

// src/components/layout/Header.tsx
export function Header() {
  return (
    <header className="...">
      {/* ... logo, etc ... */}
      
      <div className="flex items-center gap-4">
        {/* Quick access to sessions */}
        <Link
          to="/profile/sessions"
          className="text-sm text-neutral-600 hover:text-neutral-900"
          title="View your active sessions"
        >
          <SessionsIcon className="h-5 w-5" />
        </Link>

        <UserDropdown />
      </div>
    </header>
  );
}