import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationsApi } from '@lib/api/clients';
import type { SendMessageRequest } from '@lib/api/types';

// ============================================================================
// Conversation Hooks
// ============================================================================

export const conversationKeys = {
  all: ['conversations'] as const,
  lead: (leadId: string) => [...conversationKeys.all, 'lead', leadId] as const,
};

// ===== Fetch Messages for Lead =====
export function useMessages(leadId: string) {
  return useQuery({
    queryKey: conversationKeys.lead(leadId),
    queryFn: () => conversationsApi.getMessages(leadId),
    enabled: !!leadId,
    staleTime: 1000 * 10, // 10 seconds
  });
}

// ===== Send Message =====
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      leadId,
      data,
    }: {
      leadId: string;
      data: SendMessageRequest;
    }) => {
      return conversationsApi.sendMessage(leadId, data);
    },
    onSuccess: (_, variables) => {
      // Invalidate messages for this lead
      queryClient.invalidateQueries({
        queryKey: conversationKeys.lead(variables.leadId),
      });
    },
  });
}