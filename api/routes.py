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
        
        # Check fingerprint limits
        print("Checking fingerprint limits...")
        allowed, reason = is_fingerprint_allowed(fingerprint_hash)
        if not allowed:
            print(f"Fingerprint blocked: {reason}")
            record_denied_attempt(data, 'fingerprint_blocked')
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
            'device_signature': json.dumps(fingerprint_data.get('device_signature', {}))
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
        profile_id = data.get('profile_id')  # New field for profile-based sessions
        
        if not all([session_name, start_time, end_time]):
            return jsonify(status='error', message='Missing required fields')
        
        # If profile_id is provided, you can store it with the session for reference
        result = create_attendance_session(session_name, start_time, end_time, profile_id)
        if result:
            message = 'Attendance session created'
            if profile_id:
                message += ' using session profile'
            return jsonify(status='success', message=message)
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


@api_bp.route('/api/session_profiles', methods=['GET'])
def get_session_profiles():
    """Get all session profiles"""
    try:
        from database.operations import get_all_data
        profiles = get_all_data('session_profiles')
        return jsonify({'profiles': profiles})
    except Exception as e:
        return jsonify({'profiles': [], 'error': str(e)})

@api_bp.route('/api/session_profiles', methods=['POST'])
def create_session_profile():
    """Create a new session profile"""
    try:
        data = request.json or {}
        profile_name = data.get('profile_name')
        room_type = data.get('room_type')
        building = data.get('building', '')
        capacity = data.get('capacity', 0)
        organizer = data.get('organizer', '')  # <-- Add this line

        if not all([profile_name, room_type]):
            return jsonify({'error': 'Profile name and room type are required'}), 400

        # Insert directly into database since we might not have the helper function yet
        from database.operations import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO session_profiles (profile_name, room_type, building, capacity, organizer, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (profile_name, room_type, building, capacity, organizer))  # <-- Add organizer here

        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Session profile created successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/session_profiles/<int:profile_id>', methods=['DELETE'])
