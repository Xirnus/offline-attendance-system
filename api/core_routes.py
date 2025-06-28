"""
Core Routes Module for Offline Attendance System

This module contains the core functionality routes:
- QR Code Generation: Creates secure tokens and QR codes for attendance sessions
- Student Check-in: Processes attendance submissions with device fingerprinting
- Token Validation: Handles QR code scanning and validation

Security Features:
- Device fingerprinting to prevent multiple check-ins
- Token-based authentication with expiration
- Rate limiting to prevent abuse
"""

import json
from flask import Blueprint, request, render_template, send_file, jsonify
from database.operations import (
    get_student_by_id, update_student_attendance, 
    get_active_session, create_token, get_token, 
    update_token, record_attendance, record_denied_attempt,
    is_device_already_used_in_session, is_student_in_class,
    is_student_already_checked_in_session
)
from services.fingerprint import generate_comprehensive_fingerprint, create_fingerprint_hash
from services.attendance import is_fingerprint_allowed, store_device_fingerprint
from services.token import generate_token, validate_token_access
from services.rate_limiting import is_rate_limited, get_client_ip
from utils.qr_generator import generate_qr_code, build_qr_url

core_bp = Blueprint('core', __name__)

# Also, modify the generate_qr function to store the token globally or return it
@core_bp.route('/generate_qr')
def generate_qr():
    if is_rate_limited(get_client_ip(request)):
        return "Rate limit exceeded", 429
    
    token = generate_token()
    
    try:
        create_token(token)
        qr_url = build_qr_url(request, token)
        qr_image = generate_qr_code(qr_url)
        if qr_image:
            return send_file(qr_image, mimetype='image/png')
        else:
            return "QR code generation not available", 500
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return "Error generating QR code", 500

