import { useState, useRef, useEffect } from 'react';
import { useSendMessage } from '@lib/hooks/useConversation';
import { useCreateLead } from '@lib/hooks/useLead';
import { useFileUpload } from '@lib/hooks/useFileUpload';
import type { Message } from '@lib/api/types';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import FileUpload from './FileUpload';
import Spinner from '@components/ui/Spinner';
import { clsx } from 'clsx';

// ============================================================================
// ChatWidget - Main conversational interface for seller intake
// Handles lead creation, message sending, file uploads, and error states
// ============================================================================

interface ChatWidgetProps {
  className?: string;
  onLeadCreated?: (leadId: string, conversationId: string) => void;
  initialMessages?: Message[];
}

interface PendingMessage {
  id: string;
  content: string;
  timestamp: string;
  status: 'sending' | 'error';
}

export default function ChatWidget({ className, onLeadCreated, initialMessages = [] }: ChatWidgetProps) {
  // State
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [pendingMessages, setPendingMessages] = useState<PendingMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [leadId, setLeadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Hooks
  const createLead = useCreateLead();
  const sendMessage = useSendMessage();
  const { uploads, uploadFile } = useFileUpload();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingMessages]);

  // Restore unsent messages from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('jumla_unsent_messages');
    if (stored) {
      try {
        const unsent = JSON.parse(stored);
        setPendingMessages(unsent);
      } catch (e) {
        console.error('Failed to parse unsent messages', e);
      }
    }
  }, []);

  // Save unsent messages to localStorage
  useEffect(() => {
    if (pendingMessages.length > 0) {
      localStorage.setItem('jumla_unsent_messages', JSON.stringify(pendingMessages));
    } else {
      localStorage.removeItem('jumla_unsent_messages');
    }
  }, [pendingMessages]);

  // Handle sending first message (creates lead)
  const handleFirstMessage = async (content: string, attachments?: string[]) => {
    const tempId = `temp-${Date.now()}`;
    const tempMessage: PendingMessage = {
      id: tempId,
      content,
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    setPendingMessages((prev) => [...prev, tempMessage]);
    setError(null);

    try {
      // Create lead with first message
      const response = await createLead.mutateAsync({
        source: 'chat',
        initial_message: content,
      });

      const { lead, conversation_id } = response;
      setLeadId(lead.id);
      setConversationId(conversation_id);

      // Add user message to UI
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };

      // Add bot welcome message
      const botMessage: Message = {
        id: `msg-bot-${Date.now()}`,
        role: 'assistant',
        content:
          "Thanks for reaching out! I'm here to help you sell your property. Can you tell me a bit more about your home?",
        timestamp: new Date().toISOString(),
      };

      setMessages([userMessage, botMessage]);
      setPendingMessages((prev) => prev.filter((m) => m.id !== tempId));

      onLeadCreated?.(lead.id, conversation_id);
    } catch (err: any) {
      console.error('Failed to create lead:', err);
      setPendingMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: 'error' } : m))
      );
      setError(err.message || 'Failed to send message. Please try again.');
    }
  };

  // Handle subsequent messages
  const handleSendMessage = async (content: string, attachments?: string[]) => {
    if (!leadId) {
      return handleFirstMessage(content, attachments);
    }

    const tempId = `temp-${Date.now()}`;
    const tempMessage: PendingMessage = {
      id: tempId,
      content,
      timestamp: new Date().toISOString(),
      status: 'sending',
    };

    setPendingMessages((prev) => [...prev, tempMessage]);
    setError(null);

    try {
      // Use leadId instead of conversationId
      const response = await sendMessage.mutateAsync({
        leadId, // Changed from conversationId
        data: {
          content,
          attachments,
        },
      });

      // Add both user and bot messages to UI
      setMessages((prev) => [...prev, response.user_message, response.bot_message]);
      setPendingMessages((prev) => prev.filter((m) => m.id !== tempId));
    } catch (err: any) {
      console.error('Failed to send message:', err);
      setPendingMessages((prev) =>
        prev.map((m) => (m.id === tempId ? { ...m, status: 'error' } : m))
      );
      setError(err.message || 'Failed to send message. Please try again.');
    }
  };
  // Retry failed message
  const handleRetry = (messageId: string) => {
    const failedMessage = pendingMessages.find((m) => m.id === messageId);
    if (failedMessage) {
      setPendingMessages((prev) => prev.filter((m) => m.id !== messageId));
      handleSendMessage(failedMessage.content);
    }
  };

  // Delete failed message
  const handleDeleteFailed = (messageId: string) => {
    setPendingMessages((prev) => prev.filter((m) => m.id !== messageId));
  };

  return (
    <div
      className={clsx(
        'flex h-full flex-col rounded-lg border border-neutral-200 bg-white shadow-lg',
        className
      )}
      role="region"
      aria-label="Chat conversation"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-neutral-200 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500" aria-label="Online" />
          <h2 className="text-lg font-semibold text-neutral-900">Jumla-bot Assistant</h2>
        </div>
        {createLead.isPending && <Spinner size="sm" label="Creating conversation..." />}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4" aria-live="polite" aria-atomic="false">
        <MessageList
          messages={messages}
          pendingMessages={pendingMessages}
          onRetry={handleRetry}
          onDelete={handleDeleteFailed}
        />
        <div ref={messagesEndRef} />
      </div>

      {/* Error Banner */}
      {error && (
        <div
          className="border-t border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          <strong className="font-medium">Error:</strong> {error}
        </div>
      )}

      {/* File Upload Area */}
      {uploads.length > 0 && (
        <div className="border-t border-neutral-200 px-4 py-2">
          <FileUpload uploads={uploads} />
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-neutral-200 p-4">
        <MessageInput
          onSend={handleSendMessage}
          onFileUpload={uploadFile}
          disabled={createLead.isPending || sendMessage.isPending}
          placeholder={
            conversationId
              ? 'Type your message...'
              : "Hi! I'm interested in selling my property..."
          }
        />
      </div>
    </div>
  );
}