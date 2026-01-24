import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useLeads } from '@lib/hooks/useLead';
import Card from '@components/ui/Card';
import Badge from '@components/ui/Badge';
import Button from '@components/ui/Button';
import Spinner from '@components/ui/Spinner';
import LeadFilters from './LeadFilters';

// ============================================================================
// LeadList - Filterable, sortable list of all leads
// ============================================================================

export default function LeadList() {
  const [filters, setFilters] = useState({
    page: 1,
    page_size: 20,
    status: '',
    search: '',
  });

  const { data, isLoading, error } = useLeads(filters);

  const leads = data?.leads || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / filters.page_size);

  const handleFilterChange = (newFilters: Partial<typeof filters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters, page: 1 }));
  };

  const handlePageChange = (newPage: number) => {
    setFilters((prev) => ({ ...prev, page: newPage }));
  };

  if (error) {
    return (
      <div className="flex min-h-[calc(100vh-64px)] items-center justify-center">
        <Card className="max-w-md text-center">
          <p className="text-red-600">Failed to load leads. Please try again.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-64px)] bg-neutral-50 p-6">
      <div className="container mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-neutral-900">Leads</h1>
          <div className="text-sm text-neutral-600">
            Showing {leads.length} of {total} total leads
          </div>
        </div>

        {/* Filters */}
        <LeadFilters
          filters={filters}
          onFilterChange={handleFilterChange}
          className="mb-6"
        />

        {/* Leads Table */}
        <Card>
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" label="Loading leads..." />
            </div>
          ) : leads.length === 0 ? (
            <div className="py-12 text-center text-neutral-500">
              No leads found. Try adjusting your filters.
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-neutral-200 text-left text-sm font-medium text-neutral-700">
                      <th className="pb-3 pr-4">Lead ID</th>
                      <th className="pb-3 pr-4">Status</th>
                      <th className="pb-3 pr-4">Seller Name</th>
                      <th className="pb-3 pr-4">Email</th>
                      <th className="pb-3 pr-4">Property Address</th>
                      <th className="pb-3 pr-4">Source</th>
                      <th className="pb-3 pr-4">Created</th>
                      <th className="pb-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-100">
                    {leads.map((lead) => (
                      <tr key={lead.id} className="text-sm hover:bg-neutral-50">
                        <td className="py-3 pr-4">
                          <code className="rounded bg-neutral-100 px-2 py-1 text-xs">
                            {lead.id.slice(0, 8)}
                          </code>
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant={getStatusVariant(lead.status)}>
                            {formatStatus(lead.status)}
                          </Badge>
                        </td>
                        <td className="py-3 pr-4">{lead.seller_info?.name || '—'}</td>
                        <td className="py-3 pr-4">{lead.seller_info?.email || '—'}</td>
                        <td className="py-3 pr-4">
                          {lead.property_info?.address
                            ? `${lead.property_info.address}, ${lead.property_info.city}`
                            : '—'}
                        </td>
                        <td className="py-3 pr-4">
                          <Badge variant="default" size="sm">
                            {lead.source}
                          </Badge>
                        </td>
                        <td className="py-3 pr-4 text-neutral-600">
                          {new Date(lead.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3">
                          <Link
                            to={`/admin/leads/${lead.id}`}
                            className="text-primary-600 hover:text-primary-700 hover:underline"
                          >
                            View Details
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-6 flex items-center justify-between border-t border-neutral-200 pt-4">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handlePageChange(filters.page - 1)}
                    disabled={filters.page === 1}
                  >
                    Previous
                  </Button>

                  <span className="text-sm text-neutral-600">
                    Page {filters.page} of {totalPages}
                  </span>

                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => handlePageChange(filters.page + 1)}
                    disabled={filters.page >= totalPages}
                  >
                    Next
                  </Button>
                </div>
              )}
            </>
          )}
        </Card>
      </div>
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