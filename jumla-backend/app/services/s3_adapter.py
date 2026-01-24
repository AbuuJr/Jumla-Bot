# ========================================
# app/services/s3_adapter.py
# ========================================
"""
S3 storage adapter (AWS S3 or MinIO)
"""
from typing import Optional, BinaryIO
import logging
import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class S3Adapter:
    """S3-compatible storage adapter"""
    
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket)
                logger.info(f"Created S3 bucket: {self.bucket}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        file_key: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload file to S3
        
        Returns:
            File URL if successful, None otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type
            
            self.client.upload_fileobj(
                file_data,
                self.bucket,
                file_key,
                ExtraArgs=extra_args
            )
            
            # Generate URL
            if settings.S3_ENDPOINT_URL:
                url = f"{settings.S3_ENDPOINT_URL}/{self.bucket}/{file_key}"
            else:
                url = f"https://{self.bucket}.s3.{settings.S3_REGION}.amazonaws.com/{file_key}"
            
            logger.info(f"File uploaded: {file_key}")
            return url
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            return None
    
    async def download_file(self, file_key: str) -> Optional[bytes]:
        """
        Download file from S3
        
        Returns:
            File bytes if successful, None otherwise
        """
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=file_key)
            return response["Body"].read()
        
        except ClientError as e:
            logger.error(f"S3 download error: {e}")
            return None
    
    async def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3
        
        Returns:
            True if successful
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_key)
            logger.info(f"File deleted: {file_key}")
            return True
        
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    def generate_presigned_url(
        self,
        file_key: str,
        expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for temporary file access
        
        Args:
            file_key: S3 object key
            expiration: URL expiration in seconds (default 1 hour)
        
        Returns:
            Presigned URL if successful
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_key},
                ExpiresIn=expiration
            )
            return url
        
        except ClientError as e:
            logger.error(f"Presigned URL error: {e}")
            return None


# Singleton instance
s3_adapter = S3Adapter()