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
from database.class_table_manager import (
    create_class_table, insert_students as insert_class_students,
    OptimizedClassManager, create_class_optimized
)

class_bp = Blueprint('class', __name__)

def convert_year_to_integer(year_level):
    """Convert year level to integer for database storage"""
    if isinstance(year_level, int):
        return year_level
    
    year_str = str(year_level).lower().strip()
    
    # Extract numeric value from common year level formats
    if '1st' in year_str or 'first' in year_str or year_str == '1':
        return 1
    elif '2nd' in year_str or 'second' in year_str or year_str == '2':
        return 2
    elif '3rd' in year_str or 'third' in year_str or year_str == '3':
        return 3
    elif '4th' in year_str or 'fourth' in year_str or year_str == '4':
        return 4
    elif '5th' in year_str or 'fifth' in year_str or year_str == '5':
        return 5
    
    # Try to extract any number from the string
    import re
    match = re.search(r'(\d+)', year_str)
    if match:
        return int(match.group(1))
    
    # Default to 1 if no valid year found
    print(f"Warning: Unable to parse year level: {year_level}, defaulting to 1")
    return 1

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
        
        for i, row in enumerate(rows[:8]):  # Check first 8 rows for metadata
            if not any(row):  # Skip empty rows
                continue
                
            # Look for specific metadata patterns
            if row[0] and len(row) > 1:
                key = str(row[0]).lower().strip()
                value = str(row[1]).strip() if row[1] else None
                
                if 'professor' in key and value:
                    metadata['professor'] = value
                elif 'class' in key and 'name' in key and value:
                    metadata['class_name'] = value
                elif 'room' in key and 'type' in key and value:
                    metadata['room_type'] = value
                elif 'building' in key and value:
                    metadata['building'] = value
                elif 'venue' in key and value:
                    metadata['venue'] = value

        # Set defaults if not found
        professor_name = metadata.get('professor', 'Unknown Professor')
        class_name = metadata.get('class_name', file_name)  # Use extracted class name or file name
        room_type = metadata.get('room_type', 'Classroom')
        venue = metadata.get('venue', 'Main Building')
        building = metadata.get('building', 'Main Building')

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

        # Database operations - Choose between old redundant method and new optimized method
        use_optimized = request.form.get('use_optimized', 'false').lower() == 'true'
        
        if use_optimized:
            # NEW OPTIMIZED METHOD - eliminates data redundancy
            print("Using optimized classes database schema...")
            manager = OptimizedClassManager()
            
            class_id = manager.import_from_excel_data(
                class_name=class_name,  # Use extracted class name
                professor_name=professor_name,
                student_data=student_data
            )
            
            if class_id:
                success_message = f'Successfully imported {len(student_data)} students using optimized schema'
            else:
                return jsonify({'error': 'Failed to create class with optimized schema'}), 500
        else:
            # OLD METHOD - creates redundant table per class (for backward compatibility)
            print("Using legacy table-per-class method...")
            columns = [
                ('student_id', 'TEXT'),
                ('student_name', 'TEXT'),
                ('year_level', 'TEXT'),
                ('course', 'TEXT')
            ]
            
            create_class_table(table_name, columns, db_path='classes.db')
            insert_class_students(table_name, student_data, db_path='classes.db')
            success_message = f'Successfully imported {len(student_data)} students to class table'
        
        # Skip attendance.db insertion for uploaded class records
        # Class records are managed separately from the main attendance system
        print("Skipping attendance.db insertion for uploaded class records - class tables are managed separately")

        return jsonify({
            'message': success_message,
            'display_name': display_name,
            'professor': professor_name,
            'room_type': room_type,
            'venue': venue,
            'optimized': use_optimized,
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
        
        # Convert year_level to integer for attendance.db
        year_level_int = convert_year_to_integer(data['year_level'])
        
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
        
        # For manually added students, also add to attendance.db if not already there
        # (This is different from bulk uploads which are class-specific)
        try:
            attendance_conn = sqlite3.connect('attendance.db')
            attendance_cursor = attendance_conn.cursor()
            
            # Check if student exists in attendance.db
            attendance_cursor.execute("SELECT student_id FROM students WHERE student_id = ?", (student_data['studentId'],))
            if not attendance_cursor.fetchone():
                # Add to attendance.db with integer year
                attendance_cursor.execute(
                    "INSERT INTO students (student_id, name, year, course) VALUES (?, ?, ?, ?)",
                    (student_data['studentId'], student_data['studentName'], 
                     year_level_int, student_data['course'])
                )
                attendance_conn.commit()
                print(f"Added manually entered student {student_data['studentId']} to attendance.db with year {year_level_int}")
            else:
                print(f"Student {student_data['studentId']} already exists in attendance.db")
            
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

# ===================================================================
# OPTIMIZED CLASS API ENDPOINTS
# These endpoints use the new normalized schema instead of table-per-class
# ===================================================================

@class_bp.route('/api/optimized/setup', methods=['POST'])
def setup_optimized_schema():
    """Initialize the optimized classes database schema"""
    try:
        from database.models import create_optimized_classes_schema
        success = create_optimized_classes_schema()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Optimized classes schema created successfully'
            })
        else:
            return jsonify({'error': 'Failed to create optimized schema'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/migrate', methods=['POST'])
def migrate_to_optimized():
    """Migrate existing class tables to optimized schema"""
    try:
        from database.models import migrate_existing_classes_data
        success = migrate_existing_classes_data()
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Successfully migrated to optimized schema'
            })
        else:
            return jsonify({'error': 'Migration failed'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes', methods=['GET'])
def get_optimized_classes():
    """Get all classes using the optimized schema"""
    try:
        manager = OptimizedClassManager()
        classes = manager.get_all_classes()
        
        return jsonify({
            'status': 'success',
            'classes': classes,
            'count': len(classes)
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes/<int:class_id>/students', methods=['GET'])
def get_optimized_class_students(class_id):
    """Get students enrolled in a specific class using optimized schema"""
    try:
        manager = OptimizedClassManager()
        students = manager.get_class_students(class_id)
        
        return jsonify({
            'status': 'success',
            'students': students,
            'count': len(students),
            'class_id': class_id
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes', methods=['POST'])
def create_optimized_class():
    """Create a new class using optimized schema"""
    try:
        data = request.get_json()
        
        if not data or not data.get('class_name') or not data.get('professor_name'):
            return jsonify({'error': 'class_name and professor_name are required'}), 400
        
        manager = OptimizedClassManager()
        class_id = manager.create_class(
            class_name=data['class_name'],
            professor_name=data['professor_name'],
            course_code=data.get('course_code'),
            semester=data.get('semester'),
            academic_year=data.get('academic_year')
        )
        
        if class_id:
            return jsonify({
                'status': 'success',
                'message': 'Class created successfully',
                'class_id': class_id
            })
        else:
            return jsonify({'error': 'Failed to create class'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes/<int:class_id>/enroll', methods=['POST'])
def enroll_students_optimized(class_id):
    """Enroll students in a class using optimized schema"""
    try:
        data = request.get_json()
        
        if not data or not data.get('student_ids'):
            return jsonify({'error': 'student_ids array is required'}), 400
        
        manager = OptimizedClassManager()
        enrolled_count = manager.enroll_students(class_id, data['student_ids'])
        
        return jsonify({
            'status': 'success',
            'message': f'Enrolled {enrolled_count} students successfully',
            'enrolled_count': enrolled_count,
            'total_requested': len(data['student_ids'])
        })
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes/<int:class_id>', methods=['DELETE'])
def delete_class_optimized(class_id):
    """Delete a class and all its enrollments using optimized schema"""
    try:
        manager = OptimizedClassManager()
        success = manager.delete_class(class_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Class {class_id} deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete class'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@class_bp.route('/api/optimized/classes/<int:class_id>/students/<student_id>', methods=['DELETE'])
def unenroll_student_optimized(class_id, student_id):
    """Remove a student from a class using optimized schema"""
    try:
        manager = OptimizedClassManager()
        success = manager.unenroll_student(class_id, student_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Student {student_id} removed from class successfully'
            })
        else:
            return jsonify({'error': 'Failed to remove student from class'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500