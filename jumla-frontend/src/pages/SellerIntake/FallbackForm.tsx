import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateLead } from '@lib/hooks/useLead';
import Input from '@components/ui/Input';
import Button from '@components/ui/Button';
import Card from '@components/ui/Card';

// ============================================================================
// FallbackForm - Traditional form for users who prefer not to use chat
// ============================================================================

const formSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Phone must be at least 10 digits'),
  address: z.string().min(5, 'Address is required'),
  city: z.string().min(2, 'City is required'),
  state: z.string().length(2, 'State must be 2 characters'),
  zip: z.string().regex(/^\d{5}$/, 'ZIP must be 5 digits'),
  propertyType: z.enum(['single_family', 'condo', 'townhouse', 'multi_family']),
  bedrooms: z.coerce.number().min(1).max(20),
  bathrooms: z.coerce.number().min(1).max(20),
  squareFeet: z.coerce.number().min(100),
  yearBuilt: z.coerce.number().min(1800).max(new Date().getFullYear()),
  motivation: z.string().optional(),
});

type FormData = z.infer<typeof formSchema>;

interface FallbackFormProps {
  onSuccess: (leadId: string) => void;
}

export default function FallbackForm({ onSuccess }: FallbackFormProps) {
  const createLead = useCreateLead();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit: SubmitHandler<FormData> = async (data) => {
    try {
      const response = await createLead.mutateAsync({
        source: 'form',
        seller_info: {
          name: data.name,
          email: data.email,
          phone: data.phone,
          motivation: data.motivation,
        },
        property_info: {
          address: data.address,
          city: data.city,
          state: data.state,
          zip: data.zip,
          property_type: data.propertyType,
          bedrooms: data.bedrooms,
          bathrooms: data.bathrooms,
          square_feet: data.squareFeet,
          year_built: data.yearBuilt,
        },
      });

      onSuccess(response.lead.id);
    } catch (error) {
      console.error('Form submission failed:', error);
    }
  };

  return (
    <Card>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <h2 className="text-2xl font-bold text-neutral-900">Property Information Form</h2>

        {/* Seller Information */}
        <div>
          <h3 className="mb-3 text-lg font-semibold text-neutral-900">Your Information</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Full Name" {...register('name')} error={errors.name?.message} required />
            <Input label="Email" type="email" {...register('email')} error={errors.email?.message} required />
            <Input label="Phone" type="tel" {...register('phone')} error={errors.phone?.message} required />
          </div>
        </div>

        {/* Property Address */}
        <div>
          <h3 className="mb-3 text-lg font-semibold text-neutral-900">Property Address</h3>
          <div className="space-y-4">
            <Input label="Street Address" {...register('address')} error={errors.address?.message} required />
            <div className="grid gap-4 md:grid-cols-3">
              <Input label="City" {...register('city')} error={errors.city?.message} required />
              <Input label="State" {...register('state')} error={errors.state?.message} required maxLength={2} />
              <Input label="ZIP Code" {...register('zip')} error={errors.zip?.message} required maxLength={5} />
            </div>
          </div>
        </div>

        {/* Property Details */}
        <div>
          <h3 className="mb-3 text-lg font-semibold text-neutral-900">Property Details</h3>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-neutral-700">
                Property Type <span className="text-red-500">*</span>
              </label>
              <select
                {...register('propertyType')}
                className="block w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
              >
                <option value="single_family">Single Family</option>
                <option value="condo">Condo</option>
                <option value="townhouse">Townhouse</option>
                <option value="multi_family">Multi-Family</option>
              </select>
              {errors.propertyType && (
                <p className="mt-1 text-sm text-red-600">{errors.propertyType.message}</p>
              )}
            </div>

            <Input
              label="Bedrooms"
              type="number"
              {...register('bedrooms')}
              error={errors.bedrooms?.message}
              required
            />
            <Input
              label="Bathrooms"
              type="number"
              step="0.5"
              {...register('bathrooms')}
              error={errors.bathrooms?.message}
              required
            />
            <Input
              label="Square Feet"
              type="number"
              {...register('squareFeet')}
              error={errors.squareFeet?.message}
              required
            />
            <Input
              label="Year Built"
              type="number"
              {...register('yearBuilt')}
              error={errors.yearBuilt?.message}
              required
            />
          </div>
        </div>

        {/* Additional Info */}
        <div>
          <label htmlFor="motivation" className="mb-1 block text-sm font-medium text-neutral-700">
            Why are you selling? (Optional)
          </label>
          <textarea
            id="motivation"
            {...register('motivation')}
            rows={3}
            className="block w-full rounded-md border border-neutral-300 px-3 py-2 focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
            placeholder="e.g., Relocating for work, downsizing, etc."
          />
        </div>

        {/* Submit */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          isLoading={createLead.isPending}
        >
          Submit & Get My Offer
        </Button>
      </form>
    </Card>
  );
}