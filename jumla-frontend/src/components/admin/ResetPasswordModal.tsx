// src/components/admin/ResetPasswordModal.tsx
// Modal for resetting user passwords

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useResetPassword } from '@lib/hooks/useUsers';
import Modal from '@components/ui/Modal';
import Input from '@components/ui/Input';
import Button from '@components/ui/Button';
import type { User } from '@lib/api/types';

// ============================================================================
// Reset Password Modal
// ============================================================================

const resetPasswordSchema = z.object({
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string().min(8, 'Password must be at least 8 characters'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ['confirm_password'],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

interface ResetPasswordModalProps {
  user: User;
  onClose: () => void;
}

export default function ResetPasswordModal({ user, onClose }: ResetPasswordModalProps) {
  const { mutate: resetPassword, isPending } = useResetPassword();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    resetPassword(
      {
        email: user.email,
        new_password: data.new_password,
      },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  // Check if this is an admin user
  const isAdminUser = user.role === 'admin';

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Reset Password"
      size="md"
    >
      <div className="space-y-4">
        {/* User Info */}
        <div className="rounded-md bg-neutral-50 border border-neutral-200 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 text-primary-700 font-medium">
              {user.full_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-medium text-neutral-900">
                {user.full_name || 'No name'}
              </p>
              <p className="text-sm text-neutral-600">{user.email}</p>
              <p className="text-xs text-neutral-500">
                Role: {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
              </p>
            </div>
          </div>
        </div>

        {/* Warning for Admin users */}
        {isAdminUser && (
          <div className="rounded-md bg-red-50 border border-red-200 p-4">
            <div className="flex gap-2">
              <svg className="h-5 w-5 flex-shrink-0 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-red-800">
                <p className="font-semibold">Admin Password Reset Restricted</p>
                <p className="mt-1">
                  Admin passwords can only be reset by a System Owner. If you proceed, this action will fail.
                  Please contact your System Owner for admin password resets.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* New Password */}
          <Input
            label="New Password"
            type="password"
            placeholder="Minimum 8 characters"
            autoComplete="new-password"
            {...register('new_password')}
            error={errors.new_password?.message}
            required
          />

          {/* Confirm Password */}
          <Input
            label="Confirm Password"
            type="password"
            placeholder="Re-enter password"
            autoComplete="new-password"
            {...register('confirm_password')}
            error={errors.confirm_password?.message}
            required
          />

          {/* Info */}
          <div className="rounded-md bg-blue-50 border border-blue-200 p-3">
            <div className="flex gap-2">
              <svg className="h-5 w-5 flex-shrink-0 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-blue-800">
                <p className="font-semibold">Security Note</p>
                <p className="mt-1">
                  Resetting the password will:
                </p>
                <ul className="mt-1 list-disc list-inside space-y-1">
                  <li>Immediately update the user's password</li>
                  <li>Revoke all active sessions (logout from all devices)</li>
                  <li>Require the user to login with the new password</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              type="button"
              variant="ghost"
              onClick={onClose}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant={isAdminUser ? 'error' : 'primary'}
              isLoading={isPending}
            >
              {isPending ? 'Resetting...' : 'Reset Password'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
}