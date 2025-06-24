"""
Main Application Entry Point for Offline Attendance System

This is the primary Flask application file that initializes and runs the offline attendance
tracking system. It sets up the web server, registers API routes, configures database
connections, and provides network interface detection for multi-device access.

Main Features:
- Flask Web Application: Complete web server setup with template rendering
- API Route Registration: Automatic registration of all attendance API endpoints
- Database Initialization: Automatic database setup and migration on startup
- Network Interface Detection: Multi-IP support for hotspot and network scenarios
- Debug Mode: Development-friendly error reporting and auto-reload capabilities
- Route Monitoring: Comprehensive route registration logging for troubleshooting

Core Routes:
- / (index): Main dashboard and QR code generation interface
- /students: Student management and data import interface
- /dashboard: Attendance monitoring and session management
- /api/*: All API endpoints for attendance operations (via blueprint)

Application Flow:
1. Import Dependencies: Load Flask, database, and utility modules
2. Register Blueprints: Add API routes for attendance functionality
3. Define Template Routes: Set up web interface endpoints
4. Initialize Database: Create tables and run migrations
5. Network Detection: Find available IP addresses for access
6. Start Server: Launch Flask development server on all interfaces

Network Configuration:
- Host: 0.0.0.0 (accessible from all network interfaces)
- Port: 5000 (standard Flask development port)
- Multi-IP Support: Automatic detection of hotspot and network IPs
- Debug Mode: Enabled for development with detailed error reporting

Development Features:
- Route Registration Logging: Shows all available endpoints on startup
- Error Tracking: Comprehensive exception handling and stack traces
- Network Interface Display: Shows all possible access URLs
- Auto-reload Disabled: Prevents database lock issues during development

Used by: Direct execution for running the attendance system
Dependencies: Flask, database modules, network utilities, API blueprints
"""

from flask import Flask, render_template, request, jsonify
from flask import current_app as app
from database import init_db, migrate_database
from utils.network import get_all_network_interfaces
from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy.exc import SQLAlchemyError
import re

app = Flask(__name__)

# Register API blueprint
try:
    from api.routes import api_bp
    app.register_blueprint(api_bp)
except Exception as e:
    print(f"ERROR importing/registering api_bp: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Define your template routes BEFORE app.run()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/sessions')
def sessions():
    return render_template('sessions.html')

@app.route('/class_upload')
def class_upload():
    return render_template('class_upload.html')

@app.route('/api/session_profiles/<int:profile_id>', methods=['PUT'])
def update_session_profile(profile_id):
    try:
        data = request.get_json()
        # Update profile in database
        # Return success response
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save_class_upload', methods=['POST'])
def save_class_upload():
    data = request.get_json()
    sheet_name = data.get('sheet_name')
    records = data.get('data')

    # Sanitize table name
    table_name = re.sub(r'\W|^(?=\d)', '_', sheet_name.lower())

    # Define columns
    columns = [
        Column('id', Integer, primary_key=True, autoincrement=True),
        Column('professor_name', String(128)),
        Column('room_type', String(64)),
        Column('venue', String(128)),
        Column('student_id', String(64)),
        Column('student_name', String(128)),
        Column('year_level', String(32)),
        Column('course', String(64)),
    ]

    metadata = MetaData(bind=app.db.engine)
    # Drop table if exists (optional)
    # if app.db.engine.has_table(table_name):
    #     Table(table_name, metadata, autoload_with=app.db.engine).drop(app.db.engine)

    # Create table dynamically
    table = Table(table_name, metadata, *columns)
    metadata.create_all(app.db.engine, tables=[table])

    # Insert data
    insert_data = []
    for row in records:
        insert_data.append({
            'professor_name': row.get('Professor Name', ''),
            'room_type': row.get('Room Type', ''),
            'venue': row.get('Venue (Building & Room No.)', ''),
            'student_id': row.get('Student ID', ''),
            'student_name': row.get('Student Name', ''),
            'year_level': row.get('Year Level', ''),
            'course': row.get('Course', ''),
        })

    try:
        with app.db.engine.connect() as conn:
            conn.execute(table.insert(), insert_data)
        return jsonify({'success': True})
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Attendance System")
    print("=" * 40)
    
    try:
        init_db()
        migrate_database()
        
        interfaces = get_all_network_interfaces()
        print(f"Primary IP: {interfaces[0]}")
        print("\nAccess URLs:")
        for ip in interfaces[:3]:  # Show top 3
            print(f"  → http://{ip}:5000")
        
        # Debug: Print all registered routes
        print("\n=== REGISTERED ROUTES ===")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")
        print("========================\n")
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()