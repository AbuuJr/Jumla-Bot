# ========================================
# app/services/sendgrid_adapter.py
# ========================================
"""
SendGrid email adapter
"""
from typing import Optional, List
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from app.config import settings

logger = logging.getLogger(__name__)


class SendGridAdapter:
    """SendGrid email adapter"""
    
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = Email(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME)
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Optional[str]:
        """
        Send email via SendGrid
        
        Returns:
            Message ID if successful, None otherwise
        """
        try:
            message = Mail(
                from_email=self.from_email,
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", body)
            )
            
            if html_body:
                message.add_content(Content("text/html", html_body))
            
            response = self.client.send(message)
            
            logger.info(f"Email sent to {to_email}: {response.status_code}")
            return response.headers.get("X-Message-Id")
        
        except Exception as e:
            logger.error(f"SendGrid error: {e}")
            return None
    
    async def send_bulk_email(
        self,
        recipients: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> dict:
        """
        Send bulk email via SendGrid
        
        Returns:
            Dictionary with success/failure counts
        """
        results = {"success": 0, "failed": 0}
        
        for recipient in recipients:
            message_id = await self.send_email(recipient, subject, body, html_body)
            if message_id:
                results["success"] += 1
            else:
                results["failed"] += 1
        
        return results


# Singleton instance
sendgrid_adapter = SendGridAdapter()
