import { useState, useRef, KeyboardEvent } from 'react';
import Button from '@components/ui/Button';

// ============================================================================
// MessageInput - Text input with file attachment support
// ============================================================================

interface MessageInputProps {
  onSend: (content: string, attachments?: string[]) => void;
  onFileUpload: (file: File) => Promise<string>;
  disabled?: boolean;
  placeholder?: string;
}

export default function MessageInput({
  onSend,
  onFileUpload,
  disabled = false,
  placeholder = 'Type your message...',
}: MessageInputProps) {
  const [content, setContent] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = () => {
    if (!content.trim() && attachments.length === 0) return;

    onSend(content.trim(), attachments.length > 0 ? attachments : undefined);
    setContent('');
    setAttachments([]);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Send on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      const file = files[0];
      const fileUrl = await onFileUpload(file);
      setAttachments((prev) => [...prev, fileUrl]);
    } catch (error) {
      console.error('File upload failed:', error);
    } finally {
      setIsUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);

    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  return (
    <div className="flex flex-col gap-2">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {attachments.map((url, idx) => (
            <div
              key={idx}
              className="flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-1 text-xs"
            >
              <span>📎 File {idx + 1}</span>
              <button
                onClick={() => setAttachments((prev) => prev.filter((_, i) => i !== idx))}
                className="text-neutral-500 hover:text-neutral-700"
                aria-label="Remove attachment"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isUploading}
          rows={1}
          className="flex-1 resize-none rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-neutral-100"
          aria-label="Message input"
          style={{ maxHeight: '120px' }}
        />

        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          disabled={disabled || isUploading}
          className="hidden"
          accept="image/*,application/pdf,.doc,.docx"
          aria-label="File upload input"
        />

        <Button
          variant="secondary"
          size="md"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isUploading}
          isLoading={isUploading}
          aria-label="Attach file"
        >
          📎
        </Button>

        <Button
          variant="primary"
          size="md"
          onClick={handleSend}
          disabled={disabled || isUploading || (!content.trim() && attachments.length === 0)}
          aria-label="Send message"
        >
          Send
        </Button>
      </div>

      <p className="text-xs text-neutral-500">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  );
}