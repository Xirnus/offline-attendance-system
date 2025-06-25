"""
Student Routes Module for Offline Attendance System

This module contains all student-related API endpoints including:
- Student upload and import (Excel/CSV)
- Student CRUD operations (Create, Read, Update, Delete)
- Student attendance management
- Student data retrieval and statistics

Key Endpoints:
- /upload_students - Import students from Excel/CSV files
- /get_students - Retrieve all students
- /clear_students - Delete all students
- /api/students/<id> - Individual student operations (GET, PUT, DELETE)
- /api/students_status - Get student status information
- /api/students_with_attendance - Get students with attendance data
- /api/add_student - Add a single student
"""

import os
import re
from io import StringIO
import csv
import pandas as pd
from flask import Blueprint, request, jsonify
from database.operations import (
    get_students_with_attendance_data, insert_students, 
    get_all_students, clear_all_students
)

# Create the student routes blueprint
student_bp = Blueprint('student', __name__)

def normalize_header(name: str) -> str:
    """
    Normalize a header name by:
    - Converting to string
    - Stripping whitespace
    - Removing underscores and spaces (and you could remove other non-alphanumerics if desired)
    - Lowercasing
    E.g. "School ID" -> "schoolid", "Year_Level" -> "yearlevel"
    """
    if name is None:
        return ""
    # Keep only alphanumeric characters, or remove underscores/spaces:
    # Here: remove anything that's not a letter or digit.
    s = str(name).strip().lower()
    # Remove spaces and underscores:
    s = re.sub(r'[\s_]+', '', s)
    # If you want to also remove other punctuation, you could:
    # s = re.sub(r'[^a-z0-9]', '', s)
    return s

@student_bp.route('/upload_students', methods=['POST'])
def upload_students():
    """
    Upload students via Excel (.xlsx/.xls) or CSV.
    Required columns (case-insensitive, underscore/space-insensitive) are:
      School_ID, Name, Course, Year_Level
    """
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        filename = file.filename or ""
        filename_lower = filename.lower()

        # Canonical required columns
        required_columns = ['School_ID', 'Name', 'Course', 'Year_Level']
        # Build normalized forms for required columns
        normalized_required = { normalize_header(col): col for col in required_columns }
        # normalized_required maps e.g. "schoolid" -> "School_ID"

        rows = None

        # --- Excel files ---
        if filename_lower.endswith(('.xlsx', '.xls')):
            try:
                df = pd.read_excel(file)
            except Exception as e:
                return jsonify({'error': f'Error reading Excel file: {str(e)}'}), 400

            df_cols = list(df.columns)
            # Map normalized -> actual column name
            df_normalized_map = {}
            for col in df_cols:
                norm = normalize_header(col)
                # If duplicate normalized keys appear, first one is kept
                if norm not in df_normalized_map:
                    df_normalized_map[norm] = col

            # Check for missing required columns
            missing = []
            actual_cols = {}
            for norm_req, canon in normalized_required.items():
                if norm_req not in df_normalized_map:
                    missing.append(canon)
                else:
                    actual_cols[canon] = df_normalized_map[norm_req]
            if missing:
                return jsonify({
                    'error': 'Missing required columns in Excel (case-insensitive, underscore/space-insensitive): '
                             + ', '.join(missing),
                    'found_columns': df_cols
                }), 400

            # Extract and rename
            df_selected = df[
                [
                    actual_cols['School_ID'],
                    actual_cols['Name'],
                    actual_cols['Course'],
                    actual_cols['Year_Level']
                ]
            ].copy()
            df_selected.columns = ['student_id', 'name', 'course', 'year_raw']

            # Parse year_raw into integer 1–5, default 1
            def extract_year(val):
                if pd.isna(val):
                    return 1
                s = str(val).strip()
                match = re.search(r'(\d+)', s)
                if match:
                    y = int(match.group(1))
                    return y if 1 <= y <= 5 else 1
                try:
                    y2 = int(float(s))
                    return y2 if 1 <= y2 <= 5 else 1
                except Exception:
                    return 1

            df_selected['year'] = df_selected['year_raw'].apply(extract_year)
            rows = df_selected[['student_id', 'name', 'course', 'year']].values.tolist()

        # --- CSV files ---
        elif filename_lower.endswith('.csv'):
            try:
                content = file.read().decode('utf-8')
            except Exception as e:
                return jsonify({'error': f'Error reading CSV file: {str(e)}'}), 400

            reader = csv.reader(StringIO(content))
            all_rows = list(reader)
            if not all_rows or len(all_rows) < 2:
                return jsonify({'error': 'CSV must have at least header and one data row'}), 400

            header = all_rows[0]
            # Build normalized header -> index map
            header_map = {}
            for idx, col in enumerate(header):
                norm = normalize_header(col)
                if norm not in header_map:
                    header_map[norm] = idx

            # Check required columns
            missing = []
            actual_indices = {}
            for norm_req, canon in normalized_required.items():
                if norm_req not in header_map:
                    missing.append(canon)
                else:
                    actual_indices[canon] = header_map[norm_req]
            if missing:
                return jsonify({
                    'error': 'Missing required columns in CSV (case-insensitive, underscore/space-insensitive): '
                             + ', '.join(missing),
                    'found_columns': header
                }), 400

            # Process rows
            processed_rows = []
            for row in all_rows[1:]:
                # student_id index
                idx_id = actual_indices['School_ID']
                if idx_id >= len(row):
                    continue
                student_id_val = row[idx_id].strip()
                if not student_id_val:
                    continue
                # other fields
                idx_name = actual_indices['Name']
                idx_course = actual_indices['Course']
                idx_year = actual_indices['Year_Level']

                name_val = row[idx_name].strip() if idx_name < len(row) else ""
                course_val = row[idx_course].strip() if idx_course < len(row) else ""
                year_raw = row[idx_year].strip() if idx_year < len(row) else ""

                match = re.search(r'(\d+)', year_raw)
                if match:
                    y = int(match.group(1))
                    year_int = y if 1 <= y <= 5 else 1
                else:
                    try:
                        y2 = int(float(year_raw))
                        year_int = y2 if 1 <= y2 <= 5 else 1
                    except Exception:
                        year_int = 1

                processed_rows.append([student_id_val, name_val, course_val, year_int])

            rows = processed_rows

        else:
            return jsonify({'error': 'Unsupported file type. Only .xlsx, .xls, .csv allowed.'}), 400

        if rows is None:
            return jsonify({'error': 'No rows parsed from file.'}), 400

        # Call existing operations.insert_students; no changes needed there
        count = insert_students(rows)
        return jsonify({'message': f'Successfully imported {count} students'}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@student_bp.route('/get_students')
def get_students():
    try:
        students = get_all_students()
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'students': [], 'error': str(e)})

