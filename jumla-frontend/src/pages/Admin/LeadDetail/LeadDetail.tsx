import { useParams, useNavigate } from 'react-router-dom';
import { useLead, useOffer, useApproveOffer } from '@lib/hooks/useLead';
import Card, { CardHeader } from '@components/ui/Card';
import Badge from '@components/ui/Badge';
import Button from '@components/ui/Button';
import Spinner from '@components/ui/Spinner';
import OfferCard from './OfferCard';
import { format } from 'date-fns';

// ============================================================================
// LeadDetail - Detailed view of a single lead with conversation and offer
// ============================================================================

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: leadData, isLoading: leadLoading, error: leadError } = useLead(id!);
  const { data: offer, isLoading: offerLoading } = useOffer(id!);
  const approveOffer = useApproveOffer();

  if (leadLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading lead details..." />
      </div>
    );
  }

  if (leadError || !leadData) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Card className="max-w-md text-center">
          <p className="text-red-600">Failed to load lead details.</p>
          <Button className="mt-4" onClick={() => navigate('/admin/leads')}>
            Back to Leads
          </Button>
        </Card>
      </div>
    );
  }

  const { lead, conversation } = leadData;

  const handleApproveOffer = async () => {
    if (!offer) return;

    try {
      await approveOffer.mutateAsync({
        offer_id: offer.id,
        notes: 'Approved from admin dashboard',
      });
      alert('Offer approved successfully!');
    } catch (error) {
      console.error('Failed to approve offer:', error);
      alert('Failed to approve offer. Please try again.');
    }
  };

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate('/admin/leads')}
              className="mb-2 text-sm text-primary-600 hover:text-primary-700 hover:underline"
            >
              ← Back to Leads
            </button>
            <h1 className="text-3xl font-bold text-neutral-900">Lead Details</h1>
            <p className="mt-1 text-sm text-neutral-600">ID: {lead.id}</p>
          </div>
          <Badge variant={getStatusVariant(lead.status)} size="lg">
            {formatStatus(lead.status)}
          </Badge>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left Column: Seller & Property Info */}
          <div className="space-y-6">
            {/* Seller Information */}
            <Card>
              <CardHeader title="Seller Information" />
              <dl className="space-y-3">
                <InfoRow label="Name" value={lead.seller_info?.name} />
                <InfoRow label="Email" value={lead.seller_info?.email} />
                <InfoRow label="Phone" value={lead.seller_info?.phone} />
                <InfoRow label="Motivation" value={lead.seller_info?.motivation} />
                <InfoRow label="Timeline" value={lead.seller_info?.timeline} />
              </dl>
            </Card>

            {/* Property Information */}
            <Card>
              <CardHeader title="Property Information" />
              <dl className="space-y-3">
                <InfoRow label="Address" value={lead.property_info?.address} />
                <InfoRow
                  label="City, State ZIP"
                  value={
                    lead.property_info?.city
                      ? `${lead.property_info.city}, ${lead.property_info.state} ${lead.property_info.zip}`
                      : undefined
                  }
                />
                <InfoRow label="Property Type" value={lead.property_info?.property_type} />
                <InfoRow
                  label="Bed / Bath"
                  value={
                    lead.property_info?.bedrooms
                      ? `${lead.property_info.bedrooms} bed, ${lead.property_info.bathrooms} bath`
                      : undefined
                  }
                />
                <InfoRow label="Square Feet" value={lead.property_info?.square_feet?.toLocaleString()} />
                <InfoRow label="Year Built" value={lead.property_info?.year_built} />
                <InfoRow label="Condition" value={lead.property_info?.condition} />
                <InfoRow
                  label="Asking Price"
                  value={
                    lead.property_info?.asking_price
                      ? `$${lead.property_info.asking_price.toLocaleString()}`
                      : undefined
                  }
                />
              </dl>
            </Card>

            {/* Metadata */}
            <Card>
              <CardHeader title="Metadata" />
              <dl className="space-y-3">
                <InfoRow label="Source" value={lead.source} />
                <InfoRow label="Created" value={format(new Date(lead.created_at), 'PPpp')} />
                <InfoRow label="Last Updated" value={format(new Date(lead.updated_at), 'PPpp')} />
              </dl>
            </Card>
          </div>

          {/* Right Column: Conversation & Offer */}
          <div className="space-y-6">
            {/* Conversation */}
            {conversation && conversation.messages.length > 0 && (
              <Card>
                <CardHeader
                  title="Conversation History"
                  subtitle={`${conversation.messages.length} messages`}
                />
                <div className="max-h-96 space-y-3 overflow-y-auto">
                  {conversation.messages.map((message) => (
                    <div
                      key={message.id}
                      className={clsx(
                        'rounded-lg p-3 text-sm',
                        message.role === 'user' ? 'bg-primary-50' : 'bg-neutral-100'
                      )}
                    >
                      <p className="font-medium text-neutral-900">
                        {message.role === 'user' ? 'Seller' : 'Assistant'}
                      </p>
                      <p className="mt-1 text-neutral-700">{message.content}</p>
                      <p className="mt-1 text-xs text-neutral-500">
                        {format(new Date(message.timestamp), 'h:mm a')}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Offer */}
            {offerLoading ? (
              <Card>
                <div className="flex justify-center py-8">
                  <Spinner size="md" label="Loading offer..." />
                </div>
              </Card>
            ) : offer ? (
              <OfferCard
                offer={offer}
                onApprove={handleApproveOffer}
                isApproving={approveOffer.isPending}
              />
            ) : (
              <Card>
                <CardHeader title="Offer" />
                <p className="text-neutral-600">No offer has been generated yet.</p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ===== Sub-components =====
function InfoRow({ label, value }: { label: string; value?: string | number }) {
  return (
    <div className="flex justify-between border-b border-neutral-100 pb-2">
      <dt className="text-sm font-medium text-neutral-600">{label}</dt>
      <dd className="text-sm text-neutral-900">{value || '—'}</dd>
    </div>
  );
}

// ===== Helper Functions =====
function getStatusVariant(status: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const mapping: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    new: 'info',
    qualifying: 'warning',
    qualified: 'success',
    offer_generated: 'warning',
    offer_approved: 'success',
    closed: 'default',
  };
  return mapping[status] || 'default';
}

function formatStatus(status: string): string {
  return status
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}