import { useMutation, useQueryClient } from '@tanstack/react-query';
import { conversationsApi } from '@lib/api/clients';
import type { SendMessageRequest } from '@lib/api/types';
import { leadKeys } from './useLead';

// ============================================================================
// Conversation Hooks - React Query hooks for chat operations
// ============================================================================

interface SendMessageParams {
  conversationId: string;
  data: SendMessageRequest;
  leadId?: string; // For cache invalidation
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ conversationId, data }: SendMessageParams) =>
      conversationsApi.sendMessage(conversationId, data),
    onSuccess: (_, variables) => {
      // Invalidate lead detail to refresh conversation
      if (variables.leadId) {
        queryClient.invalidateQueries({ queryKey: leadKeys.detail(variables.leadId) });
      }
    },
  });
}