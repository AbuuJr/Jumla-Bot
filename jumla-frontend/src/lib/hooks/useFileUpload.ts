import { useState } from 'react';
import { fileApi } from '@lib/api/clients';

// ============================================================================
// File Upload Hook - Handles two-step upload process
// 1. Request signed URL from backend
// 2. Upload file directly to storage
// ============================================================================

interface UploadProgress {
  filename: string;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
  fileUrl?: string;
}

export function useFileUpload() {
  const [uploads, setUploads] = useState<Map<string, UploadProgress>>(new Map());

  const uploadFile = async (file: File): Promise<string> => {
    const uploadId = `${Date.now()}-${file.name}`;

    // Initialize upload progress
    setUploads((prev) =>
      new Map(prev).set(uploadId, {
        filename: file.name,
        progress: 0,
        status: 'pending',
      })
    );

    try {
      // Step 1: Request signed URL
      setUploads((prev) =>
        new Map(prev).set(uploadId, {
          filename: file.name,
          progress: 10,
          status: 'uploading',
        })
      );

      const { signed_url, file_url } = await fileApi.requestUpload({
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
      });

      // Step 2: Upload to signed URL
      setUploads((prev) =>
        new Map(prev).set(uploadId, {
          filename: file.name,
          progress: 50,
          status: 'uploading',
        })
      );

      await fileApi.uploadToSignedUrl(signed_url, file);

      // Success
      setUploads((prev) =>
        new Map(prev).set(uploadId, {
          filename: file.name,
          progress: 100,
          status: 'success',
          fileUrl: file_url,
        })
      );

      return file_url;
    } catch (error: any) {
      setUploads((prev) =>
        new Map(prev).set(uploadId, {
          filename: file.name,
          progress: 0,
          status: 'error',
          error: error.message || 'Upload failed',
        })
      );
      throw error;
    }
  };

  const clearUpload = (uploadId: string) => {
    setUploads((prev) => {
      const newMap = new Map(prev);
      newMap.delete(uploadId);
      return newMap;
    });
  };

  const clearAllUploads = () => {
    setUploads(new Map());
  };

  return {
    uploads: Array.from(uploads.entries()).map(([id, progress]) => ({ id, ...progress })),
    uploadFile,
    clearUpload,
    clearAllUploads,
  };
}