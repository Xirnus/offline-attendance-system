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
        return "Error generating QR code", 500

@core_bp.route('/scan/<token>')
def scan(token):
    try:
        token_data = get_token(token)
        
        request_data = {
            'user_agent': request.headers.get('User-Agent', ''),
            'language': request.headers.get('Accept-Language', ''),
            'platform': request.headers.get('Sec-Ch-Ua-Platform', '').replace('"', ''),
        }
        
        device_info = generate_comprehensive_fingerprint(request_data)
        device_sig = device_info.get('device_signature', {})
        
        valid, message = validate_token_access(token_data, device_sig)
        if not valid:
            return f"<h3>{message}</h3>", 400
        
        if not token_data['opened']:
            update_token(token, opened=True, device_signature=json.dumps(device_sig))
        
        return render_template('index.html', token=token)
    except Exception as e:
        return "Error processing QR code", 500

@core_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json or {}
        student_id = data.get('student_id', '').strip()
        token = data.get('token', '').strip()
        
        print(f"Check-in attempt - Student ID: {student_id}, Token: {token[:8]}...")
        
        # Basic validation
        if not student_id:
            print("Missing student ID")
            return jsonify(status='error', message='Student ID is required'), 400
        if not token:
            print("Missing token")
            return jsonify(status='error', message='Token is required'), 400
        
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
        
        # Check if already checked in
        if student.get('status') == 'present':
            print(f"Student {student_id} already present")
            return jsonify(status='error', message='Already checked in for this session'), 409
        
        # Generate fingerprint
        print("Generating fingerprint...")
        request_data = {
            'user_agent': data.get('user_agent', ''),
            'screen_resolution': data.get('screen_resolution', ''),
            'timezone': data.get('timezone', ''),
            'language': data.get('language', ''),
            'platform': data.get('platform', ''),
        }
        
        fingerprint_data = generate_comprehensive_fingerprint(request_data)
        fingerprint_hash = create_fingerprint_hash(request_data)
        
        print(f"Fingerprint generated: {fingerprint_hash[:8]}...")
        
        # Enhanced validation checks
        print("Performing enhanced validation checks...")
        
        # Check if this device has already been used to check in for this session
        session_id = active_session.get('id')
        if is_device_already_used_in_session(fingerprint_hash, session_id):
            print(f"Device {fingerprint_hash[:8]}... already used in session {session_id}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'device_already_used_in_session')
            return jsonify(status='error', message='This device has already been used to check in for this session'), 409
        
        # Check if student is enrolled in the session's class (if class is specified)
        class_table = active_session.get('class_table')
        if class_table and not is_student_in_class(student_id, class_table):
            print(f"Student {student_id} not enrolled in class {class_table}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'student_not_in_class')
            return jsonify(status='error', message='You are not enrolled in this class'), 403
        
        # Check if student has already checked in with a different device for this session
        if is_student_already_checked_in_session(student_id, session_id):
            print(f"Student {student_id} already checked in for session {session_id}")
            return jsonify(status='error', message='You have already checked in for this session'), 409
        
        print("Enhanced validation checks passed")
        
        # Check fingerprint limits
        print("Checking fingerprint limits...")
        allowed, reason = is_fingerprint_allowed(fingerprint_hash)
        if not allowed:
            print(f"Fingerprint blocked: {reason}")
            enhanced_data = data.copy()
            enhanced_data.update({
                'session_id': session_id,
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'), 
                'year': str(student.get('year', 'Unknown'))
            })
            record_denied_attempt(enhanced_data, 'fingerprint_blocked')
            return jsonify(status='error', message=reason), 403
        
        print("Fingerprint allowed")
        
        # Update attendance records
        print(f"Updating attendance for {student_id}...")
        update_student_attendance(student_id, 'present')
        print("Student attendance updated")
        
        print("Marking token as used...")
        update_token(token, used=True, fingerprint_hash=fingerprint_hash)
        print("Token marked as used")
        
        # Record attendance
        print("Recording attendance...")
        attendance_data = {
            'token': token,
            'student_id': student_id,
            'fingerprint_hash': fingerprint_hash,
            'name': student['name'],
            'course': student['course'],
            'year': str(student['year']),
            'device_info': json.dumps(fingerprint_data),
            'device_signature': json.dumps(fingerprint_data.get('device_signature', {})),
            'session_id': session_id
        }
        
        record_attendance(attendance_data)
        print("Attendance recorded")
        
        print("Storing device fingerprint...")
        store_device_fingerprint(fingerprint_hash, json.dumps(fingerprint_data))
        print("Device fingerprint stored")
        
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
        cursor.execute('SELECT COUNT(*) FROM attendances')
        attendance_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM denied_attempts')
        denied_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM device_fingerprints')
        device_count = cursor.fetchone()[0]
        
        # Delete all data from the tables
        cursor.execute('DELETE FROM attendances')
        cursor.execute('DELETE FROM denied_attempts') 
        cursor.execute('DELETE FROM device_fingerprints')
        
        # Reset auto-increment counters
        cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("attendances", "denied_attempts", "device_fingerprints")')
        
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
