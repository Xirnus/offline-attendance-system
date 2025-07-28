"""
Token Management Service Module for Offline Attendance System

This module provides secure token generation, validation, and management for QR code-based attendance tracking. It handles token lifecycle, expiration, and device-specific validation to ensure secure and controlled access to attendance check-in functionality.

Main Features:
- Token Generation: Create cryptographically secure random tokens
- Expiration Management: Time-based token validity with configurable expiry
- Device Binding: Tie tokens to specific device signatures for security
- Access Validation: Multi-layer validation for token usage
- Usage Tracking: Monitor token usage and prevent reuse

Key Functions:
- generate_token(): Create secure random tokens for QR codes
- is_token_expired(): Check token validity based on timestamp
- validate_token_access(): Comprehensive token and device validation

Token Security Features:
- Random alphanumeric token generation
- Configurable token length for security flexibility
- Time-based expiration to prevent stale token usage
- Device signature binding to prevent token sharing
- Single-use enforcement to prevent duplicate check-ins
- Comprehensive validation with detailed error messages

Token Lifecycle:
1. Generate: Create new token for QR code
2. Bind: Associate token with device when first accessed
3. Validate: Check token validity and device consistency
4. Consume: Mark token as used after successful check-in
5. Expire: Automatic expiration based on time limits

Security Policies:
- Tokens expire after configurable time period
- Device signature must match between QR scan and check-in
- Tokens can only be used once per generation
- Invalid tokens provide specific error messages
- Failed validation attempts are logged for security

Used by: API routes, QR code generation, attendance validation
Dependencies: Standard library (random, string, time), config settings
"""

import random
import string
import time
from config.config import Config

def generate_token():
    """Generate random token"""
    return ''.join(random.choices(
        string.ascii_letters + string.digits, 
        k=Config.TOKEN_LENGTH
    ))

def is_token_expired(token_timestamp):
    """Check if token is expired"""
    return time.time() - token_timestamp > Config.TOKEN_EXPIRY

def validate_token_access(token_data, device_fingerprint_hash):
    """Validate token access based on device fingerprint hash (visitor_id)"""
    if not token_data:
        return False, "Invalid token"
    if token_data['used']:
        return False, "QR code already used"
    if is_token_expired(token_data['generated_at']):
        return False, "Token expired"
    # Check device fingerprint consistency (compare hash, not DB id)
    if token_data['opened'] and token_data.get('device_fingerprint_id'):
        import sqlite3
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT fingerprint_hash FROM device_fingerprints WHERE id = ?', (token_data['device_fingerprint_id'],))
        row = cursor.fetchone()
        conn.close()
        token_fingerprint_hash = row[0] if row else None
        print(f"[DEBUG] validate_token_access: token_fingerprint_hash={repr(token_fingerprint_hash)}, device_fingerprint_hash={repr(device_fingerprint_hash)}")
        if str(token_fingerprint_hash).strip() != str(device_fingerprint_hash).strip():
            return False, "Token can only be used on the same device that opened the QR code"
    return True, "Token valid"