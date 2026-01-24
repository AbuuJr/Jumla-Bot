# ========================================
# app/services/twilio_adapter.py
# ========================================
"""
Twilio SMS adapter
"""
from typing import Optional
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings

logger = logging.getLogger(__name__)


class TwilioAdapter:
    """Twilio SMS adapter"""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.from_number = settings.TWILIO_PHONE_NUMBER
    
    async def send_sms(
        self,
        to_number: str,
        message: str
    ) -> Optional[str]:
        """
        Send SMS via Twilio
        
        Returns:
            Message SID if successful, None otherwise
        """
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            logger.info(f"SMS sent to {to_number}: {message_obj.sid}")
            return message_obj.sid
        
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            return None
    
    def verify_signature(
        self,
        signature: str,
        url: str,
        params: dict
    ) -> bool:
        """
        Verify Twilio webhook signature
        
        Returns:
            True if signature is valid
        """
        from twilio.request_validator import RequestValidator
        
        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(url, params, signature)


# Singleton instance
twilio_adapter = TwilioAdapter()




