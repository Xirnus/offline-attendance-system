"""
Session Routes Module for Offline Attendance System

This module contains all session management endpoints:
- Attendance session creation and management
- Session status monitoring
- Session profiles management
- Session control (start/stop)

Session Management Features:
- Create and manage attendance sessions
- Session profiles for reusable configurations
- Active session monitoring
- Automated absent marking on session end
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

@session_bp.route('/api/stop_session', methods=['POST'])
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
