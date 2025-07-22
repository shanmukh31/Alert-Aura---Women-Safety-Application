import re
from datetime import datetime

def validate_phone_number(number):
    """Validate Indian phone number format"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, number))

def get_timestamp():
    """Get formatted timestamp"""
    return datetime.now().strftime("%H:%M:%S")

def get_formatted_time():
    """Get formatted time with AM/PM"""
    return datetime.now().strftime("%I:%M:%S %p") 