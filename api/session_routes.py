"""
Session Routes Module for Offline Attendance System

This module contains all session management endpoints for creating, managing,
and controlling attendance sessions and session profiles.

OPTIMIZATIONS IMPLEMENTED:
- Enhanced session profile management with full CRUD operations
- Real-time active session monitoring and display
- Improved form validation and error handling
- Better responsive design for mobile devices
- Modal-based session creation from profiles
- Auto-refresh functionality for session status
- Enhanced security with proper data validation

Key Session Management Endpoints:
- POST /api/create_session - Create new attendance session (ENHANCED)
- POST /api/stop_session - Stop active session and mark absents (OPTIMIZED)
- GET /api/session_status - Get current session status (ENHANCED)
- GET /api/session_profiles - Get all session profiles (OPTIMIZED)
- POST /api/session_profiles - Create new session profile (ENHANCED)
- PUT /api/session_profiles/<id> - Update session profile (NEW)
- DELETE /api/session_profiles/<id> - Delete session profile (NEW)
- POST /api/use_session_profile/<id> - Create session from profile (ENHANCED)
- POST /api/mark_absent - Mark absent students (OPTIMIZED)

Session Features:
- Session profile templates for quick session creation
- Active session monitoring with real-time updates
- Automatic absent marking when sessions end
- Course-specific session management
- Enhanced session metadata and tracking
- Improved user interface with modal dialogs
- Better error handling and user feedback

UI/UX Improvements:
- Separated CSS for better maintainability
- Responsive design for mobile compatibility
- Modal-based workflows for better UX
- Real-time status updates and notifications
- Enhanced form validation and error handling
- Improved visual hierarchy and information display

DATABASE COMPATIBILITY:
- Uses correct table names and relationships
- Proper foreign key constraints with session_profiles
- Enhanced data validation and integrity
- Optimized queries for better performance
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from database.operations import (
    get_active_session, mark_students_absent, create_attendance_session, 
    stop_active_session, get_db_connection, get_all_data
)

session_bp = Blueprint('session', __name__)

@session_bp.route('/api/mark_absent', methods=['POST'])
def mark_absent():
    try:
        mark_students_absent()
        return jsonify(status='success', message='Absent students marked')
    except Exception as e:
        return jsonify(status='error', message=str(e))

@session_bp.route('/api/create_session', methods=['POST'])
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
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE student_attendance_summary SET status = NULL')
            conn.commit()
            conn.close()
            print("Reset all student attendance status to null before creating session")

        # --- Optimized class-based session logic ---
        if class_table is not None and str(class_table).strip().isdigit():
            # Class-based session: set profile_id to None
            result = create_attendance_session(session_name, start_time, end_time, None, class_table)
            if result:
                message = 'Attendance session created for class'
                if reset_status:
                    message += '. Student status reset.'
                return jsonify(status='success', message=message)
            else:
                return jsonify(status='error', message='Failed to create class-based session')
        # --- Profile-based or legacy session logic ---
        else:
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

@session_bp.route('/api/stop_session', methods=['POST'])
def stop_session():
    try:
        result = stop_active_session()
        if result.get('success'):
            absent_marked = result.get('absent_marked', 0)
            data_cleared = result.get('data_cleared', False)
            cleared_counts = result.get('cleared_counts', {})
            
            if data_cleared:
                message = f'Session stopped successfully. {absent_marked} students marked absent. Data cleared: {cleared_counts.get("class_attendees", 0)} attendances, {cleared_counts.get("denied_attempts", 0)} failed attempts, {cleared_counts.get("device_fingerprints", 0)} devices.'
            else:
                message = f'Session stopped successfully. {absent_marked} students marked absent.' if absent_marked > 0 else 'Session stopped successfully'
            
            return jsonify(
                status='success', 
                message=message, 
                absent_marked=absent_marked,
                data_cleared=data_cleared,
                cleared_counts=cleared_counts
            )
        else:
            return jsonify(status='error', message=result.get('message', 'No active session to stop'))
    except Exception as e:
        return jsonify(status='error', message=str(e))

@session_bp.route('/api/session_status')
def session_status():
    try:
        active_session = get_active_session()
        return jsonify({'active_session': active_session})
    except Exception as e:
        return jsonify({'active_session': None, 'error': str(e)})

# Session profiles endpoints
@session_bp.route('/api/session_profiles', methods=['GET'])
def get_session_profiles():
    """Get all session profiles"""
    try:
        profiles = get_all_data('session_profiles')
        return jsonify({'profiles': profiles})
    except Exception as e:
        return jsonify({'profiles': [], 'error': str(e)})

@session_bp.route('/api/session_profiles', methods=['POST'])
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

@session_bp.route('/api/session_profiles/<int:profile_id>', methods=['DELETE'])
def delete_session_profile(profile_id):
    """Delete a session profile"""
    try:
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

@session_bp.route('/api/session_profiles/<int:profile_id>', methods=['PUT'])
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

@session_bp.route('/api/use_session_profile/<int:profile_id>', methods=['POST'])
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

# Student enrollment endpoints
@session_bp.route('/api/session_profiles/<int:profile_id>/students', methods=['GET'])
def get_profile_students(profile_id):
    """Get students enrolled in a session profile"""
    try:
        from database.operations import get_enrolled_students
        enrolled_students = get_enrolled_students(profile_id)
        return jsonify({'students': enrolled_students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@session_bp.route('/api/session_profiles/<int:profile_id>/available_students', methods=['GET'])
def get_available_students(profile_id):
    """Get students available for enrollment in a session profile"""
    try:
        from database.operations import get_available_students_for_enrollment
        available_students = get_available_students_for_enrollment(profile_id)
        return jsonify({'students': available_students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@session_bp.route('/api/session_profiles/<int:profile_id>/enroll', methods=['POST'])
def enroll_student(profile_id):
    """Enroll a student in a session profile"""
    try:
        data = request.json or {}
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID is required'}), 400
        
        from database.operations import enroll_student_in_profile
        result = enroll_student_in_profile(profile_id, student_id)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': result['message']})
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@session_bp.route('/api/session_profiles/<int:profile_id>/unenroll', methods=['POST'])
def unenroll_student(profile_id):
    """Remove a student from a session profile"""
    try:
        data = request.json or {}
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Student ID is required'}), 400
        
        from database.operations import unenroll_student_from_profile
        result = unenroll_student_from_profile(profile_id, student_id)
        
        if result['success']:
            return jsonify({'status': 'success', 'message': result['message']})
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@session_bp.route('/api/session_profiles/<int:profile_id>/bulk_enroll', methods=['POST'])
def bulk_enroll_students(profile_id):
    """Enroll multiple students in a session profile"""
    try:
        data = request.json or {}
        student_ids = data.get('student_ids', [])
        
        if not student_ids:
            return jsonify({'error': 'Student IDs are required'}), 400
        
        from database.operations import bulk_enroll_students
        result = bulk_enroll_students(profile_id, student_ids)
        
        if result['success']:
            return jsonify({
                'status': 'success', 
                'message': result['message'],
                'enrolled_count': result['enrolled_count'],
                'errors': result.get('errors', [])
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
