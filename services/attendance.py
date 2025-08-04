"""
Attendance Service Module for Offline Attendance System

This module provides core attendance business logic and device fingerprint management for the SQLite-based attendance tracking system. It handles device usage validation, fingerprint storage, and attendance policy enforcement.

Main Features:
- Device Fingerprint Validation: Check if devices are allowed to check in
- Per-Session Usage Limit Enforcement: Prevent multiple check-ins from same device within a session
- Device Tracking: Store and update device fingerprint information
- Security Policy: Configurable blocking and validation rules

Key Functions:
- is_fingerprint_allowed(): Validates device fingerprints against per-session usage policies
- store_device_fingerprint(): Records and updates device usage information

Business Logic:
- Configurable device usage limits per session (not time-based)
- Automatic device fingerprint tracking and counting
- Per-session usage restrictions (prevents multiple check-ins in same session)
- Graceful error handling to prevent system disruption

Security Features:
- Device fingerprint-based duplicate prevention per session
- Configurable blocking policies via system settings
- Per-session usage counting and enforcement
- Historical device usage tracking

Used by: API routes, check-in validation, attendance recording
Dependencies: Database operations, system settings, device fingerprinting
"""

import time
import json
from database.operations import get_settings, get_db_connection, row_to_dict
from database.performance_manager import get_optimized_db, db_operation
from utils.logging_system import get_logger, monitor_performance
from datetime import datetime

logger = get_logger()

@monitor_performance("fingerprint_validation")
def is_fingerprint_allowed(fingerprint_hash, session_id=None):
    """Check if device fingerprint is allowed for a specific session (if session_id is provided)"""
    try:
        settings = get_settings()
        
        logger.log_security_event(
            'fingerprint_check',
            f"Validating fingerprint for session {session_id}",
            severity='info',
            fingerprint_hash=fingerprint_hash[:8] + "...",
            session_id=session_id,
            settings=settings
        )
        
        if not settings['enable_fingerprint_blocking']:
            logger.log_event('info', "Fingerprint blocking disabled - allowing all devices",
                           component='attendance', action='fingerprint_check',
                           session_id=session_id, allowed=True, reason='blocking_disabled')
            return True, "Fingerprint blocking disabled"
        
        # If no session_id provided, allow the device (no session-specific restriction)
        if session_id is None:
            logger.log_event('info', "No session_id provided - allowing device",
                           component='attendance', action='fingerprint_check',
                           allowed=True, reason='no_session')
            return True, "No session restriction"
        
        with db_operation("check_fingerprint_usage") as db:
            # Check if device has already been used in this specific session
            usage_count = db.execute_query('''
                SELECT COUNT(*) as usage_count 
                FROM class_attendees ca
                JOIN device_fingerprints df ON ca.device_fingerprint_id = df.id
                WHERE df.fingerprint_hash = ? AND ca.session_id = ?
            ''', (fingerprint_hash, session_id), fetch='one')['usage_count']
            
            if usage_count > 0:
                logger.log_security_event(
                    'device_reuse_blocked',
                    f"Device already used {usage_count} time(s) in session {session_id}",
                    severity='warning',
                    fingerprint_hash=fingerprint_hash[:8] + "...",
                    session_id=session_id,
                    usage_count=usage_count
                )
                return False, f"Device already used in this session. Please use a different device."
            
            logger.log_event('info', "Device allowed for session",
                           component='attendance', action='fingerprint_check',
                           session_id=session_id, allowed=True, reason='not_used')
            return True, f"Device allowed for this session"
            
    except Exception as e:
        logger.log_error(e, "is_fingerprint_allowed")
        # Allow on error to prevent blocking legitimate users
        return True, f"Error checking fingerprint: {e}"

@monitor_performance("store_device_fingerprint")
def store_device_fingerprint(fingerprint_hash, device_info):
    """Store or update device fingerprint and return the record"""
    try:
        logger.log_event('debug', "Storing device fingerprint",
                        component='attendance', action='store_fingerprint',
                        fingerprint_hash=fingerprint_hash[:8] + "...")
        
        with db_operation("store_device_fingerprint") as db:
            existing = db.execute_query(
                'SELECT * FROM device_fingerprints WHERE fingerprint_hash = ?',
                (fingerprint_hash,), fetch='one'
            )
            
            current_time = datetime.utcnow().isoformat()
            
            # Convert device_info to JSON string if it's a dict
            device_info_str = json.dumps(device_info) if isinstance(device_info, dict) else device_info
            
            if existing:
                db.execute_query('''
                    UPDATE device_fingerprints 
                    SET last_seen = ?, usage_count = usage_count + 1, device_info = ?, updated_at = ?
                    WHERE fingerprint_hash = ?
                ''', (current_time, device_info_str, current_time, fingerprint_hash))
                device_id = existing[0]  # Get the ID from existing record
                
                logger.log_event('debug', "Updated existing device fingerprint",
                               component='attendance', action='update_fingerprint',
                               device_id=device_id)
            else:
                db.execute_query('''
                    INSERT INTO device_fingerprints 
                    (fingerprint_hash, first_seen, last_seen, usage_count, device_info, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (fingerprint_hash, current_time, current_time, 1, device_info_str, current_time, current_time))
                
                device_id = db.execute_query("SELECT last_insert_rowid()", fetch='one')[0]
                
                logger.log_event('info', "Created new device fingerprint",
                               component='attendance', action='create_fingerprint',
                               device_id=device_id)
            
            # Get the full record to return
            result = db.execute_query('SELECT * FROM device_fingerprints WHERE id = ?', 
                                    (device_id,), fetch='one')
            
            # Convert to dict format
            return row_to_dict(result)
        
    except Exception as e:
        logger.log_error(e, "store_device_fingerprint")
        # Return a minimal record to prevent errors
        return {'id': None, 'fingerprint_hash': fingerprint_hash}