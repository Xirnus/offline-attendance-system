from .connection import get_db_connection
from config import DEFAULT_SETTINGS
import time
from datetime import datetime

def row_to_dict(row):
    """Convert sqlite3.Row to dict, return None if row is None"""
    return dict(row) if row else None

def get_settings():
    """Get app settings from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            row_dict = dict(row)  
            return {
                'max_uses_per_device': row_dict['max_uses_per_device'],
                'time_window_minutes': row_dict['time_window_minutes'],
                'enable_fingerprint_blocking': bool(row_dict['enable_fingerprint_blocking'])
            }
        else:
            return DEFAULT_SETTINGS
    except Exception:
        return DEFAULT_SETTINGS

def update_settings(data):
    """Update app settings"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE settings 
        SET max_uses_per_device = ?, time_window_minutes = ?, enable_fingerprint_blocking = ?
        WHERE id = ?
    ''', (data['max_uses_per_device'], data['time_window_minutes'], 
          data['enable_fingerprint_blocking'], 'config'))
    conn.commit()
    conn.close()

def create_token(token):
    """Store new token in database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO active_tokens (token, timestamp, used, opened, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (token, time.time(), False, False, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_token(token):
    """Get token data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM active_tokens WHERE token = ?', (token,))
    result = cursor.fetchone()
    conn.close()
    return row_to_dict(result) 

def update_token(token, **kwargs):
    """Update token with new data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clauses = []
    values = []
    for key, value in kwargs.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)
    
    query = f"UPDATE active_tokens SET {', '.join(set_clauses)} WHERE token = ?"
    values.append(token)
    
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    
def record_attendance(data):
    """Record attendance with enhanced device signature"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO attendances 
            (token, fingerprint_hash, timestamp, created_at, name, course, year, device_info, device_signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('token'),
            data.get('fingerprint_hash'),
            time.time(),
            current_time,
            data.get('name'),
            data.get('course'),
            data.get('year'),
            data.get('device_info'),
            data.get('device_signature') 
        ))
        
        conn.commit()
        conn.close()
        print(f"Attendance recorded for {data.get('name')} with device: {data.get('device_signature')}")
    except Exception as e:
        print(f"Error recording attendance: {e}")

def record_denied_attempt(data, reason):
    """Record denied attempt with enhanced device signature"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO denied_attempts 
            (token, fingerprint_hash, timestamp, created_at, reason, name, course, year, device_info, device_signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('token'),
            data.get('fingerprint_hash'),
            time.time(),
            current_time,
            reason,
            data.get('name', 'Unknown'),
            data.get('course', 'Unknown'),
            data.get('year', 'Unknown'),
            data.get('device_info'),
            data.get('device_signature')
        ))
        
        conn.commit()
        conn.close()
        print(f"Denied attempt recorded for {data.get('name')} with device: {data.get('device_signature')}")
    except Exception as e:
        print(f"Error recording denied attempt: {e}")

def get_all_data(table_name, limit=100):
    """Get all data from specified table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    timestamp_columns = {
        'device_fingerprints': 'last_seen',
        'attendances': 'timestamp',
        'denied_attempts': 'timestamp',
        'active_tokens': 'created_at',
        'settings': 'id'
    }
    
    order_column = timestamp_columns.get(table_name, 'id') 
    cursor.execute(f'SELECT * FROM {table_name} ORDER BY {order_column} DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]