@student_bp.route('/api/students_status')
def students_status():
    try:
        students = get_all_students()
        return jsonify(students)
    except Exception as e:
        return jsonify([])
    
@student_bp.route('/clear_students', methods=['POST'])
def clear_students():
    try:
        count = clear_all_students()
        return jsonify({'deleted': count})
    except Exception as e:
        return jsonify({'error': str(e)})

@student_bp.route('/api/students_with_attendance')
def get_students_with_attendance():
    """Get all students with their attendance data"""
    try:
        students = get_students_with_attendance_data()
        return jsonify({'students': students})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/api/students/<student_id>', methods=['GET'])
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

@student_bp.route('/api/students/<student_id>', methods=['PUT'])
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

@student_bp.route('/api/students/<student_id>', methods=['DELETE'])
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

@student_bp.route('/api/students/<student_id>/attendance', methods=['PUT'])
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
        
        # Add student_id for WHERE clause
        params.append(student_id)
        
        # Execute update
        update_query = f'''
            UPDATE students 
            SET {', '.join(update_fields)}
            WHERE student_id = ?
        '''
        
        cursor.execute(update_query, params)
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if rows_affected == 0:
            return jsonify({'error': 'No changes were made'}), 400
        
        return jsonify({'message': 'Student attendance updated successfully'})
        
    except Exception as e:
        print(f"Error updating attendance for student {student_id}: {e}")
        return jsonify({'error': str(e)}), 500

@student_bp.route('/api/add_student', methods=['POST'])
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
        count = insert_students([[student_id, name, course, year]])
        
        if count == 1:
            return jsonify({'message': 'Student added successfully'})
        else:
            return jsonify({'error': 'Failed to add student'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500