@core_bp.route('/api/current_token', methods=['GET'])
def get_current_token():
    """Get the current QR token"""
    try:
        from database.connection import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the most recent token that hasn't been used
        cursor.execute('''
            SELECT token FROM tokens 
            WHERE used = 0 
            ORDER BY generated_at DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'status': 'success',
                'token': result[0]
            })
        else:
            return jsonify({
                'status': 'success',
                'token': None,
                'message': 'No active token found'
            })
            
    except Exception as e:
        print(f"Error getting current token: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@core_bp.route('/scan/<token>')
def scan(token):
    try:
        print(f"Scanning token: {token[:10]}...")
        token_data = get_token(token)
        print(f"Token data retrieved: {token_data}")
        
        if not token_data:
            print("Token not found or invalid")
            return "<h3>Invalid or expired QR code</h3>", 400
        
        request_data = {
            'user_agent': request.headers.get('User-Agent', ''),
            'language': request.headers.get('Accept-Language', ''),
            'platform': request.headers.get('Sec-Ch-Ua-Platform', '').replace('"', ''),
        }
        
        device_info = generate_comprehensive_fingerprint(request_data)
        device_sig = device_info.get('device_signature', {})
        fingerprint_hash = create_fingerprint_hash(device_info)
        
        # Get or create device fingerprint record
        device_fingerprint = store_device_fingerprint(fingerprint_hash, device_info)
        device_fingerprint_id = device_fingerprint['id']
        
        valid, message = validate_token_access(token_data, device_fingerprint_id)
        if not valid:
            print(f"Token access validation failed: {message}")
            return f"<h3>{message}</h3>", 400
        
        if not token_data.get('opened', False):
            print("Marking token as opened and linking to device fingerprint")
            update_token(token, opened=True, device_fingerprint_id=device_fingerprint_id)
        
        print("Rendering index.html template")
        return render_template('index.html', token=token)
    except Exception as e:
        print(f"Error processing QR code: {str(e)}")
        import traceback
        traceback.print_exc()
        return f"<h3>Error processing QR code: {str(e)}</h3>", 500

@core_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json or {}
        student_id = data.get('student_id', '').strip()
        token = data.get('token', '').strip()
        session_id = data.get('session_id', '').strip()  # Accept session_id from frontend
        visitor_id = data.get('visitor_id', '').strip()
        screen_size = data.get('screen_size', '').strip()
        user_agent = data.get('user_agent', '').strip()
        timezone = data.get('timezone', '').strip()

        print(f"Check-in attempt - Student ID: {student_id}, Token: {token[:8]}...")

        # Basic validation
        if not student_id:
            print("Missing student ID")
            return jsonify(status='error', message='Student ID is required'), 400
        if not token:
            print("Missing token")
            return jsonify(status='error', message='Token is required'), 400
        if not visitor_id:
            print("Missing visitor_id")
            return jsonify(status='error', message='Device identifier is required'), 400

        # Check if student exists
        print(f"Looking up student: {student_id}")
        student = get_student_by_id(student_id)
        if not student:
            print(f"Student not found: {student_id}")
            return jsonify(status='error', message='Student ID not found in database'), 404

        print(f"Found student: {student['name']}")

        # Check token validity
        print(f"Validating token: {token[:8]}...")
        token_data = get_token(token)
        if not token_data:
            print("Invalid token")
            return jsonify(status='error', message='Invalid or expired token'), 401
        if token_data.get('used'):
            print("Token already used")
            return jsonify(status='error', message='Token already used'), 409

        print("Token is valid")

        # Check for active session
        print("Checking for active session...")
        active_session = get_active_session()
        if not active_session:
            print("No active session")
            return jsonify(status='error', message='No active attendance session'), 400

        print(f"Active session found: {active_session.get('session_name', 'Unnamed')}")
        # Get session ID from active session if not provided
        if not session_id:
            session_id = active_session.get('id')
        profile_id = active_session.get('profile_id')
        class_table = active_session.get('class_table')

        # Enrollment checks (unchanged)
        if class_table and str(class_table).strip().lower() not in ('', 'none', 'null'):
            print(f"Class-based session detected (class_table={class_table}), skipping session profile enrollment check.")
        else:
            if profile_id:
                print(f"Checking enrollment for student {student_id} in profile {profile_id}")
                from database.operations import check_student_enrollment
                if not check_student_enrollment(profile_id, student_id):
                    print(f"Student {student_id} not enrolled in session profile {profile_id}")
                    enhanced_data = data.copy()
                    enhanced_data.update({
                        'session_id': session_id,
                        'profile_id': profile_id,
                        'name': student.get('name', 'Unknown'),
                        'course': student.get('course', 'Unknown'), 
                        'year': str(student.get('year', 'Unknown'))
                    })
                    record_denied_attempt(enhanced_data, 'student_not_enrolled_in_profile')
                    return jsonify(status='error', message='You are not enrolled in this session. Please contact your instructor to be added.'), 403
                print(f"Student {student_id} is enrolled in profile {profile_id}")

        # Check if already checked in
        if is_student_already_checked_in_session(student_id, session_id):
            print(f"Student {student_id} already checked in for session {session_id}")
            return jsonify(status='error', message='You have already checked in for this session'), 409

        # Device uniqueness: use visitor_id as the canonical device identifier
        device_id = visitor_id
        print(f"Device ID (visitor_id): {device_id}")

        # Check if this device has already been used to check in for this session
        if is_device_already_used_in_session(device_id, session_id):
            print(f"Device {device_id} already used in session {session_id}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'device_already_used_in_session')
            return jsonify(status='error', message='This device has already been used to check in for this session'), 409

        # Enrollment checks for class (unchanged)
        course = active_session.get('course')
        class_table = active_session.get('class_table')
        if class_table:
            print(f"Checking enrollment for student {student_id} in class_table {class_table}")
            from database.operations import is_student_enrolled_in_class_id, is_student_in_class
            try:
                class_id = int(class_table)
                if not is_student_enrolled_in_class_id(student_id, class_id):
                    print(f"Student {student_id} not enrolled in class {class_id}")
                    enhanced_data = data.copy()
                    enhanced_data.update({
                        'session_id': session_id,
                        'name': student.get('name', 'Unknown'),
                        'course': student.get('course', 'Unknown'), 
                        'year': str(student.get('year', 'Unknown'))
                    })
                    record_denied_attempt(enhanced_data, 'student_not_enrolled_in_class')
                    return jsonify(status='error', message='You are not enrolled in this class. Please contact your instructor to be added to the class.'), 403
            except ValueError:
                if not is_student_in_class(student_id, class_table):
                    print(f"Student {student_id} not enrolled in course {class_table}")
                    enhanced_data = data.copy()
                    enhanced_data.update({
                        'session_id': session_id,
                        'name': student.get('name', 'Unknown'),
                        'course': student.get('course', 'Unknown'), 
                        'year': str(student.get('year', 'Unknown'))
                    })
                    record_denied_attempt(enhanced_data, 'student_not_in_class')
                    return jsonify(status='error', message='You are not enrolled in this class'), 403
        elif course and not is_student_in_class(student_id, course):
            print(f"Student {student_id} not enrolled in class {course}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'student_not_enrolled_in_class')
            return jsonify(status='error', message='You are not enrolled in this class'), 403

        # Check device limits (if any, using visitor_id)
        print("Checking device limits...")
        allowed, reason = is_fingerprint_allowed(device_id)
        if not allowed:
            print(f"Device blocked: {reason}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'device_blocked')
            return jsonify(status='error', message=reason), 403

        print("Device allowed")

        # Store device info (minimal) and record attendance in the same transaction
        print("Storing device info and recording attendance in a single transaction...")
        import sqlite3
        from config import Config  # <-- FIX: import Config here
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        try:
            # Store or update device fingerprint
            import json
            current_time = __import__('datetime').datetime.utcnow().isoformat()
            # Use only the minimal device info sent by frontend
            minimal_device_info = {
                'visitor_id': visitor_id,
                'screen_size': screen_size,
                'user_agent': user_agent,
                'timezone': timezone
            }
            device_info_str = json.dumps(minimal_device_info)
            cursor.execute('SELECT id FROM device_fingerprints WHERE fingerprint_hash = ?', (device_id,))
            row = cursor.fetchone()
            if row:
                device_fingerprint_id = row[0]
                cursor.execute('''
                    UPDATE device_fingerprints 
                    SET last_seen = ?, usage_count = usage_count + 1, device_info = ?, updated_at = ?
                    WHERE id = ?
                ''', (current_time, device_info_str, current_time, device_fingerprint_id))
            else:
                cursor.execute('''
                    INSERT INTO device_fingerprints 
                    (fingerprint_hash, first_seen, last_seen, usage_count, device_info, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (device_id, current_time, current_time, 1, device_info_str, current_time, current_time))
                device_fingerprint_id = cursor.lastrowid
            print(f"[DEBUG] (TX) device_fingerprint_id={device_fingerprint_id}")
            # Mark token as used
            from database.operations import update_token
            update_token(token, used=True, device_fingerprint_id=device_fingerprint_id, conn=conn)
            print("Token marked as used")
            # Record attendance
            print("Recording attendance...")
            attendance_data = {
                'session_id': session_id,
                'student_id': student_id,
                'device_fingerprint_id': device_fingerprint_id,
                'token': token,
                'name': student['name'],
                'course': student['course'],
                'year': str(student['year']),
                'device_info': device_info_str,
            }
            from database.operations import record_attendance
            record_attendance(attendance_data, conn=conn)  # pass conn to avoid DB lock
            print("Attendance recorded")
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Check-in error (transaction): {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify(status='error', message='Server error occurred'), 500
        print(f"Check-in successful for {student['name']}")
        return jsonify(
            status='success', 
            message=f'Welcome {student["name"]}! Attendance recorded successfully'
        )
    except Exception as e:
        print(f"Check-in error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify(status='error', message='Server error occurred'), 500

@core_bp.route('/api/delete_all_data', methods=['POST'])
def delete_all_data():
    """Delete all attendance, denied attempts, and device fingerprint data"""
    try:
        from database.connection import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get counts before deletion for confirmation
        cursor.execute('SELECT COUNT(*) FROM class_attendees')
        attendance_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM denied_attempts')
        denied_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM device_fingerprints')
        device_count = cursor.fetchone()[0]
        
        # Delete all data from the tables
        cursor.execute('DELETE FROM class_attendees')
        cursor.execute('DELETE FROM denied_attempts') 
        cursor.execute('DELETE FROM device_fingerprints')
        
        # Reset auto-increment counters
        cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("class_attendees", "denied_attempts", "device_fingerprints")')
        
        conn.commit()
        conn.close()
        
        print(f"Deleted data - Attendances: {attendance_count}, Denied Attempts: {denied_count}, Devices: {device_count}")
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully deleted all data: {attendance_count} attendances, {denied_count} denied attempts, {device_count} devices',
            'deleted_counts': {
                'attendances': attendance_count,
                'denied_attempts': denied_count,
                'device_fingerprints': device_count
            }
        })
        
    except Exception as e:
        print(f"Error deleting data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Failed to delete data: {str(e)}'
        }), 500
