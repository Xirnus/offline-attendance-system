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
    
    if not settings['enable_fingerprint_blocking']:
        return True, "Fingerprint blocking disabled"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        time_threshold = time.time() - (settings['time_window_minutes'] * 60)
        cursor.execute('''
            SELECT COUNT(*) as usage_count 
            FROM attendances 
            WHERE fingerprint_hash = ? AND timestamp > ?
        ''', (fingerprint_hash, time_threshold))
        
        usage_count = cursor.fetchone()['usage_count']
        conn.close()
        
        if usage_count >= settings['max_uses_per_device']:
            hours = settings['time_window_minutes'] // 60
            return False, f"Device already used {usage_count} times in the last {hours} hours, Please use another device"
        
        return True, "Device allowed"
    except Exception as e:
        return True, "Error checking fingerprint"

def store_device_fingerprint(fingerprint_hash, device_info):
    """Store or update device fingerprint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM device_fingerprints WHERE fingerprint_hash = ?', (fingerprint_hash,))
        existing = cursor.fetchone()
        current_time = datetime.utcnow().isoformat()
        
        if existing:
            cursor.execute('''
                UPDATE device_fingerprints 
                SET last_seen = ?, usage_count = usage_count + 1, device_info = ?
                WHERE fingerprint_hash = ?
            ''', (current_time, device_info, fingerprint_hash))
        else:
            cursor.execute('''
                INSERT INTO device_fingerprints 
                (fingerprint_hash, first_seen, last_seen, usage_count, device_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (fingerprint_hash, current_time, current_time, 1, device_info))
        
        conn.commit()
        conn.close()
    except Exception as e:
        pass  # Silently handle errors to avoid breaking the main flow