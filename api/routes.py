"""
API Routes Module for Offline Attendance System

This module contains all API endpoints for the Flask-based attendance tracking system. It handles QR code generation, student check-ins, session management, and data retrieval.

Main Features:
- QR Code Generation: Creates secure tokens and QR codes for attendance sessions
- Student Check-in: Processes attendance submissions with device fingerprinting
- Session Management: Create, stop, and monitor attendance sessions
- Data Management: Student upload, export, and CRUD operations
- Security: Rate limiting, device fingerprinting, and token validation
- Analytics: Attendance reports, student statistics, and session data

Key Endpoints:
- /generate_qr - Generate QR codes for attendance sessions
- /scan/<token> - Validate and process QR code scans
- /checkin - Handle student attendance submissions
- /api/students_* - Student management and data retrieval
- /api/session_* - Attendance session control
- /api/settings - System configuration management

Security Features:
- Device fingerprinting to prevent multiple check-ins
- Token-based authentication with expiration
- Rate limiting to prevent abuse
- Session validation and access control
"""

from flask import Blueprint, request, render_template, send_file, jsonify
import json
from datetime import datetime
from database.operations import (
    get_student_by_id, update_student_attendance, 
    get_active_session, mark_students_absent, create_attendance_session, 
    stop_active_session, get_students_with_attendance_data,
    get_settings, update_settings, create_token, get_token, 
    update_token, record_attendance, record_denied_attempt, get_all_data
)
from services.fingerprint import generate_comprehensive_fingerprint, create_fingerprint_hash
from services.attendance import is_fingerprint_allowed, store_device_fingerprint
from services.token import generate_token, validate_token_access
from services.rate_limiting import is_rate_limited, get_client_ip
from utils.qr_generator import generate_qr_code, build_qr_url

api_bp = Blueprint('api', __name__)

@api_bp.route('/generate_qr')
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

@api_bp.route('/scan/<token>')
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

@api_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json or {}
        student_id = data.get('student_id', '').strip()
        token = data.get('token', '').strip()
        
        # Basic validation
        if not student_id:
            return jsonify(status='error', message='Student ID is required'), 400
        if not token:
            return jsonify(status='error', message='Token is required'), 400
        
        # Check if student exists
        student = get_student_by_id(student_id)
        if not student:
            return jsonify(status='error', message='Student ID not found in database'), 404
        
        # Check token validity
        token_data = get_token(token)
        if not token_data:
            return jsonify(status='error', message='Invalid or expired token'), 401
        if token_data.get('used'):
            return jsonify(status='error', message='Token already used'), 409
        
        # Check for active session
        active_session = get_active_session()
        if not active_session:
            return jsonify(status='error', message='No active attendance session'), 400
        
        # Check if already checked in
        if student.get('status') == 'present':
            return jsonify(status='error', message='Already checked in for this session'), 409
        
        # Generate fingerprint
        request_data = {
            'user_agent': data.get('user_agent', ''),
            'screen_resolution': data.get('screen_resolution', ''),
            'timezone': data.get('timezone', ''),
            'language': data.get('language', ''),
            'platform': data.get('platform', ''),
        }
        
        fingerprint_data = generate_comprehensive_fingerprint(request_data)
        fingerprint_hash = create_fingerprint_hash(request_data)
        
        # Check fingerprint limits
        allowed, reason = is_fingerprint_allowed(fingerprint_hash)
        if not allowed:
            record_denied_attempt(data, 'fingerprint_blocked')
            return jsonify(status='error', message=reason), 403
        
        # Update attendance records
        update_student_attendance(student_id, 'present')
        update_token(token, used=True, fingerprint_hash=fingerprint_hash)
        
        # Record attendance
        attendance_data = {
            'token': token,
            'student_id': student_id,
            'fingerprint_hash': fingerprint_hash,
            'name': student['name'],
            'course': student['course'],
            'year': str(student['year']),
            'device_info': json.dumps(fingerprint_data),
            'device_signature': json.dumps(fingerprint_data.get('device_signature', {}))
        }
        
        record_attendance(attendance_data)
        store_device_fingerprint(fingerprint_hash, json.dumps(fingerprint_data))
        
        return jsonify(
            status='success', 
            message=f'Welcome {student["name"]}! Attendance recorded successfully'
        )
    
    except Exception as e:
        return jsonify(status='error', message='Server error occurred'), 500

@api_bp.route('/api/attendances')
def api_attendances():
    try:
        attendances = get_all_data('attendances')
        for attendance in attendances:
            if 'fingerprint_hash' in attendance and attendance['fingerprint_hash']:
                attendance['fingerprint_hash'] = attendance['fingerprint_hash'][:8] + '...'
        return jsonify(attendances)
    except Exception as e:
        return jsonify([])

