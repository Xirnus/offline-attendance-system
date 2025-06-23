"""
Database Operations Module for Offline Attendance System

This module provides all database CRUD operations and business logic for the SQLite-based attendance tracking system. It serves as the data access layer between the API routes and the database, handling complex queries, transactions, and data integrity.

Main Features:
- Student Management: Create, read, update, delete student records
- Attendance Tracking: Record attendance, manage sessions, track statistics
- Token Management: Handle QR code tokens and validation
- Session Control: Create, start, stop attendance sessions
- Data Analytics: Generate attendance reports and statistics
- Device Tracking: Monitor and limit device usage per student
- Settings Management: System configuration and security settings

Key Function Categories:
- Student Operations: get_student_by_id, insert_students, update_student_attendance
- Session Management: create_attendance_session, stop_active_session, get_active_session
- Attendance Recording: record_attendance, mark_students_absent, get_students_with_attendance_data
- Token Operations: create_token, get_token, update_token
- Data Retrieval: get_all_data, get_all_students, get_settings
- Security Functions: record_denied_attempt, device fingerprinting

Database Transactions:
- Automatic retry mechanisms for database locks
- Transaction rollback on errors
- Connection pooling and proper resource cleanup
- Concurrent access handling with SQLite WAL mode

Business Logic:
- Automatic absent marking when sessions end
- Present/absent count tracking per student
- Historical attendance record maintenance
- Device usage limits and fingerprint validation

Used by: API routes, web interface controllers, background tasks
Dependencies: Database connection module, config settings, retry decorators
"""

from .connection import get_db_connection, get_db_connection_with_retry, retry_db_operation
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

@retry_db_operation()
def record_attendance(data):
    """Record attendance with enhanced device signature"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
        cursor = conn.cursor()
        current_time = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT INTO attendances 
            (token, fingerprint_hash, timestamp, created_at, name, course, year, device_info, device_signature, student_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('token'),
            data.get('fingerprint_hash'),
            time.time(),
            current_time,
            data.get('name'),
            data.get('course'),
            data.get('year'),
            data.get('device_info'),
            data.get('device_signature'),
            data.get('student_id')
        ))
        
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@retry_db_operation()
def record_denied_attempt(data, reason):
    """Record denied attempt with enhanced device signature"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
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
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

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
                ''', (
                    str(row[0]).strip(),  # student_id
                    str(row[1]).strip(),  # name
                    str(row[2]).strip(),  # course
                    int(row[3])           # year
                ))
                count += 1
            except Exception:
                continue
    
    conn.commit()
    conn.close()
    return count

def mark_students_absent_for_session(session_id, cursor):
    """Mark students as absent for a specific session"""
    # Get students who haven't checked in for this session
    cursor.execute('''
        SELECT s.student_id FROM students s
        WHERE s.student_id NOT IN (
            SELECT DISTINCT sah.student_id 
            FROM student_attendance_history sah
            WHERE sah.session_id = ? AND sah.status = 'present'
        )
    ''', (session_id,))
    
    students_to_mark = cursor.fetchall()
    
    if not students_to_mark:
        return 0
    
    # Mark students as absent
    for (student_id,) in students_to_mark:
        # Update student status
        cursor.execute('''
            UPDATE students 
            SET status = 'absent', absent_count = COALESCE(absent_count, 0) + 1
            WHERE student_id = ?
        ''', (student_id,))
        
        # Record in attendance history
        cursor.execute('''
            INSERT INTO student_attendance_history 
            (student_id, status, session_id, recorded_at)
            VALUES (?, 'absent', ?, datetime('now'))
        ''', (student_id, session_id))
    
    return len(students_to_mark)

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

def get_student_by_id(student_id):
    """Get student by student ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

@retry_db_operation()
def update_student_attendance(student_id, status):
    """Update student attendance status and record history"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
        cursor = conn.cursor()
        
        # Update student status
        cursor.execute('''
            UPDATE students 
            SET status = ?, last_check_in = datetime('now')
            WHERE student_id = ?
        ''', (status, student_id))
        
        # Get current active session
        cursor.execute('SELECT id FROM attendance_sessions WHERE is_active = 1 LIMIT 1')
        session = cursor.fetchone()
        session_id = session[0] if session else None
        
        # Record in attendance history
        cursor.execute('''
            INSERT INTO student_attendance_history 
            (student_id, status, session_id, recorded_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (student_id, status, session_id))
        
        conn.commit()
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@retry_db_operation()
def mark_students_absent():
    """Mark students as absent if they didn't check in during active session"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
        cursor = conn.cursor()
        
        # Get active session
        cursor.execute('SELECT id FROM attendance_sessions WHERE is_active = 1')
        session = cursor.fetchone()
        
        if not session:
            return 0
        
        session_id = session[0]
        
        # Get students who haven't checked in for this session
        cursor.execute('''
            SELECT student_id FROM students 
            WHERE student_id NOT IN (
                SELECT DISTINCT student_id 
                FROM student_attendance_history 
                WHERE session_id = ? AND status = 'present'
            )
            AND (status IS NULL OR status != 'present')
        ''', (session_id,))
        
        students_to_mark = cursor.fetchall()
        
        if not students_to_mark:
            return 0
        
        # Mark students as absent
        for (student_id,) in students_to_mark:
            cursor.execute('''
                UPDATE students 
                SET status = 'absent' 
                WHERE student_id = ?
            ''', (student_id,))
            
            # Record in attendance history
            cursor.execute('''
                INSERT INTO student_attendance_history 
                (student_id, status, session_id, recorded_at)
                VALUES (?, 'absent', ?, datetime('now'))
            ''', (student_id, session_id))
        
        absent_count = len(students_to_mark)
        conn.commit()
        
        return absent_count
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def get_active_session():
    """Get the currently active attendance session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM attendance_sessions 
            WHERE is_active = 1 
            AND datetime('now') BETWEEN datetime(start_time) AND datetime(end_time)
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        return row_to_dict(result)
    except Exception:
        return None

