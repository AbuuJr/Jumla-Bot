import type { Offer } from '@lib/api/types';
import Card, { CardHeader, CardFooter } from '@components/ui/Card';
import Badge from '@components/ui/Badge';
import Button from '@components/ui/Button';
import { format } from 'date-fns';

// ============================================================================
// OfferCard - Display offer details with approval action
// ============================================================================

interface OfferCardProps {
  offer: Offer;
  onApprove: () => void;
  isApproving?: boolean;
}

export default function OfferCard({ offer, onApprove, isApproving = false }: OfferCardProps) {
  const canApprove = offer.status === 'pending' || offer.status === 'draft';

  return (
    <Card className="border-2 border-primary-200 bg-primary-50">
      <CardHeader title="Generated Offer" />

      {/* Offer Status */}
      <div className="mb-4">
        <Badge variant={getOfferStatusVariant(offer.status)} size="lg">
          {formatOfferStatus(offer.status)}
        </Badge>
      </div>

      {/* Offer Details */}
      <div className="space-y-4">
        <div className="rounded-lg bg-white p-4">
          <p className="text-sm text-neutral-600">Offer Amount</p>
          <p className="text-3xl font-bold text-primary-600">
            ${offer.offer_amount.toLocaleString()}
          </p>
        </div>

        <dl className="space-y-3">
          <OfferRow label="Earnest Money" value={`$${offer.earnest_money.toLocaleString()}`} />
          <OfferRow label="Closing Timeline" value={`${offer.closing_days} days`} />
          <OfferRow
            label="Contingencies"
            value={
              offer.contingencies.length > 0 ? offer.contingencies.join(', ') : 'No contingencies'
            }
          />
        </dl>

        {/* Terms */}
        {offer.terms && (
          <div className="rounded-lg bg-white p-4">
            <p className="mb-2 text-sm font-medium text-neutral-700">Terms & Conditions</p>
            <p className="text-sm text-neutral-600">{offer.terms}</p>
          </div>
        )}

        {/* Metadata */}
        <div className="border-t border-neutral-200 pt-4 text-xs text-neutral-600">
          <p>Generated: {format(new Date(offer.generated_at), 'PPpp')}</p>
          {offer.approved_at && (
            <p>Approved: {format(new Date(offer.approved_at), 'PPpp')}</p>
          )}
          <p>Expires: {format(new Date(offer.expires_at), 'PPpp')}</p>
        </div>
      </div>

      {/* Actions */}
      {canApprove && (
        <CardFooter>
          <Button variant="secondary" size="md" disabled={isApproving}>
            Reject
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={onApprove}
            isLoading={isApproving}
            disabled={isApproving}
          >
            Approve Offer
          </Button>
        </CardFooter>
      )}
    </Card>
  );
}

// ===== Sub-components =====
function OfferRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-sm text-neutral-600">{label}</dt>
      <dd className="text-sm font-medium text-neutral-900">{value}</dd>
    </div>
  );
}

// ===== Helper Functions =====
function getOfferStatusVariant(status: string): 'default' | 'success' | 'warning' | 'error' {
  const mapping: Record<string, 'default' | 'success' | 'warning' | 'error'> = {
    draft: 'default',
    pending: 'warning',
    approved: 'success',
    rejected: 'error',
    expired: 'default',
  };
  return mapping[status] || 'default';
}

function formatOfferStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}