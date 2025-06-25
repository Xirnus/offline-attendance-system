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

import os
import sqlite3
from flask import Blueprint, request, render_template, send_file, jsonify
import json
from datetime import datetime

import openpyxl
from database.operations import (
    get_student_by_id, update_student_attendance, 
    get_active_session, mark_students_absent, create_attendance_session, 
    stop_active_session, get_students_with_attendance_data,
    get_settings, update_settings, create_token, get_token, 
    update_token, record_attendance, record_denied_attempt, get_all_data
)
from services.reports import reports_service
from services.fingerprint import generate_comprehensive_fingerprint, create_fingerprint_hash
from services.attendance import is_fingerprint_allowed, store_device_fingerprint
from services.token import generate_token, validate_token_access
from services.rate_limiting import is_rate_limited, get_client_ip
from utils.qr_generator import generate_qr_code, build_qr_url
from database.class_table_manager import create_class_table, insert_students as insert_class_students

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
            required_columns = ['Student_ID', 'Name', 'Course', 'Year_Level']
            df = df[required_columns] 
            df.columns = ['student_id', 'name', 'course', 'year'] 
            # Extract numeric year from strings like "3rd Year", "1st Year", etc.
            def extract_year(year_str):
                import re
                if pd.isna(year_str):
                    return 1  # Default to 1st year
                
                year_str = str(year_str).strip()
                
                # Extract number from strings like "3rd Year", "1st Year", "2nd Year"
                match = re.search(r'(\d+)', year_str)
                if match:
                    year_num = int(match.group(1))
                    # Validate year range (1-5 for typical college years)
                    return year_num if 1 <= year_num <= 5 else 1
                
                # If no number found, try to parse as direct integer
                try:
                    return int(float(year_str))
                except (ValueError, TypeError):
                    return 1  # Default fallback
            
            df['year'] = df['year'].apply(extract_year)
            rows = df.values.tolist()
        elif filename.endswith('.csv'):
            import csv
            from io import StringIO
            content = file.read().decode('utf-8')
            reader = csv.reader(StringIO(content))
            rows = list(reader)
            if len(rows) > 1:
                # Process CSV rows to extract year numbers
                header = rows[0]
                data_rows = rows[1:]
                
                # Find year column index
                year_col_idx = None
                for i, col in enumerate(header):
                    if 'year' in col.lower():
                        year_col_idx = i
                        break
                
                if year_col_idx is not None:
                    for row in data_rows:
                        if len(row) > year_col_idx:
                            # Extract numeric year from year string
                            import re
                            year_str = str(row[year_col_idx]).strip()
                            match = re.search(r'(\d+)', year_str)
                            if match:
                                row[year_col_idx] = int(match.group(1))
                            else:
                                row[year_col_idx] = 1  # Default
                
                rows = data_rows
            else:
                rows = []
        
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
        profile_id = data.get('profile_id')
        class_table = data.get('class_table')
        reset_status = data.get('reset_status', True)  # Default to True

        if not all([session_name, start_time, end_time]):
            return jsonify(status='error', message='Missing required fields')

        # Reset student status before creating new session if requested
        if reset_status:
            from database.operations import get_db_connection
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE students SET status = NULL')
            conn.commit()
            conn.close()
            print("Reset all student status to null before creating session")

        result = create_attendance_session(session_name, start_time, end_time, profile_id, class_table)
        if result:
            message = 'Attendance session created'
            if profile_id:
                message += ' using session profile'
            if reset_status:
                message += '. Student status reset.'
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

