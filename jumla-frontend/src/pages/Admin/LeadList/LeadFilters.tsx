import { useState } from 'react';
import Input from '@components/ui/Input';
import Button from '@components/ui/Button';
import { clsx } from 'clsx';

// ============================================================================
// LeadFilters - Filter and search controls for lead list
// ============================================================================

interface LeadFiltersProps {
  filters: {
    status: string;
    search: string;
  };
  onFilterChange: (filters: { status?: string; search?: string }) => void;
  className?: string;
}

export default function LeadFilters({ filters, onFilterChange, className }: LeadFiltersProps) {
  const [searchInput, setSearchInput] = useState(filters.search);

  const handleStatusChange = (status: string) => {
    onFilterChange({ status: status === filters.status ? '' : status });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onFilterChange({ search: searchInput });
  };

  const handleClearFilters = () => {
    setSearchInput('');
    onFilterChange({ status: '', search: '' });
  };

  const statusOptions = [
    { value: 'new', label: 'New' },
    { value: 'qualifying', label: 'Qualifying' },
    { value: 'qualified', label: 'Qualified' },
    { value: 'offer_generated', label: 'Offer Generated' },
    { value: 'offer_approved', label: 'Offer Approved' },
    { value: 'closed', label: 'Closed' },
  ];

  const hasActiveFilters = filters.status || filters.search;

  return (
    <div className={clsx('rounded-lg border border-neutral-200 bg-white p-4', className)}>
      {/* Search Bar */}
      <form onSubmit={handleSearchSubmit} className="mb-4 flex gap-2">
        <Input
          placeholder="Search by seller name, email, or address..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1"
        />
        <Button type="submit" variant="primary">
          Search
        </Button>
      </form>

      {/* Status Filters */}
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Filter by Status:</p>
        <div className="flex flex-wrap gap-2">
          {statusOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => handleStatusChange(option.value)}
              className={clsx(
                'rounded-full border px-4 py-1.5 text-sm font-medium transition-colors',
                filters.status === option.value
                  ? 'border-primary-600 bg-primary-600 text-white'
                  : 'border-neutral-300 bg-white text-neutral-700 hover:border-primary-400 hover:bg-primary-50'
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <div className="mt-4 text-center">
          <button
            onClick={handleClearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 hover:underline"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}