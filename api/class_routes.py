"""
Class Routes Module for Offline Attendance System

This module contains all class table management endpoints:
- Class record upload from Excel files
- Class table management and operations
- Class data retrieval and display
- Class table deletion and cleanup

Class Management Features:
- Upload class records from Excel files with metadata extraction
- Create and manage class-specific tables
- Display class information with proper formatting
- Delete class tables and associated data
"""

import sqlite3
import openpyxl
from flask import Blueprint, request, jsonify
from database.class_table_manager import create_class_table, insert_students as insert_class_students

class_bp = Blueprint('class', __name__)

@class_bp.route('/upload_class_record', methods=['POST'])
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

@class_bp.route('/api/class_tables', methods=['GET'])
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

@class_bp.route('/api/delete_class_table', methods=['POST'])
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

@class_bp.route('/api/classes')
def get_classes():
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

@class_bp.route('/api/classes/<table_name>/students', methods=['POST'])
def add_student_to_class(table_name):
    """Add a single student to a specific class table"""
    try:
        data = request.json or {}
        
        # Validate required fields
        required_fields = ['student_id', 'student_name', 'year_level', 'course']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Sanitize input data
        student_data = {
            'studentId': str(data['student_id']).strip(),
            'studentName': str(data['student_name']).strip(),
            'yearLevel': str(data['year_level']).strip(),
            'course': str(data['course']).strip()
        }
        
        # Validate table exists
        db_path = 'classes.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Class table not found'}), 404
        
        # Check if student already exists in this class
        cursor.execute(f'SELECT student_id FROM "{table_name}" WHERE student_id = ?', (student_data['studentId'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Student ID already exists in this class'}), 409
        
        # Insert the new student
        cursor.execute(f'''
            INSERT INTO "{table_name}" (student_id, student_name, year_level, course)
            VALUES (?, ?, ?, ?)
        ''', (student_data['studentId'], student_data['studentName'], 
              student_data['yearLevel'], student_data['course']))
        
        conn.commit()
        conn.close()
        
        # Also add to attendance.db if not already there
        try:
            attendance_conn = sqlite3.connect('attendance.db')
            attendance_cursor = attendance_conn.cursor()
            
            # Check if student exists in attendance.db
            attendance_cursor.execute("SELECT student_id FROM students WHERE student_id = ?", (student_data['studentId'],))
            if not attendance_cursor.fetchone():
                # Add to attendance.db
                attendance_cursor.execute(
                    "INSERT INTO students (student_id, name, year, course) VALUES (?, ?, ?, ?)",
                    (student_data['studentId'], student_data['studentName'], 
                     student_data['yearLevel'], student_data['course'])
                )
                attendance_conn.commit()
                print(f"Added student {student_data['studentId']} to attendance.db")
            
            attendance_conn.close()
        except Exception as e:
            print(f"Warning: Could not add student to attendance.db: {str(e)}")
            # Continue even if attendance.db insertion fails
        
        return jsonify({
            'status': 'success',
            'message': 'Student added successfully',
            'student': student_data
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/classes/<table_name>/students/<student_id>', methods=['DELETE'])
def remove_student_from_class(table_name, student_id):
    """Remove a student from a specific class table"""
    try:
        # Validate table exists
        db_path = 'classes.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Class table not found'}), 404
        
        # Check if student exists in this class
        cursor.execute(f'SELECT student_name FROM "{table_name}" WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        if not student:
            conn.close()
            return jsonify({'error': 'Student not found in this class'}), 404
        
        student_name = student[0]
        
        # Delete the student
        cursor.execute(f'DELETE FROM "{table_name}" WHERE student_id = ?', (student_id,))
        rows_affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({
                'status': 'success',
                'message': f'Student {student_name} removed from class successfully'
            })
        else:
            return jsonify({'error': 'Failed to remove student'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500