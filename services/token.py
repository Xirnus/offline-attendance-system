import random
import string
import time
from config import Config

def generate_token():
    """Generate random token"""
    return ''.join(random.choices(
        string.ascii_letters + string.digits, 
        k=Config.TOKEN_LENGTH
    ))

def is_token_expired(token_timestamp):
    """Check if token is expired"""
    return time.time() - token_timestamp > Config.TOKEN_EXPIRY

def validate_token_access(token_data, device_signature):
    """Validate token access based on device signature"""
    if not token_data:
        return False, "Invalid token"
    
    if token_data['used']:
        return False, "Token already used"
    
    if is_token_expired(token_data['timestamp']):
        return False, "Token expired"
    
    # Check device signature consistency
    if token_data['opened'] and token_data['device_signature'] != device_signature:
        return False, "Token can only be used on the same device type"
    
    return True, "Token valid"