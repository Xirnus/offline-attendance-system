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
            return False, f"Device used {usage_count} times in last {hours} hours"
        
        return True, "Device allowed"
    except Exception as e:
        print(f"Error checking fingerprint: {e}")
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
        print(f"Error storing fingerprint: {e}")

def validate_attendance_data(data):
    """Validate attendance form data"""
    required = ['token', 'fingerprint_hash', 'name', 'course', 'year']
    return all(data.get(field) for field in required)