import time
import hashlib
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
            return False, f"Device used {usage_count} times in last {hours} hours"
        
        return True, "Device allowed"
    except Exception as e:
        print(f"Error checking fingerprint: {e}")
        return True, "Error checking fingerprint"

def has_device_scanned_qr(qr_code_id, fingerprint_hash):
    """Check if this specific device has already scanned this QR code"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as scan_count 
            FROM qr_scans 
            WHERE qr_code_id = ? AND fingerprint_hash = ?
        ''', (qr_code_id, fingerprint_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['scan_count'] > 0
    except Exception as e:
        print(f"Error checking QR scan history: {e}")
        return False

def is_qr_code_valid(qr_code_id):
    """Check if QR code is valid and active"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM qr_codes 
            WHERE qr_code_id = ? AND is_active = 1
        ''', (qr_code_id,))
        
        qr_code = cursor.fetchone()
        conn.close()
        
        if not qr_code:
            return False, "Invalid or inactive QR code"
        
        # Check if QR code has expired
        if qr_code.get('expires_at'):
            expiry_time = datetime.fromisoformat(qr_code['expires_at'])
            if datetime.utcnow() > expiry_time:
                return False, "QR code has expired"
        
        return True, "Valid QR code"
    except Exception as e:
        print(f"Error validating QR code: {e}")
        return False, "Error validating QR code"

def record_qr_scan(qr_code_id, fingerprint_hash, device_info, scan_result="success"):
    """Record QR code scan attempt"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        current_time = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO qr_scans 
            (qr_code_id, fingerprint_hash, device_info, scan_time, scan_result)
            VALUES (?, ?, ?, ?, ?)
        ''', (qr_code_id, fingerprint_hash, device_info, current_time, scan_result))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error recording QR scan: {e}")

def validate_attendance_request(data):
    """Enhanced validation for attendance requests with QR tracking"""
    # Basic validation
    required = ['token', 'fingerprint_hash', 'name', 'course', 'year', 'qr_code_id']
    if not all(data.get(field) for field in required):
        return False, "Missing required fields"
    
    qr_code_id = data['qr_code_id']
    fingerprint_hash = data['fingerprint_hash']
    
    # Check if QR code is valid
    is_valid, message = is_qr_code_valid(qr_code_id)
    if not is_valid:
        return False, message
    
    # Check if this device has already scanned this QR code
    if has_device_scanned_qr(qr_code_id, fingerprint_hash):
        return False, "This device has already scanned this QR code"
    
    # Check fingerprint limits
    is_allowed, fp_message = is_fingerprint_allowed(fingerprint_hash)
    if not is_allowed:
        return False, fp_message
    
    return True, "Valid attendance request"

def process_attendance_with_qr(data):
    """Process attendance with QR code tracking"""
    # Validate the request
    is_valid, message = validate_attendance_request(data)
    if not is_valid:
        # Record failed scan attempt
        record_qr_scan(
            data.get('qr_code_id'), 
            data.get('fingerprint_hash'), 
            data.get('device_info', '{}'), 
            f"failed: {message}"
        )
        return False, message
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Record attendance
        current_time = datetime.utcnow().isoformat()
        cursor.execute('''
            INSERT INTO attendances 
            (name, course, year, fingerprint_hash, qr_code_id, timestamp, device_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'], 
            data['course'], 
            data['year'], 
            data['fingerprint_hash'],
            data['qr_code_id'],
            current_time,
            data.get('device_info', '{}')
        ))
        
        attendance_id = cursor.lastrowid
        
        # Record successful QR scan
        record_qr_scan(
            data['qr_code_id'], 
            data['fingerprint_hash'], 
            data.get('device_info', '{}'), 
            "success"
        )
        
        # Update device fingerprint usage
        store_device_fingerprint(data['fingerprint_hash'], data.get('device_info', '{}'))
        
        conn.commit()
        conn.close()
        
        return True, f"Attendance recorded successfully (ID: {attendance_id})"
        
    except Exception as e:
        print(f"Error processing attendance: {e}")
        return False, "Error processing attendance"

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
        print(f"Error storing fingerprint: {e}")

def validate_attendance_data(data):
    """Validate attendance form data (backward compatibility)"""
    required = ['token', 'fingerprint_hash', 'name', 'course', 'year']
    return all(data.get(field) for field in required)