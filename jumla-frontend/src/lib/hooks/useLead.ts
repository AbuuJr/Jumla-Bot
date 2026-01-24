import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { leadsApi, offersApi } from '@lib/api/clients';
import type { LeadCreateRequest } from '@lib/api/types';

// ============================================================================
// Lead Hooks - React Query hooks for lead CRUD operations
// ============================================================================

// Query Keys
export const leadKeys = {
  all: ['leads'] as const,
  lists: () => [...leadKeys.all, 'list'] as const,
  list: (filters: Record<string, any>) => [...leadKeys.lists(), filters] as const,
  details: () => [...leadKeys.all, 'detail'] as const,
  detail: (id: string) => [...leadKeys.details(), id] as const,
  offer: (leadId: string) => [...leadKeys.all, 'offer', leadId] as const,
};

// ===== Fetch Lead List =====
export function useLeads(params?: {
  page?: number;
  page_size?: number;
  status?: string;
  search?: string;
}) {
  return useQuery({
    queryKey: leadKeys.list(params || {}),
    queryFn: () => leadsApi.list(params),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });
}

// ===== Fetch Single Lead =====
export function useLead(id: string) {
  return useQuery({
    queryKey: leadKeys.detail(id),
    queryFn: () => leadsApi.get(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

// ===== Create Lead =====
export function useCreateLead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: LeadCreateRequest) => leadsApi.create(data),
    onSuccess: () => {
      // Invalidate and refetch leads list
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() });
    },
  });
}

// ===== Update Lead =====
export function useUpdateLead(id: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<LeadCreateRequest>) => leadsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: leadKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() });
    },
  });
}

// ===== Fetch Offer for Lead =====
export function useOffer(leadId: string) {
  return useQuery({
    queryKey: leadKeys.offer(leadId),
    queryFn: () => offersApi.get(leadId),
    enabled: !!leadId,
    retry: false, // Don't retry if offer doesn't exist yet
  });
}

// ===== Generate Offer =====
export function useGenerateOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: offersApi.generate,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: leadKeys.offer(data.lead_id) });
      queryClient.invalidateQueries({ queryKey: leadKeys.detail(data.lead_id) });
    },
  });
}

// ===== Approve Offer =====
export function useApproveOffer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: offersApi.approve,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: leadKeys.offer(data.offer.lead_id) });
      queryClient.invalidateQueries({ queryKey: leadKeys.detail(data.offer.lead_id) });
    },
  });
}