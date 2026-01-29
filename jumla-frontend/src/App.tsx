import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import ToastContainer from './components/ui/Toast';

// Pages
import Landing from '@pages/Landing/Landing';
import SellerIntake from '@pages/SellerIntake/SellerIntake';
import BuyerInfo from '@pages/BuyerInfo/BuyerInfo';
import Login from '@pages/Auth/Login';
import AdminDashboard from '@pages/Admin/Dashboard';
import LeadList from '@pages/Admin/LeadList/LeadList';
import LeadDetail from '@pages/Admin/LeadDetail/LeadDetail';

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

function App() {
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

                {/* Catch-all redirect */}
                <Route path="*" element={<Navigate to="/" />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
      <ToastContainer />
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

export default App;



