// src/pages/Login.tsx
// Enhanced with session expiry handling

import { useState, useEffect } from 'react';
import { useNavigate, Navigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '@lib/hooks/useAuth';
import { useToast } from '@lib/hooks/useToast';
import Input from '@components/ui/Input';
import Button from '@components/ui/Button';
import Card from '@components/ui/Card';

// ============================================================================
// Login Page - Admin authentication with session handling
// ============================================================================

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated, error: authError } = useAuth();
  const toast = useToast();
  const [loginError, setLoginError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  // Check for session expiry message
  useEffect(() => {
    const sessionExpired = searchParams.get('session_expired');
    if (sessionExpired === 'true') {
      toast.warning('Your session has expired. Please login again.');
      // Clean up URL
      window.history.replaceState({}, '', '/login');
    }
  }, [searchParams, toast]);

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/admin" />;
  }

  const onSubmit = async (data: LoginFormData) => {
    setLoginError(null);
    try {
      await login(data);
      toast.success('Login successful!');
      navigate('/admin');
    } catch (error: any) {
      const errorMessage = error.message || 'Login failed. Please try again.';
      setLoginError(errorMessage);
      toast.error(errorMessage);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-64px)] items-center justify-center bg-neutral-50 px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-neutral-900">Admin Login</h1>
          <p className="mt-2 text-sm text-neutral-600">
            Sign in to access the admin dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {(loginError || authError) && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800" role="alert">
              <div className="flex items-start gap-2">
                <svg className="h-5 w-5 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>{loginError || authError}</span>
              </div>
            </div>
          )}

          <Input
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="admin@example.com"
            {...register('email')}
            error={errors.email?.message}
            required
          />

          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            {...register('password')}
            error={errors.password?.message}
            required
          />

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            isLoading={isSubmitting}
          >
            {isSubmitting ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>

        <div className="mt-6 space-y-2 text-center text-sm text-neutral-600">
          <p className="font-semibold">Need credentials?</p>
          <p className="text-xs">
            Contact your system administrator or email{' '}
            <a 
              href="mailto:abuu.markets@gmail.com"
              className="text-primary-600 hover:text-primary-700 hover:underline"
            >
              abuu.markets@gmail.com
            </a>
            {' '}for account creation.
          </p>
        </div>

        {/* Security note */}
        <div className="mt-4 rounded-md bg-neutral-100 border border-neutral-200 p-3">
          <p className="text-xs text-neutral-600 text-center">
            🔒 Secure login with session management
          </p>
        </div>
      </Card>
    </div>
  );
}

