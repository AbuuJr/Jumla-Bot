// src/pages/Login.tsx
// Enhanced with session expiry handling and improved error messages


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
// Login Page - Admin authentication with session handling and improved errors
// ============================================================================


const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});


type LoginFormData = z.infer<typeof loginSchema>;


type ErrorType = 'user_not_found' | 'wrong_password' | 'inactive' | 'network' | 'general' | null;


export default function Login() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isAuthenticated, error: authError } = useAuth();
  const toast = useToast();
  const [loginError, setLoginError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<ErrorType>(null);


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
    setErrorType(null);
    
    try {
      await login(data);
      toast.success('Login successful!');
      navigate('/admin');
    } catch (error: any) {
      console.error('Login error:', error);
      
      // Get error message
      const errorMessage = error?.message || error?.response?.data?.detail || 'Login failed. Please try again.';
      
      // Determine error type based on message
      let type: ErrorType = 'general';
      
      if (errorMessage.includes('No account found') || errorMessage.includes('not found')) {
        type = 'user_not_found';
      } else if (errorMessage.includes('deactivated') || errorMessage.includes('inactive') || errorMessage.includes('Account is inactive')) {
        type = 'inactive';
      } else if (errorMessage.includes('Incorrect password') || errorMessage.includes('Incorrect email or password')) {
        type = 'wrong_password';
      } else if (errorMessage.includes('Network error') || error?.status === 0) {
        type = 'network';
      }
      
      setLoginError(errorMessage);
      setErrorType(type);
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
          {/* Enhanced Error Display with Context */}
          {(loginError || authError) && (
            <div className="rounded-md bg-red-50 border border-red-200 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">
                    {loginError || authError}
                  </h3>
                  
                  {/* Context-specific help */}
                  {errorType === 'user_not_found' && (
                    <div className="mt-2 text-sm text-red-700">
                      <p className="font-semibold mb-1">Need access?</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Contact your organization's administrator to request an account</li>
                        <li>If you're setting up a new organization, contact Jumla-bot support</li>
                        <li>Verify you're using the correct email address</li>
                      </ul>
                    </div>
                  )}


                  {errorType === 'inactive' && (
                    <div className="mt-2 text-sm text-red-700">
                      <p className="font-semibold mb-1">Account deactivated</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Your account has been deactivated by an administrator</li>
                        <li>Contact your organization's system administrator for assistance</li>
                        <li>They can reactivate your account if needed</li>
                      </ul>
                    </div>
                  )}


                  {errorType === 'wrong_password' && (
                    <div className="mt-2 text-sm text-red-700">
                      <p className="font-semibold mb-1">Password help</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Make sure Caps Lock is off</li>
                        <li>Check for extra spaces before or after your password</li>
                        <li>Contact your administrator if you've forgotten your password</li>
                      </ul>
                    </div>
                  )}


                  {errorType === 'network' && (
                    <div className="mt-2 text-sm text-red-700">
                      <p className="font-semibold mb-1">Connection issues</p>
                      <ul className="list-disc list-inside space-y-1">
                        <li>Check your internet connection</li>
                        <li>Verify the backend server is running</li>
                        <li>Try refreshing the page</li>
                      </ul>
                    </div>
                  )}
                </div>
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


        {/* Info Box - Admin Access Only */}
        <div className="mt-4 rounded-md bg-blue-50 border border-blue-200 p-3">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-xs text-blue-700">
                <strong>Admin Access Only:</strong> This portal is for authorized administrators,
                agents, and integrators only. Accounts are created and managed by your organization's
                system administrator.
              </p>
            </div>
          </div>
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