@api_bp.route('/api/denied')
def api_denied():
    try:
        denied = get_all_data('denied_attempts')
        for attempt in denied:
            if 'fingerprint_hash' in attempt and attempt['fingerprint_hash']:
                attempt['fingerprint_hash'] = attempt['fingerprint_hash'][:8] + '...'
        return jsonify(denied)
    except Exception as e:
        return jsonify([])

@api_bp.route('/api/device_fingerprints', methods=['GET'])
def api_device_fingerprints():
    try:
        fingerprints = get_all_data('device_fingerprints')
        for fp in fingerprints:
            if 'fingerprint_hash' in fp and fp['fingerprint_hash']:
                fp['fingerprint_hash'] = fp['fingerprint_hash'][:8] + '...'
        return jsonify(fingerprints)
    except Exception as e:
        return jsonify([])

@api_bp.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    try:
        if request.method == 'GET':
            return jsonify(get_settings())
        
        data = request.json or {}
        update_settings(data)
        return jsonify(get_settings())
    except Exception as e:
        return jsonify(get_settings())

@api_bp.route('/api/export_data')
def export_data():
    try:
        export_data = {
            'attendances': get_all_data('attendances'),
            'denied_attempts': get_all_data('denied_attempts'),
            'settings': get_settings(),
            'device_fingerprints': get_all_data('device_fingerprints'),
            'export_timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)})

@api_bp.route('/upload_students', methods=['POST'])
def upload_students():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'})
        
        filename = file.filename.lower()
        
        if filename.endswith(('.xlsx', '.xls')):
            import pandas as pd
            df = pd.read_excel(file)
            required_columns = ['Student ID', 'Name', 'Course', 'Year']
            df = df[required_columns] 
            df.columns = ['student_id', 'name', 'course', 'year'] 
            df['year'] = df['year'].astype(int)
            rows = df.values.tolist()
        elif filename.endswith('.csv'):
            import csv
            from io import StringIO
            content = file.read().decode('utf-8')
            reader = csv.reader(StringIO(content))
            rows = list(reader)
            rows = rows[1:] if len(rows) > 1 else []
        else:
            return jsonify({'error': 'Only CSV and Excel files are supported'})
        
        from database.operations import insert_students
        count = insert_students(rows)
        return jsonify({'message': f'Successfully imported {count} students'})
        
    except Exception as e:
        return jsonify({'error': str(e)})

@api_bp.route('/get_students')
def get_students():
    try:
        from database.operations import get_all_students
        students = get_all_students()
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'students': [], 'error': str(e)})

@api_bp.route('/api/students_status')
def students_status():
    try:
        from database.operations import get_all_students
        students = get_all_students()
        return jsonify(students)
    except Exception as e:
        return jsonify([])
    
@api_bp.route('/clear_students', methods=['POST'])
def clear_students():
    try:
        from database.operations import clear_all_students
        count = clear_all_students()
        return jsonify({'deleted': count})
    except Exception as e:
        return jsonify({'error': str(e)})
    
@api_bp.route('/api/mark_absent', methods=['POST'])
def mark_absent():
    try:
        mark_students_absent()
        return jsonify(status='success', message='Absent students marked')
    except Exception as e:
        return jsonify(status='error', message=str(e))

@api_bp.route('/api/create_session', methods=['POST'])
def create_session():
    try:
        data = request.json or {}
        session_name = data.get('session_name')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not all([session_name, start_time, end_time]):
            return jsonify(status='error', message='Missing required fields')
        
        result = create_attendance_session(session_name, start_time, end_time)
        if result:
            return jsonify(status='success', message='Attendance session created')
        else:
            return jsonify(status='error', message='Failed to create session')
    except Exception as e:
        return jsonify(status='error', message=str(e))

@api_bp.route('/api/stop_session', methods=['POST'])
def stop_session():
    try:
        result = stop_active_session()
        if result.get('success'):
            absent_marked = result.get('absent_marked', 0)
            message = f'Session stopped successfully. {absent_marked} students marked absent.' if absent_marked > 0 else 'Session stopped successfully'
            return jsonify(status='success', message=message, absent_marked=absent_marked)
        else:
            return jsonify(status='error', message=result.get('message', 'No active session to stop'))
    except Exception as e:
        return jsonify(status='error', message=str(e))

@api_bp.route('/api/session_status')
def session_status():
    try:
        active_session = get_active_session()
        return jsonify({'active_session': active_session})
    except Exception as e:
        return jsonify({'active_session': None, 'error': str(e)})

@api_bp.route('/api/students_with_attendance')
def get_students_with_attendance():
    """Get all students with their attendance data"""
    try:
        students = get_students_with_attendance_data()
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500