# Export and reporting endpoints
@api_bp.route('/api/export/pdf')
def export_pdf():
    """Generate and download PDF report"""
    try:
        report_type = request.args.get('type', 'comprehensive')
        date_range = None
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        pdf_path = reports_service.generate_pdf_report(report_type, date_range)
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/export/excel')
def export_excel():
    """Generate and download Excel report"""
    try:
        excel_path = reports_service.export_to_excel()
        return send_file(excel_path, as_attachment=True, download_name=os.path.basename(excel_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/export/csv')
def export_csv():
    """Generate and download CSV export"""
    try:
        data_type = request.args.get('type', 'all')
        csv_path = reports_service.export_to_csv(data_type)
        
        if data_type == 'all':
            # Return info about generated files
            return jsonify({
                'message': 'CSV files generated successfully',
                'files': [
                    f"{csv_path}_students.csv",
                    f"{csv_path}_attendance.csv", 
                    f"{csv_path}_sessions.csv"
                ]
            })
        else:
            return send_file(csv_path, as_attachment=True, download_name=os.path.basename(csv_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/reports/analytics')
def get_analytics():
    """Get comprehensive attendance analytics"""
    try:
        analytics = reports_service.get_attendance_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/reports/email', methods=['POST'])
def send_email_report():
    """Send email report to specified recipient"""
    try:
        data = request.json or {}
        recipient_email = data.get('recipient_email')
        report_type = data.get('report_type', 'pdf')
        smtp_config = data.get('smtp_config')
        
        if not recipient_email:
            return jsonify({'error': 'Recipient email is required'}), 400
        
        success = reports_service.send_email_report(recipient_email, report_type, smtp_config)
        
        if success:
            return jsonify({'message': 'Email report sent successfully'})
        else:
            return jsonify({'error': 'Failed to send email report'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/reports/schedule', methods=['POST'])
def schedule_reports():
    """Schedule automated email reports"""
    try:
        schedule_config = request.json or {}
        
        required_fields = ['recipient_email', 'frequency', 'time']
        if not all(field in schedule_config for field in required_fields):
            return jsonify({'error': 'Missing required scheduling fields'}), 400
        
        reports_service.schedule_reports(schedule_config)
        return jsonify({'message': 'Report scheduling configured successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/api/reports/preview')
def preview_report():
    """Preview report data without generating file"""
    try:
        report_type = request.args.get('type', 'summary')
        
        if report_type == 'analytics':
            data = reports_service.get_attendance_analytics()
        else:
            # Return basic preview data
            from database.operations import get_students_with_attendance_data, get_all_data
            students_data = get_students_with_attendance_data()
            attendance_data = get_all_data('attendances')
            
            data = {
                'summary': {
                    'total_students': len(students_data),
                    'total_checkins': len(attendance_data),
                    'generated_at': datetime.utcnow().isoformat()
                },
                'recent_attendance': attendance_data[-10:] if attendance_data else [],
                'student_count_by_course': {}
            }
            
            # Group students by course
            for student in students_data:
                course = student.get('course', 'Unknown')
                if course not in data['student_count_by_course']:
                    data['student_count_by_course'][course] = 0
                data['student_count_by_course'][course] += 1
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Session profiles endpoints
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

# Student management endpoints  
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
        };
        
        return jsonify(student_data);
        
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
        
        conn.commit();
        
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

@api_bp.route('/upload_class_record', methods=['POST'])
def upload_class_record():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({'error': 'Only Excel files (.xlsx, .xls) are allowed'}), 400

        # Read the Excel file
        wb = openpyxl.load_workbook(file)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        
        if len(rows) < 5:  # At least metadata + headers + 1 student
            return jsonify({'error': 'Invalid file format - not enough rows'}), 400

        # Extract metadata (first few rows)
        metadata = {}
        current_header = None
        
        for row in rows[:5]:  # Check first 5 rows for metadata
            if not any(row):  # Skip empty rows
                continue
                
            # Check if this is a metadata header row
            if row[0] and any(x in str(row[0]).lower() for x in ['professor', 'room', 'venue']):
                # This is likely a header row for metadata
                current_header = {
                    'professor': 0,
                    'room_type': 1 if len(row) > 1 and 'room type' in str(row[1]).lower() else None,
                    'venue': 2 if len(row) > 2 and 'venue' in str(row[2]).lower() else None
                }
                continue
                
            # If we have headers, extract values
            if current_header:
                if 'professor' in current_header and row[current_header['professor']]:
                    metadata['professor'] = str(row[current_header['professor']]).strip()
                if 'room_type' in current_header and current_header['room_type'] is not None and len(row) > current_header['room_type'] and row[current_header['room_type']]:
                    metadata['room_type'] = str(row[current_header['room_type']]).strip()
                if 'venue' in current_header and current_header['venue'] is not None and len(row) > current_header['venue'] and row[current_header['venue']]:
                    metadata['venue'] = str(row[current_header['venue']]).strip()
                break

        # Set defaults if not found
        professor_name = metadata.get('professor', 'Unknown Professor')
        room_type = metadata.get('room_type', 'Unknown Room Type')
        venue = metadata.get('venue', 'Unknown Venue')

        # Find the row with student headers
        student_data_start = None
        for i, row in enumerate(rows):
            if row and row[0] and 'student id' in str(row[0]).lower():
                student_data_start = i
                break
                
        if student_data_start is None:
            return jsonify({'error': 'Could not find student data headers'}), 400

        # Process headers
        headers = [str(h).strip().lower().replace(' ', '_') for h in rows[student_data_start]]
        required_columns = {'student_id', 'student_name', 'year_level', 'course'}
        
        # Validate headers
        missing_columns = required_columns - set(headers)
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}. Found columns: {", ".join(headers)}'
            }), 400

        # Process student data (rows after headers)
        student_data = []
        new_students_for_attendance = []  # For attendance.db (only new students)
        existing_student_ids = set()  # To track existing student IDs in attendance.db

        # First get all existing student IDs from attendance.db
        try:
            attendance_conn = sqlite3.connect('attendance.db')
            attendance_cursor = attendance_conn.cursor()
            attendance_cursor.execute("SELECT student_id FROM students")
            existing_student_ids = {row[0] for row in attendance_cursor.fetchall()}
        except Exception as e:
            print(f"Warning: Could not check existing students in attendance.db: {str(e)}")
            existing_student_ids = set()
        
        for row in rows[student_data_start+1:]:
            # Skip empty rows or rows with empty student_id
            if not row or not row[0] or not str(row[0]).strip():
                continue
                
            student = dict(zip(headers, row))
            student_id = str(student.get('student_id', '')).strip()
            
            student_data.append({
                'studentId': student_id,
                'studentName': str(student.get('student_name', '')).strip(),
                'yearLevel': str(student.get('year_level', '')).strip(),
                'course': str(student.get('course', '')).strip()
            })
            
            # Only add to attendance.db if student_id doesn't exist
            if student_id not in existing_student_ids:
                new_students_for_attendance.append((
                    student_id,
                    str(student.get('student_name', '')).strip(),
                    str(student.get('year_level', '')).strip(),
                    str(student.get('course', '')).strip()
                ))
                existing_student_ids.add(student_id)  # Add to set to prevent duplicates in this batch

        if not student_data:
            return jsonify({'error': 'No valid student data found in the file'}), 400

        # Create display name from filename (without extension) and professor name
        file_name = file.filename
        if file_name.lower().endswith('.xlsx'):
            file_name = file_name[:-5]
        elif file_name.lower().endswith('.xls'):
            file_name = file_name[:-4]
            
        # Ensure there's exactly one " - " between filename and professor name
        file_name = file_name.rstrip(' -')  # Remove any existing dashes or spaces at the end
        professor_name = professor_name.lstrip(' -')  # Remove any existing dashes or spaces at the start
        display_name = f"{file_name} - {professor_name}"

        # Create table name (sanitized version for database)
        # Ensure there's exactly one "_" between filename and professor name in table name
        sanitized_file_name = file_name.replace(' ', '_').rstrip('_')
        sanitized_professor = professor_name.replace(' ', '_').lstrip('_')
        table_name = f"{sanitized_file_name}___{sanitized_professor}"
        table_name = ''.join(c for c in table_name if c.isalnum() or c == '_')

        # Database operations for classes.db
        columns = [
            ('student_id', 'TEXT'),
            ('student_name', 'TEXT'),
            ('year_level', 'TEXT'),
            ('course', 'TEXT')
        ]
        
        create_class_table(table_name, columns, db_path='classes.db')
        insert_class_students(table_name, student_data, db_path='classes.db')
        
        # Database operations for attendance.db (only for new students)
        if new_students_for_attendance:
            try:
                attendance_conn = sqlite3.connect('attendance.db')
                attendance_cursor = attendance_conn.cursor()
                
                # Insert only new students into attendance.db
                attendance_cursor.executemany(
                    "INSERT INTO students (student_id, name, year, course) VALUES (?, ?, ?, ?)",
                    new_students_for_attendance
                )
                
                attendance_conn.commit()
                attendance_conn.close()
                print(f"Added {len(new_students_for_attendance)} new students to attendance.db")
            except Exception as e:
                print(f"Warning: Could not insert into attendance.db: {str(e)}")
                # Continue even if attendance.db insertion fails

        return jsonify({
            'message': f'Successfully imported {len(student_data)} students',
            'new_students_added_to_attendance': len(new_students_for_attendance),
            'display_name': display_name,
            'professor': professor_name,
            'room_type': room_type,
            'venue': venue,
            'student_data': student_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500
@api_bp.route('/api/class_tables', methods=['GET'])
def get_class_tables():
    try:
        db_path = 'classes.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all user tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cursor.fetchall()]
        
        result = []
        for table in tables:
            # Get all students from each table
            cursor.execute(f'SELECT * FROM "{table}"')  # Note the quotes around table name
            columns = [desc[0] for desc in cursor.description]
            students = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            # Reconstruct display name from table name
            display_name = table.replace('_', ' ').replace('-', ' - ')
            
            result.append({
                'table_name': table,
                'display_name': display_name,
                'students': students,
                'can_delete': True  # Flag to indicate deletable tables
            })
            
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to retrieve class tables: {str(e)}'
        }), 500
    

@api_bp.route('/api/delete_class_table', methods=['POST'])
def delete_class_table():
    try:
        data = request.json or {}
        table_name = data.get('table_name')
        
        if not table_name:
            return jsonify({'error': 'Table name is required'}), 400
            
        db_path = 'classes.db'
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Table not found'}), 404
            
        # Delete the table
        cursor.execute(f'DROP TABLE "{table_name}"')
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Table {table_name} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to delete table: {str(e)}'
        }), 500

@api_bp.route('/api/classes')
def get_classes():
    import sqlite3
    db_path = 'classes.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Get all user tables (each table is a class)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    # Reconstruct display names (match your upload logic)
    class_list = []
    for table in tables:
        parts = table.split('___')
        if len(parts) == 2:
            file_part = parts[0].replace('_', ' ')
            prof_part = parts[1].replace('_', ' ')
            display_name = f"{file_part} - {prof_part}"
        else:
            display_name = table
        class_list.append({'table_name': table, 'display_name': display_name})
    return jsonify({'classes': class_list})

@api_bp.route('/api/add_student', methods=['POST'])
def add_single_student():
    try:
        data = request.json
        student_id = data.get('student_id', '').strip()
        name = data.get('name', '').strip()
        course = data.get('course', '').strip()
        year = data.get('year', 1)
        
        if not all([student_id, name, course]):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Use the correct insert_students function
        from database.operations import insert_students
        count = insert_students([[student_id, name, course, year]])
        
        if count == 1:
            return jsonify({'message': 'Student added successfully'})
        else:
            return jsonify({'error': 'Failed to add student'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500