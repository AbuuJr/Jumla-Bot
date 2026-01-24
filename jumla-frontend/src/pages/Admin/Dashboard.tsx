import { Link } from 'react-router-dom';
import { useLeads } from '@lib/hooks/useLead';
import Card, { CardHeader } from '@components/ui/Card';
import Badge from '@components/ui/Badge';
import Spinner from '@components/ui/Spinner';

// ============================================================================
// Admin Dashboard - Overview metrics and recent leads
// ============================================================================

export default function AdminDashboard() {
  const { data: leadsData, isLoading } = useLeads({ page: 1, page_size: 10 });

  if (isLoading) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Spinner size="lg" label="Loading dashboard..." />
      </div>
    );
  }

  const leads = leadsData?.leads || [];
  const total = leadsData?.total || 0;

  // Calculate metrics
  const newLeads = leads.filter((l) => l.status === 'new').length;
  const qualifiedLeads = leads.filter((l) => l.status === 'qualified').length;
  const offersGenerated = leads.filter((l) => l.status === 'offer_generated').length;
  const offersApproved = leads.filter((l) => l.status === 'offer_approved').length;

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto">
        <h1 className="mb-6 text-3xl font-bold text-neutral-900">Dashboard</h1>

        {/* Metrics Grid */}
        <div className="mb-8 grid gap-6 md:grid-cols-4">
          <MetricCard title="Total Leads" value={total} variant="default" />
          <MetricCard title="New Leads" value={newLeads} variant="info" />
          <MetricCard title="Qualified" value={qualifiedLeads} variant="success" />
          <MetricCard title="Offers Generated" value={offersGenerated} variant="warning" />
        </div>

        {/* Recent Leads */}
        <Card>
          <CardHeader title="Recent Leads" />
          
          {leads.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              No leads found. Start by creating a test lead.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-neutral-200 text-left text-sm font-medium text-neutral-700">
                    <th className="pb-3">ID</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Seller</th>
                    <th className="pb-3">Property</th>
                    <th className="pb-3">Created</th>
                    <th className="pb-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="text-sm">
                      <td className="py-3 font-mono text-xs text-neutral-600">
                        {lead.id.slice(0, 8)}...
                      </td>
                      <td className="py-3">
                        <Badge variant={getStatusVariant(lead.status)}>
                          {formatStatus(lead.status)}
                        </Badge>
                      </td>
                      <td className="py-3">
                        {lead.seller_info?.name || lead.seller_info?.email || '—'}
                      </td>
                      <td className="py-3">
                        {lead.property_info?.address || '—'}
                      </td>
                      <td className="py-3 text-neutral-600">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3">
                        <Link
                          to={`/admin/leads/${lead.id}`}
                          className="text-primary-600 hover:text-primary-700 hover:underline"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="mt-6 flex justify-between border-t border-neutral-200 pt-4">
            <Link
              to="/admin/leads"
              className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
            >
              View all leads →
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ===== Sub-components =====
function MetricCard({
  title,
  value,
  variant,
}: {
  title: string;
  value: number;
  variant: 'default' | 'info' | 'success' | 'warning';
}) {
  const colors = {
    default: 'border-neutral-200',
    info: 'border-blue-200 bg-blue-50',
    success: 'border-green-200 bg-green-50',
    warning: 'border-yellow-200 bg-yellow-50',
  };

  return (
    <Card padding="md" className={colors[variant]}>
      <p className="text-sm font-medium text-neutral-600">{title}</p>
      <p className="mt-2 text-3xl font-bold text-neutral-900">{value}</p>
    </Card>
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