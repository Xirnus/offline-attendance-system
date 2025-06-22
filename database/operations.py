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

def insert_students(rows):
    """Insert students from CSV/Excel data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    count = 0
    
    for row in rows:
        if len(row) >= 4:  # student_id, name, course, year
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO students (student_id, name, course, year)
                    VALUES (?, ?, ?, ?)
                ''',
                (
                    str(row[0]).strip(),  # student_id
                    str(row[1]).strip(),  # name
                    str(row[2]).strip(),  # course
                    int(row[3])           # year
                ))
                count += 1
            except Exception as e:
                print(f"Error inserting student {row}: {e}")
    
    conn.commit()
    conn.close()
    return count

def get_all_students():
    """Get all students from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY name')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_all_students():
    """Clear all students from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM students')
    count = cursor.fetchone()[0]
    cursor.execute('DELETE FROM students')
    conn.commit()
    conn.close()
    return count

# Add to operations.py

def get_student_by_id(student_id):
    """Get student by student ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

def update_student_attendance(student_id, status='present'):
    """Update student attendance status and last check-in time"""
    conn = get_db_connection()
    cursor = conn.cursor()
    current_time = datetime.utcnow().isoformat()
    
    cursor.execute('''
        UPDATE students 
        SET last_check_in = ?, status = ?
        WHERE student_id = ?
    ''', (current_time, status, student_id))
    
    conn.commit()
    conn.close()

def mark_students_absent():
    """Mark students as absent if they didn't check in during active session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current active session
    cursor.execute('''
        SELECT * FROM attendance_sessions 
        WHERE is_active = 1 AND datetime('now') > datetime(end_time)
    ''')
    expired_sessions = cursor.fetchall()
    
    for session in expired_sessions:
        # Mark students as absent if they haven't checked in
        cursor.execute('''
            UPDATE students 
            SET status = 'absent', absent_count = absent_count + 1
            WHERE (status IS NULL OR status != 'present') 
            AND (last_check_in IS NULL OR last_check_in < ?)
        ''', (session['start_time'],))
        
        # Deactivate the session
        cursor.execute('UPDATE attendance_sessions SET is_active = 0 WHERE id = ?', (session['id'],))
    
    conn.commit()
    conn.close()

def create_attendance_session(session_name, start_time, end_time):
    """Create new attendance session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear previous student statuses
    cursor.execute('UPDATE students SET status = NULL')
    
    # Create new session
    cursor.execute('''
        INSERT INTO attendance_sessions (session_name, start_time, end_time, is_active)
        VALUES (?, ?, ?, 1)
    ''', (session_name, start_time, end_time))
    
    conn.commit()
    conn.close()

def get_active_session():
    """Get current active attendance session"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM attendance_sessions 
        WHERE is_active = 1 AND datetime('now') BETWEEN datetime(start_time) AND datetime(end_time)
    ''')
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None