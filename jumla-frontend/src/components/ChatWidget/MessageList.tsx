import type { Message } from '@lib/api/types';
import { clsx } from 'clsx';
import { format } from 'date-fns';
import Button from '@components/ui/Button';

// ============================================================================
// MessageList - Displays conversation messages with retry/delete for errors
// ============================================================================

interface PendingMessage {
  id: string;
  content: string;
  timestamp: string;
  status: 'sending' | 'error';
}

interface MessageListProps {
  messages: Message[];
  pendingMessages: PendingMessage[];
  onRetry: (messageId: string) => void;
  onDelete: (messageId: string) => void;
}

export default function MessageList({
  messages,
  pendingMessages,
  onRetry,
  onDelete,
}: MessageListProps) {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {pendingMessages.map((message) => (
        <PendingMessageBubble
          key={message.id}
          message={message}
          onRetry={onRetry}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

// ===== Message Bubble =====
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';

  return (
    <div className={clsx('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={clsx(
          'max-w-[80%] rounded-lg px-4 py-2',
          isUser ? 'bg-primary-600 text-white' : 'bg-neutral-100 text-neutral-900'
        )}
      >
        <p className="whitespace-pre-wrap break-words text-sm">{message.content}</p>
        {message.attachments && message.attachments.length > 0 && (
          <div className="mt-2 space-y-1">
            
            {message.attachments.map((att) => (      
              <a
                key={att.id}
                href={att.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs underline"
              >
                {att.filename}
              </a>
            ))}
          </div>
        )}
        <p className={clsx('mt-1 text-xs', isUser ? 'text-primary-200' : 'text-neutral-500')}>
          {format(new Date(message.timestamp), 'h:mm a')}
        </p>
      </div>
    </div>
  );
}

// ===== Pending Message Bubble =====
function PendingMessageBubble({
  message,
  onRetry,
  onDelete,
}: {
  message: PendingMessage;
  onRetry: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="flex justify-end">
      <div
        className={clsx(
          'max-w-[80%] rounded-lg px-4 py-2',
          message.status === 'sending'
            ? 'bg-primary-400 text-white opacity-70'
            : 'border-2 border-red-300 bg-red-50 text-red-900'
        )}
      >
        <p className="whitespace-pre-wrap break-words text-sm">{message.content}</p>
        {message.status === 'sending' ? (
          <p className="mt-1 text-xs text-primary-200">Sending...</p>
        ) : (
          <div className="mt-2 flex items-center gap-2">
            <p className="text-xs text-red-600">Failed to send</p>
            <Button size="sm" variant="outline" onClick={() => onRetry(message.id)}>
              Retry
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onDelete(message.id)}>
              Delete
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}