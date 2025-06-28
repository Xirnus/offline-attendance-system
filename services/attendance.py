"""
Attendance Service Module for Offline Attendance System

This module provides core attendance business logic and device fingerprint management for the SQLite-based attendance tracking system. It handles device usage validation, fingerprint storage, and attendance policy enforcement.

Main Features:
- Device Fingerprint Validation: Check if devices are allowed to check in
- Usage Limit Enforcement: Prevent multiple check-ins from same device
- Time Window Management: Control device usage within specified time periods
- Device Tracking: Store and update device fingerprint information
- Security Policy: Configurable blocking and validation rules

Key Functions:
- is_fingerprint_allowed(): Validates device fingerprints against usage policies
- store_device_fingerprint(): Records and updates device usage information

Business Logic:
- Configurable device usage limits per time window
- Automatic device fingerprint tracking and counting
- Time-based usage restrictions (e.g., max 1 use per 24 hours)
- Graceful error handling to prevent system disruption

Security Features:
- Device fingerprint-based duplicate prevention
- Configurable blocking policies via system settings
- Usage counting and time window enforcement
- Historical device usage tracking

Used by: API routes, check-in validation, attendance recording
Dependencies: Database operations, system settings, device fingerprinting
"""

import time
from database.operations import get_settings, get_db_connection
from datetime import datetime

def is_fingerprint_allowed(fingerprint_hash):
    """Check if device fingerprint is allowed"""
    settings = get_settings()
    
    print(f"Checking fingerprint {fingerprint_hash[:8]}... with settings: {settings}")
    
    if not settings['enable_fingerprint_blocking']:
        print("Fingerprint blocking is disabled - allowing all devices")
        return True, "Fingerprint blocking disabled"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        time_threshold = time.time() - (settings['time_window_minutes'] * 60)
        print(f"Checking usage within time window: {settings['time_window_minutes']} minutes (since {time_threshold})")
        
        cursor.execute('''
            SELECT COUNT(*) as usage_count 
            FROM class_attendees ca
            JOIN device_fingerprints df ON ca.device_fingerprint_id = df.id
            WHERE df.fingerprint_hash = ? AND ca.checked_in_at > datetime(?, 'unixepoch')
        ''', (fingerprint_hash, time_threshold))
        
        usage_count = cursor.fetchone()['usage_count']
        max_uses = settings['max_uses_per_device']
        
        print(f"Device usage: {usage_count}/{max_uses} in the last {settings['time_window_minutes']//60} hours")
        
        conn.close()
        
        if usage_count >= max_uses:
            hours = settings['time_window_minutes'] // 60
            message = f"Device already used {usage_count} times in the last {hours} hours. Maximum allowed: {max_uses}. Please use another device"
            print(f"BLOCKING: {message}")
            return False, message
        
        print(f"ALLOWING: Device usage within limits ({usage_count}/{max_uses})")
        return True, f"Device allowed ({usage_count}/{max_uses} uses)"
        
    except Exception as e:
        print(f"Error checking fingerprint: {e}")
        return True, f"Error checking fingerprint: {e}"

def store_device_fingerprint(fingerprint_hash, device_info):
    """Store or update device fingerprint and return the record"""
    import json
    try:
        print(f"[DEBUG] store_device_fingerprint: fingerprint_hash={repr(fingerprint_hash)}")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM device_fingerprints WHERE fingerprint_hash = ?', (fingerprint_hash,))
        existing = cursor.fetchone()
        current_time = datetime.utcnow().isoformat()
        
        # Convert device_info to JSON string if it's a dict
        device_info_str = json.dumps(device_info) if isinstance(device_info, dict) else device_info
        
        if existing:
            cursor.execute('''
                UPDATE device_fingerprints 
                SET last_seen = ?, usage_count = usage_count + 1, device_info = ?, updated_at = ?
                WHERE fingerprint_hash = ?
            ''', (current_time, device_info_str, current_time, fingerprint_hash))
            device_id = existing[0]  # Get the ID from existing record
        else:
            cursor.execute('''
                INSERT INTO device_fingerprints 
                (fingerprint_hash, first_seen, last_seen, usage_count, device_info, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (fingerprint_hash, current_time, current_time, 1, device_info_str, current_time, current_time))
            device_id = cursor.lastrowid
        
        conn.commit()
        
        # Get the full record to return
        cursor.execute('SELECT * FROM device_fingerprints WHERE id = ?', (device_id,))
        result = cursor.fetchone()
        conn.close()
        
        print(f"[DEBUG] store_device_fingerprint: device_id={device_id}")
        
        # Convert to dict format
        from database.operations import row_to_dict
        return row_to_dict(result)
        
    except Exception as e:
        print(f"Error storing device fingerprint: {e}")
        # Return a minimal record to prevent errors
        return {'id': None, 'fingerprint_hash': fingerprint_hash}