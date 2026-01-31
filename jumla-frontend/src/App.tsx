import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import ToastContainer from './components/ui/Toast';
import { useEffect } from 'react';

// Pages - Public
import Landing from '@pages/Landing/Landing';
import SellerIntake from '@pages/SellerIntake/SellerIntake';
import BuyerInfo from '@pages/BuyerInfo/BuyerInfo';

// pages - Admin
import Login from '@pages/Auth/Login';
import AdminDashboard from '@pages/Admin/Dashboard';
import LeadList from '@pages/Admin/LeadList/LeadList';
import LeadDetail from '@pages/Admin/LeadDetail/LeadDetail';
import Users from './pages/Admin/users';
import Sessions from './pages/Admin/Session';
import MySessions from './pages/Profile/MySessions';
import AuditLogs from './pages/Admin/AuditLogs';


// Layout
import Header from '@/components/Layouts/Header';

// Auth hook
import { useAuth } from '@lib/hooks/useAuth';

// Configure React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});


// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/auth/login" />;
}


// Admin-only Route wrapper
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/auth/login" />;
  }
  
  if (user?.role !== 'admin' && user?.role !== 'system_owner') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-neutral-900 mb-2">Access Denied</h1>
          <p className="text-neutral-600 mb-4">You don't have permission to access this page.</p>
          <Navigate to="/admin" />
        </div>
      </div>
    );
  }
  
  return <>{children}</>;
}


function App() {
  const initialize = useAuth((state) => state.initialize);


  // Initialize auth on app load (Phase 1)
  useEffect(() => {
    initialize().catch(console.error);
  }, [initialize]);


  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* Main container with background */}
        <div className="min-h-screen bg-app">
          {/* Overlay for better text readability */}
          <div className="min-h-screen bg-overlay">
            <Header />
            <main>
              <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Landing />} />
                <Route path="/sell" element={<SellerIntake />} />
                <Route path="/buyers" element={<BuyerInfo />} />
                <Route path="/auth/login" element={<Login />} />


                {/* Protected Admin Routes */}
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute>
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/leads"
                  element={
                    <ProtectedRoute>
                      <LeadList />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin/leads/:id"
                  element={
                    <ProtectedRoute>
                      <LeadDetail />
                    </ProtectedRoute>
                  }
                />


                {/* Phase 2: User Management (Admin Only) */}
                <Route
                  path="/admin/users"
                  element={
                    <AdminRoute>
                      <Users />
                    </AdminRoute>
                  }
                />


                {/* Phase 3: Session Management (Admin Only) */}
                <Route
                  path="/admin/sessions"
                  element={
                    <AdminRoute>
                      <Sessions />
                    </AdminRoute>
                  }
                />


                {/* Phase 4: Audit Logs (Admin Only) */}
                <Route
                  path="/admin/audit-logs"
                  element={
                    <AdminRoute>
                      <AuditLogs />
                    </AdminRoute>
                  }
                />


                {/* User Profile Routes */}
                <Route
                  path="/profile/sessions"
                  element={
                    <ProtectedRoute>
                      <MySessions />
                    </ProtectedRoute>
                  }
                />


                {/* Catch-all redirect */}
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </main>
          </div>
        </div>
        
        {/* Toast notifications (Phase 1) */}
        <ToastContainer />
        
        {/* React Query DevTools */}
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </BrowserRouter>
    </QueryClientProvider>
  );
}


export default App;