def create_attendance_session(session_name, start_time, end_time, profile_id=None):
    """Create attendance session, optionally from a profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # You might want to add profile_id to your sessions table
        cursor.execute('''
            INSERT INTO attendance_sessions (session_name, start_time, end_time, is_active, profile_id, created_at)
            VALUES (?, ?, ?, 1, ?, datetime('now'))
        ''', (session_name, start_time, end_time, profile_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating session: {e}")
        return False

@retry_db_operation()
def stop_active_session():
    """Stop the currently active attendance session and mark absent students"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
        cursor = conn.cursor()
        
        # Check if there's an active session
        cursor.execute('SELECT id FROM attendance_sessions WHERE is_active = 1')
        session = cursor.fetchone()
        
        if session:
            session_id = session[0]
            
            # Mark all students who didn't check in as absent
            absent_count = mark_students_absent_for_session(session_id, cursor)
            
            # Stop the active session
            cursor.execute('''
                UPDATE attendance_sessions 
                SET is_active = 0, end_time = datetime('now') 
                WHERE is_active = 1
            ''')
            conn.commit()
            
            return {'success': True, 'absent_marked': absent_count}
        else:
            return {'success': False, 'message': 'No active session to stop'}
            
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

@retry_db_operation()
def get_students_with_attendance_data():
    """Get all students with their attendance statistics"""
    conn = None
    try:
        conn = get_db_connection_with_retry()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                s.student_id,
                s.name,
                s.course,
                s.year,
                s.status,
                s.last_check_in,
                COALESCE(stats.present_count, 0) as present_count,
                COALESCE(stats.absent_count, 0) as absent_count
            FROM students s
            LEFT JOIN (
                SELECT 
                    student_id,
                    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_count,
                    SUM(CASE WHEN status = 'absent' THEN 1 ELSE 0 END) as absent_count
                FROM student_attendance_history 
                GROUP BY student_id
            ) stats ON s.student_id = stats.student_id
            ORDER BY s.name
        ''')
        
        results = cursor.fetchall()
        
        students = []
        for row in results:
            student_dict = row_to_dict(row)
            # Ensure status defaults to None/N/A if not set
            if not student_dict.get('status'):
                student_dict['status'] = None
            students.append(student_dict)
        
        return students
        
    except Exception as e:
        return []
    finally:
        if conn:
            conn.close()
            
def create_session_profile(profile_name, room_type, building, capacity):
    """Create a new session profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO session_profiles (profile_name, room_type, building, capacity, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (profile_name, room_type, building, capacity))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_session_profile_by_id(profile_id):
    """Get session profile by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM session_profiles WHERE id = ?', (profile_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None
    except Exception as e:
        return None

def update_session_profile(profile_id, data):
    """Update session profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE session_profiles 
            SET profile_name = ?, room_type = ?, building = ?, capacity = ?
            WHERE id = ?
        ''', (data.get('profile_name'), data.get('room_type'), 
              data.get('building'), data.get('capacity'), profile_id))
        
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return affected_rows > 0
    except Exception as e:
        return False

def delete_session_profile(profile_id):
    """Delete session profile"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM session_profiles WHERE id = ?', (profile_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        return affected_rows > 0
    except Exception as e:
        return False
