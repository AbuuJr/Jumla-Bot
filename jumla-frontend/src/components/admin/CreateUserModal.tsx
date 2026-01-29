// src/components/admin/CreateUserModal.tsx
// Modal for creating new users

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateUser } from '@lib/hooks/useUsers';
import Modal from '@components/ui/Modal';
import Input from '@components/ui/Input';
import Button from '@components/ui/Button';

// ============================================================================
// Create User Modal
// ============================================================================

const createUserSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  full_name: z.string().optional(),
  role: z.enum(['admin', 'agent', 'integrator', 'bot'], {
    required_error: 'Please select a role',
  }),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

interface CreateUserModalProps {
  onClose: () => void;
  organizationId: string;
}

export default function CreateUserModal({ onClose, organizationId }: CreateUserModalProps) {
  const { mutate: createUser, isPending } = useCreateUser();

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      role: 'agent',
    },
  });

  const selectedRole = watch('role');

  const onSubmit = async (data: CreateUserFormData) => {
    createUser(
      {
        ...data,
        organization_id: organizationId,
      },
      {
        onSuccess: () => {
          onClose();
        },
      }
    );
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Create New User"
      size="md"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Email */}
        <Input
          label="Email"
          type="email"
          placeholder="user@example.com"
          autoComplete="email"
          {...register('email')}
          error={errors.email?.message}
          required
        />

        {/* Full Name */}
        <Input
          label="Full Name"
          type="text"
          placeholder="John Doe"
          autoComplete="name"
          {...register('full_name')}
          error={errors.full_name?.message}
        />

        {/* Role */}
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1">
            Role <span className="text-red-500">*</span>
          </label>
          <select
            {...register('role')}
            className={`w-full rounded-md border px-3 py-2 focus:outline-none focus:ring-2 ${
              errors.role
                ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                : 'border-neutral-300 focus:border-primary-500 focus:ring-primary-200'
            }`}
          >
            <option value="">Select a role</option>
            <option value="admin">Admin</option>
            <option value="agent">Agent</option>
            <option value="integrator">Integrator</option>
            <option value="bot">Bot</option>
          </select>
          {errors.role && (
            <p className="mt-1 text-sm text-red-600">{errors.role.message}</p>
          )}

          {/* Role descriptions */}
          <div className="mt-2 text-xs text-neutral-600">
            {selectedRole === 'admin' && (
              <p className="rounded bg-red-50 border border-red-200 p-2">
                ⚠️ <strong>Admin:</strong> Full access to organization. Can manage users, view all data.
              </p>
            )}
            {selectedRole === 'agent' && (
              <p className="rounded bg-blue-50 border border-blue-200 p-2">
                <strong>Agent:</strong> Can manage leads, create conversations, view offers.
              </p>
            )}
            {selectedRole === 'integrator' && (
              <p className="rounded bg-yellow-50 border border-yellow-200 p-2">
                <strong>Integrator:</strong> Can read leads and offers, create webhooks for integrations.
              </p>
            )}
            {selectedRole === 'bot' && (
              <p className="rounded bg-neutral-50 border border-neutral-200 p-2">
                <strong>Bot:</strong> Automated user for system interactions. Can read leads and create conversations.
              </p>
            )}
          </div>
        </div>

        {/* Password */}
        <Input
          label="Password"
          type="password"
          placeholder="Minimum 8 characters"
          autoComplete="new-password"
          {...register('password')}
          error={errors.password?.message}
          required
          helperText="User will be required to change this password on first login"
        />

        {/* Warning for Admin */}
        {selectedRole === 'admin' && (
          <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
            <div className="flex gap-2">
              <svg className="h-5 w-5 flex-shrink-0 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              <div className="text-sm text-yellow-800">
                <p className="font-semibold">Creating an Admin User</p>
                <p className="mt-1">
                  Admin users have full access to the organization. Only System Owners can reset admin passwords.
                </p>
              </div>
            </div>
          </div>
        )}

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
            variant="primary"
            isLoading={isPending}
          >
            {isPending ? 'Creating...' : 'Create User'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}