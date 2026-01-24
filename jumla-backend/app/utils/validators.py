# ========================================
# app/utils/validators.py
# ========================================
"""
Utility validators for data validation
"""
import re
from typing import Optional
from decimal import Decimal, InvalidOperation


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Accepts:
    - +1234567890 (with country code)
    - 1234567890 (10 digits)
    - (123) 456-7890 (formatted)
    """
    # Remove non-numeric characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Check length (10-15 digits)
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False
    
    return True


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format
    
    Returns: +1234567890
    """
    # Remove non-numeric characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Add country code if missing
    if not phone.startswith('+'):
        # Assume US/Canada if 10 digits
        if len(cleaned) == 10:
            cleaned = '1' + cleaned
        cleaned = '+' + cleaned
    
    return cleaned


def validate_email(email: str) -> bool:
    """
    Validate email address format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_currency(amount: str) -> Optional[Decimal]:
    """
    Validate and convert currency string to Decimal
    
    Accepts:
    - "123.45"
    - "$123.45"
    - "123,456.78"
    
    Returns:
        Decimal if valid, None otherwise
    """
    # Remove currency symbols and commas
    cleaned = re.sub(r'[$,]', '', amount)
    
    try:
        value = Decimal(cleaned)
        if value < 0:
            return None
        return value
    except InvalidOperation:
        return None


def validate_zip_code(zip_code: str) -> bool:
    """
    Validate US ZIP code format
    
    Accepts:
    - 12345 (5 digits)
    - 12345-6789 (ZIP+4)
    """
    pattern = r'^\d{5}(-\d{4})?$'
    return re.match(pattern, zip_code) is not None


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input string
    
    - Strips whitespace
    - Removes control characters
    - Limits length
    """
    # Remove control characters
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    # Strip and limit length
    sanitized = sanitized.strip()[:max_length]
    
    return sanitized


def validate_property_address(address: str) -> bool:
    """
    Basic validation for property address
    
    Checks for minimum components:
    - Street number
    - Street name
    - City or ZIP
    """
    # Very basic check - should have at least a number and some text
    has_number = bool(re.search(r'\d+', address))
    has_text = len(re.findall(r'[a-zA-Z]+', address)) >= 2
    
    return has_number and has_text


def validate_offer_amount(
    amount: Decimal,
    min_amount: Decimal,
    max_amount: Decimal
) -> tuple[bool, Optional[str]]:
    """
    Validate offer amount is within acceptable range
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if amount < min_amount:
        return False, f"Offer amount must be at least ${min_amount:,.2f}"
    
    if amount > max_amount:
        return False, f"Offer amount cannot exceed ${max_amount:,.2f}"
    
    # Check for reasonable increments (multiples of $1000)
    if amount % 1000 != 0:
        return False, "Offer amount should be in $1000 increments"
    
    return True, None


def validate_lead_score(score: Decimal) -> bool:
    """
    Validate lead score is within valid range (0-100)
    """
    return 0 <= score <= 100


def extract_address_components(address: str) -> dict:
    """
    Extract components from address string
    
    Returns:
        Dictionary with street, city, state, zip
    """
    components = {
        "street": None,
        "city": None,
        "state": None,
        "zip": None
    }
    
    # Extract ZIP code
    zip_match = re.search(r'\b\d{5}(-\d{4})?\b', address)
    if zip_match:
        components["zip"] = zip_match.group()
        address = address.replace(zip_match.group(), '')
    
    # Extract state (2-letter code)
    state_match = re.search(r'\b([A-Z]{2})\b', address)
    if state_match:
        components["state"] = state_match.group()
        address = address.replace(state_match.group(), '')
    
    # Remaining parts
    parts = [p.strip() for p in address.split(',') if p.strip()]
    
    if len(parts) >= 1:
        components["street"] = parts[0]
    if len(parts) >= 2:
        components["city"] = parts[1]
    
    return components