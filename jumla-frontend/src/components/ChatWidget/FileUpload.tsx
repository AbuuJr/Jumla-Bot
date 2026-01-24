import { clsx } from 'clsx';

// ============================================================================
// FileUpload - Display upload progress for files
// ============================================================================

interface Upload {
  id: string;
  filename: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface FileUploadProps {
  uploads: Upload[];
}

export default function FileUpload({ uploads }: FileUploadProps) {
  return (
    <div className="space-y-2">
      {uploads.map((upload) => (
        <div key={upload.id} className="rounded-md border border-neutral-200 p-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-neutral-700">{upload.filename}</span>
            <span
              className={clsx(
                'text-xs',
                upload.status === 'success' && 'text-green-600',
                upload.status === 'error' && 'text-red-600',
                upload.status === 'uploading' && 'text-primary-600'
              )}
            >
              {upload.status === 'success' && '✓ Complete'}
              {upload.status === 'error' && '✗ Failed'}
              {upload.status === 'uploading' && `${upload.progress}%`}
            </span>
          </div>

          {upload.status === 'uploading' && (
            <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-neutral-200">
              <div
                className="h-full bg-primary-600 transition-all duration-300"
                style={{ width: `${upload.progress}%` }}
              />
            </div>
          )}

          {upload.error && <p className="mt-1 text-xs text-red-600">{upload.error}</p>}
        </div>
      ))}
    </div>
  );
}