def delete_session_profile(profile_id):
    """Delete a session profile"""
    try:
        from database.operations import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM session_profiles WHERE id = ?', (profile_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        conn.close()
        
        if affected_rows > 0:
            return jsonify({'status': 'success', 'message': 'Profile deleted successfully'})
        else:
            return jsonify({'error': 'Profile not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/session_profiles/<int:profile_id>', methods=['PUT'])
def update_session_profile(profile_id):
    """Update a session profile"""
    try:
        data = request.json or {}
        from database.operations import update_session_profile
        result = update_session_profile(profile_id, data)
        
        if result:
            return jsonify({'status': 'success', 'message': 'Profile updated successfully'})
        else:
            return jsonify({'error': 'Profile not found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/use_session_profile/<int:profile_id>', methods=['POST'])
def use_session_profile(profile_id):
    """Use a session profile to create an attendance session"""
    try:
        data = request.json or {}
        session_name = data.get('session_name')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        from database.operations import get_session_profile_by_id
        profile = get_session_profile_by_id(profile_id)
        
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Use profile name if no session name provided
        if not session_name:
            session_name = f"{profile['profile_name']} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        result = create_attendance_session(session_name, start_time, end_time)
        
        if result:
            return jsonify({'status': 'success', 'message': f'Session created using {profile["profile_name"]} profile'})
        else:
            return jsonify({'error': 'Failed to create session'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/students/<student_id>', methods=['GET'])
def get_student(student_id):
    """Get a single student with detailed information"""
    try:
        from database.operations import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get student basic info
        cursor.execute('''
            SELECT student_id, name, course, year, last_check_in, status, absent_count, present_count, created_at
            FROM students 
            WHERE student_id = ?
        ''', (student_id,))
        
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({'error': 'Student not found'}), 404
        
        # Get attendance statistics from student_attendance_history
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                MAX(recorded_at) as last_recorded
            FROM students
            WHERE student_id = ?
        ''', (student_id,))
        
        stats = cursor.fetchone()
        
        # Also check attendances table for additional present records
        cursor.execute('SELECT COUNT(*) FROM attendances WHERE student_id = ?', (student_id,))
        attendance_result = cursor.fetchone()
        attendance_count = attendance_result[0] if attendance_result else 0
        
        conn.close()
        
        # Handle None values safely
        present_from_history = stats[0] if stats and stats[0] else 0
        absent_from_history = stats[1] if stats and stats[1] else 0
        last_recorded = stats[2] if stats and stats[2] else None
        
        student_data = {
            'student_id': student[0],
            'name': student[1],
            'course': student[2],
            'year': str(student[3]),  # Convert to string for consistency
            'last_check_in': student[4],
            'status': student[5],
            'absent_count': student[6] if student[6] else 0,
            'present_count': student[7] if student[7] else 0,
            'created_at': student[8],
            'history_present_count': present_from_history,
            'history_absent_count': absent_from_history,
            'attendance_records_count': attendance_count,
            'last_recorded': last_recorded
        }
        
        return jsonify(student_data)
        
    except Exception as e:
        print(f"Error getting student {student_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student information including attendance statistics"""
    try:
        from database.operations import get_db_connection
        
        data = request.json or {}
        print(f"Received update data for {student_id}: {data}")  # Debug log
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'course', 'year']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate year (should be integer between 1-5)
        try:
            year_int = int(data['year'])
            if year_int not in [1, 2, 3, 4, 5]:
                return jsonify({'error': 'Invalid year. Must be 1-5'}), 400
        except ValueError:
            return jsonify({'error': 'Year must be a number'}), 400
        
        # Validate attendance counts if provided
        present_count = None
        absent_count = None
        
        if 'present_count' in data:
            try:
                present_count = int(data['present_count'])
                if present_count < 0:
                    return jsonify({'error': 'Present count cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Present count must be a number'}), 400
        
        if 'absent_count' in data:
            try:
                absent_count = int(data['absent_count'])
                if absent_count < 0:
                    return jsonify({'error': 'Absent count cannot be negative'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'Absent count must be a number'}), 400
        
        # Validate status
        status = data.get('status', None)
        if status == '':
            status = None
        if status and status not in ['present', 'absent']:
            return jsonify({'error': 'Invalid status. Must be present, absent, or null'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute('SELECT student_id, name FROM students WHERE student_id = ?', (student_id,))
        existing_student = cursor.fetchone()
        
        if not existing_student:
            conn.close()
            return jsonify({'error': 'Student not found'}), 404
        
        print(f"Found existing student: {existing_student[1]}")  # Debug log
        
        # Build update query dynamically based on provided fields
        update_fields = []
        params = []
        
        # Always update basic info
        update_fields.extend(['name = ?', 'course = ?', 'year = ?'])
        params.extend([data['name'].strip(), data['course'].strip(), year_int])
        
        # Update attendance counts if provided
        if present_count is not None:
            update_fields.append('present_count = ?')
            params.append(present_count)
            print(f"Updating present_count to: {present_count}")  # Debug log
        
        if absent_count is not None:
            update_fields.append('absent_count = ?')
            params.append(absent_count)
            print(f"Updating absent_count to: {absent_count}")  # Debug log
        
        # Update status
        if 'status' in data:
            update_fields.append('status = ?')
            params.append(status)
            print(f"Updating status to: {status}")  # Debug log
        
        # Add student_id for WHERE clause
        params.append(student_id)
        
        # Execute update
        update_query = f'''
            UPDATE students 
            SET {', '.join(update_fields)}
            WHERE student_id = ?
        '''
        
        print(f"Executing query: {update_query}")  # Debug log
        print(f"With params: {params}")  # Debug log
        
        cursor.execute(update_query, params)
        rows_affected = cursor.rowcount
        
        print(f"Rows affected: {rows_affected}")  # Debug log
        
        conn.commit()
        
        # Verify the update by fetching the student again
        cursor.execute('''
            SELECT student_id, name, course, year, present_count, absent_count, status
            FROM students WHERE student_id = ?
        ''', (student_id,))
        
        updated_student = cursor.fetchone()
        print(f"Updated student data: {updated_student}")  # Debug log
        
        conn.close()
        
        if rows_affected == 0:
            return jsonify({'error': 'No changes were made'}), 400
        
        print(f"Successfully updated student {student_id}: {data['name']}")
        return jsonify({
            'message': 'Student updated successfully',
            'updated_data': {
                'student_id': updated_student[0],
                'name': updated_student[1],
                'course': updated_student[2],
                'year': updated_student[3],
                'present_count': updated_student[4],
                'absent_count': updated_student[5],
                'status': updated_student[6]
            }
        })
        
    except Exception as e:
        print(f"Error updating student {student_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student and all related records"""
    try:
        from database.operations import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute('SELECT name FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({'error': 'Student not found'}), 404
        
        student_name = student[0]
        
        # Delete related records first (foreign key constraints)
        
        # Delete from student
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        history_deleted = cursor.rowcount
        
        # Delete from attendances table
        cursor.execute('DELETE FROM attendances WHERE student_id = ?', (student_id,))
        attendance_deleted = cursor.rowcount
        
        # Delete student
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        
        conn.commit()
        conn.close()
        
        total_records_deleted = history_deleted + attendance_deleted
        
        print(f"Deleted student {student_id} ({student_name}) and {total_records_deleted} related records")
        return jsonify({
            'message': f'Student {student_name} deleted successfully',
            'attendance_records_deleted': attendance_deleted,
            'history_records_deleted': history_deleted,
            'total_records_deleted': total_records_deleted
        })
        
    except Exception as e:
        print(f"Error deleting student {student_id}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/students/<student_id>/attendance', methods=['PUT'])
def update_student_attendance_manual(student_id):
    """Manual override for student attendance counts"""
    try:
        from database.operations import get_db_connection
        
        data = request.json or {}
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate attendance data
        if 'absent_count' not in data and 'present_count' not in data:
            return jsonify({'error': 'Either absent_count or present_count is required'}), 400
        
        update_fields = []
        params = []
        
        if 'absent_count' in data:
            try:
                absent_count = int(data['absent_count'])
                if absent_count < 0:
                    return jsonify({'error': 'absent_count cannot be negative'}), 400
                update_fields.append('absent_count = ?')
                params.append(absent_count)
            except ValueError:
                return jsonify({'error': 'absent_count must be a number'}), 400
        
        if 'present_count' in data:
            try:
                present_count = int(data['present_count'])
                if present_count < 0:
                    return jsonify({'error': 'present_count cannot be negative'}), 400
                update_fields.append('present_count = ?')
                params.append(present_count)
            except ValueError:
                return jsonify({'error': 'present_count must be a number'}), 400
        
        if 'status' in data and data['status'] in ['present', 'absent', None]:
            update_fields.append('status = ?')
            params.append(data['status'])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if student exists
        cursor.execute('SELECT name FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            conn.close()
            return jsonify({'error': 'Student not found'}), 404
        
        # Update attendance
        params.append(student_id)
        update_query = f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = ?"
        
        cursor.execute(update_query, params)
        conn.commit()
        conn.close()
        
        print(f"Updated attendance for student {student_id}")
        return jsonify({'message': 'Student attendance updated successfully'})
        
    except Exception as e:
        print(f"Error updating attendance for student {student_id}: {e}")
        return jsonify({'error': str(e)}), 500

