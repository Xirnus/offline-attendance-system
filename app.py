import random, string, time
import sqlite3
from io import BytesIO
import os
from datetime import datetime
import json

import socket
import subprocess
import platform

from flask import Flask, render_template, request, send_file, jsonify
import qrcode

from collections import defaultdict
import threading

app = Flask(__name__)

def migrate_database():
    """Migrate database to add missing columns"""
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    try:
        # Check if fingerprint_hash column exists in attendances table
        cursor.execute("PRAGMA table_info(attendances)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fingerprint_hash' not in columns:
            print("Adding fingerprint_hash column to attendances table...")
            cursor.execute('ALTER TABLE attendances ADD COLUMN fingerprint_hash TEXT')
            print("✓ Added fingerprint_hash column")
        
        # Check if fingerprint_hash column exists in denied_attempts table
        cursor.execute("PRAGMA table_info(denied_attempts)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fingerprint_hash' not in columns:
            print("Adding fingerprint_hash column to denied_attempts table...")
            cursor.execute('ALTER TABLE denied_attempts ADD COLUMN fingerprint_hash TEXT')
            print("✓ Added fingerprint_hash column to denied_attempts")
        
        # Check if active_tokens has fingerprint_hash column
        cursor.execute("PRAGMA table_info(active_tokens)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'fingerprint_hash' not in columns:
            print("Adding fingerprint_hash column to active_tokens table...")
            cursor.execute('ALTER TABLE active_tokens ADD COLUMN fingerprint_hash TEXT')
            print("✓ Added fingerprint_hash column to active_tokens")
        
        # Check if device_signature column exists in active_tokens
        if 'device_signature' not in columns:
            print("Adding device_signature column to active_tokens table...")
            cursor.execute('ALTER TABLE active_tokens ADD COLUMN device_signature TEXT')
            print("✓ Added device_signature column to active_tokens")
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()



# Database initialization
def init_db():
    """Initialize SQLite database with required tables"""
    try:
        print("Attempting to initialize database...")
        
        # Check if database file exists
        if os.path.exists('attendance.db'):
            print("✓ Database file exists")
        else:
            print("⚠ Database file doesn't exist, will be created")
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        print("✓ Connected to database")
        
        # Create tables with detailed logging
        print("Creating active_tokens table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                opened BOOLEAN DEFAULT FALSE,
                device_signature TEXT,
                fingerprint_hash TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        print("✓ active_tokens table created")
        
        print("Creating attendances table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                fingerprint_hash TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                year TEXT NOT NULL,
                device_info TEXT
            )
        ''')
        print("✓ attendances table created")
        
        print("Creating denied_attempts table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS denied_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                fingerprint_hash TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                year TEXT NOT NULL,
                device_info TEXT
            )
        ''')
        print("✓ denied_attempts table created")
        
        print("Creating device_fingerprints table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_hash TEXT UNIQUE NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                device_info TEXT
            )
        ''')
        print("✓ device_fingerprints table created")
        
        print("Creating settings table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                max_uses_per_device INTEGER DEFAULT 1,
                time_window_minutes INTEGER DEFAULT 1440,
                enable_fingerprint_blocking BOOLEAN DEFAULT TRUE
            )
        ''')
        print("✓ settings table created")
        
        # Insert default settings if not exists
        print("Checking for default settings...")
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        if not cursor.fetchone():
            print("Inserting default settings...")
            cursor.execute('''
                INSERT INTO settings (id, max_uses_per_device, time_window_minutes, enable_fingerprint_blocking)
                VALUES (?, ?, ?, ?)
            ''', ('config', 1, 1440, True))
            print("✓ Default settings inserted")
        else:
            print("✓ Default settings already exist")
        
        # Verify tables were created
        print("Verifying table creation...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✓ Tables in database: {[table[0] for table in tables]}")
        
        conn.commit()
        print("✓ Database changes committed")
        conn.close()
        print("✓ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()

# Default settings
DEFAULT_SETTINGS = {
    'max_uses_per_device': 1,
    'time_window_minutes': 1440,  # 24 hours
    'enable_fingerprint_blocking': True
}

# Rate limiting storage
request_counts = defaultdict(list)
rate_limit_lock = threading.Lock()

def is_rate_limited(ip_address, max_requests=5, time_window=60):
    """Check if IP is rate limited (max 5 requests per minute)"""
    current_time = time.time()
    
    with rate_limit_lock:
        # Clean old requests
        request_counts[ip_address] = [
            req_time for req_time in request_counts[ip_address] 
            if current_time - req_time < time_window
        ]
        
        # Check if over limit
        if len(request_counts[ip_address]) >= max_requests:
            return True
        
        # Add current request
        request_counts[ip_address].append(current_time)
        return False

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

def get_settings():
    """Get settings from database or return defaults"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'max_uses_per_device': row['max_uses_per_device'],
                'time_window_minutes': row['time_window_minutes'],
                'enable_fingerprint_blocking': bool(row['enable_fingerprint_blocking'])
            }
        else:
            return DEFAULT_SETTINGS
    except Exception as e:
        print(f"Error getting settings: {e}")
        return DEFAULT_SETTINGS

def is_fingerprint_allowed(fingerprint_hash):
    """Check if device fingerprint is allowed to check in"""
    settings = get_settings()
    
    if not settings['enable_fingerprint_blocking']:
        return True, "Fingerprint blocking disabled"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check recent usage within time window
        time_threshold = time.time() - (settings['time_window_minutes'] * 60)
        
        cursor.execute('''
            SELECT COUNT(*) as usage_count 
            FROM attendances 
            WHERE fingerprint_hash = ? AND timestamp > ?
        ''', (fingerprint_hash, time_threshold))
        
        row = cursor.fetchone()
        usage_count = row['usage_count'] if row else 0
        
        conn.close()
        
        if usage_count >= settings['max_uses_per_device']:
            return False, f"Device already used {usage_count} times in the last {settings['time_window_minutes'] // 60} hours"
        
        return True, "Device allowed"
        
    except Exception as e:
        print(f"Error checking fingerprint: {e}")
        return True, "Error checking fingerprint, allowing access"

def store_device_fingerprint(fingerprint_hash, device_info):
    """Store or update device fingerprint information"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if fingerprint exists
        cursor.execute('SELECT * FROM device_fingerprints WHERE fingerprint_hash = ?', (fingerprint_hash,))
        existing = cursor.fetchone()
        
        current_time = datetime.utcnow().isoformat()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE device_fingerprints 
                SET last_seen = ?, usage_count = usage_count + 1, device_info = ?
                WHERE fingerprint_hash = ?
            ''', (current_time, device_info, fingerprint_hash))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO device_fingerprints 
                (fingerprint_hash, first_seen, last_seen, usage_count, device_info)
                VALUES (?, ?, ?, ?, ?)
            ''', (fingerprint_hash, current_time, current_time, 1, device_info))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error storing device fingerprint: {e}")

def extract_device_signature(ua):
    """Extract a simplified device signature from User-Agent"""
    ua = ua.lower()
    if 'iphone' in ua:
        return 'iphone'
    elif 'android' in ua:
        return 'android'
    elif 'ipad' in ua:
        return 'ipad'
    elif 'mobile' in ua:
        return 'mobile'
    else:
        return 'desktop'

@app.route('/')
def admin_dashboard():
    return render_template('dashboard.html')

@app.route('/generate_qr')
def generate_qr():
    # Rate limiting check
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if is_rate_limited(client_ip):
        return "Rate limit exceeded. Please wait before generating another QR code.", 429
    
    token = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Store token in database
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO active_tokens (token, timestamp, used, opened, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (token, time.time(), False, False, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        
        print(f"Generated new token: {token}")
        
    except Exception as e:
        print(f"Error storing token: {e}")
        return "Error generating QR code", 500
    
    # Generate QR code URL
    host = request.headers.get('Host', 'localhost:5000')
    scheme = 'https' if request.is_secure else 'http'
    base_url = f"{scheme}://{host}"
    
    qr_data = base_url + '/scan/' + token
    img = qrcode.make(qr_data)
    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/scan/<token>')
def scan(token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM active_tokens WHERE token = ?', (token,))
        token_data = cursor.fetchone()
        
        if not token_data:
            conn.close()
            return "Invalid QR code", 400
            
        if token_data['used']:
            conn.close()
            return "QR code already used", 400

        ua = request.headers.get('User-Agent', '')
        device_sig = extract_device_signature(ua)
        
        # First time opening - record device signature
        if not token_data['opened']:
            cursor.execute('''
                UPDATE active_tokens 
                SET opened = ?, device_signature = ?
                WHERE token = ?
            ''', (True, device_sig, token))
            conn.commit()
        # Check if same device type
        elif token_data['device_signature'] != device_sig:
            conn.close()
            return "<h3>QR can only be used on the same type of device that first opened it.</h3>", 400

        conn.close()
        return render_template('index.html', token=token)
    
    except Exception as e:
        print(f"Error in scan: {e}")
        return "Error processing QR code", 500

@app.route('/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json or {}
        token = data.get('token', '')
        fingerprint_hash = data.get('fingerprint_hash', '')
        name = data.get('name', '')
        course = data.get('course', '')
        year = data.get('year', '')
        device_info = json.dumps(data.get('device_info', {}))
        
        # Validate required fields
        if not all([token, fingerprint_hash, name, course, year]):
            return jsonify(status='error', message='Missing required fields')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get token from database
        cursor.execute('SELECT * FROM active_tokens WHERE token = ?', (token,))
        token_data = cursor.fetchone()
        
        if not token_data:
            # Store denied attempt
            cursor.execute('''
                INSERT INTO denied_attempts 
                (token, fingerprint_hash, timestamp, created_at, reason, name, course, year, device_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token, fingerprint_hash, time.time(), datetime.utcnow().isoformat(), 
                  'invalid_token', name, course, year, device_info))
            conn.commit()
            conn.close()
            return jsonify(status='error', message='Invalid token')
        
        if token_data['used']:
            # Store denied attempt
            cursor.execute('''
                INSERT INTO denied_attempts 
                (token, fingerprint_hash, timestamp, created_at, reason, name, course, year, device_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token, fingerprint_hash, time.time(), datetime.utcnow().isoformat(), 
                  'already_used', name, course, year, device_info))
            conn.commit()
            conn.close()
            return jsonify(status='error', message='Token already used')
        
        # Check if fingerprint is allowed
        allowed, reason = is_fingerprint_allowed(fingerprint_hash)
        if not allowed:
            # Store denied attempt
            cursor.execute('''
                INSERT INTO denied_attempts 
                (token, fingerprint_hash, timestamp, created_at, reason, name, course, year, device_info)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (token, fingerprint_hash, time.time(), datetime.utcnow().isoformat(), 
                  'fingerprint_blocked', name, course, year, device_info))
            conn.commit()
            conn.close()
            return jsonify(status='error', message=reason)
        
        # Mark token as used and store fingerprint hash
        cursor.execute('''
            UPDATE active_tokens 
            SET used = ?, fingerprint_hash = ? 
            WHERE token = ?
        ''', (True, fingerprint_hash, token))
        
        # Store attendance
        cursor.execute('''
            INSERT INTO attendances 
            (token, fingerprint_hash, timestamp, created_at, name, course, year, device_info)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (token, fingerprint_hash, time.time(), datetime.utcnow().isoformat(), 
              name, course, year, device_info))
        
        conn.commit()
        conn.close()
        
        # Store device fingerprint information
        store_device_fingerprint(fingerprint_hash, device_info)
        
        return jsonify(status='success', message='Attendance recorded successfully')
    
    except Exception as e:
        print(f"Error in checkin: {e}")
        return jsonify(status='error', message='Server error'), 500

@app.route('/api/attendances')
def api_attendances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM attendances ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        attendances = []
        for row in rows:
            attendances.append({
                'id': row['id'],
                'token': row['token'],
                'fingerprint_hash': row['fingerprint_hash'][:8] + '...',  # Show only first 8 chars for privacy
                'timestamp': row['timestamp'],
                'created_at': row['created_at'],
                'name': row['name'],
                'course': row['course'],
                'year': row['year'],
                'device_info': row['device_info']
            })
        
        return jsonify(attendances)
    except Exception as e:
        print(f"Error getting attendances: {e}")
        return jsonify([])

@app.route('/api/denied')
def api_denied():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM denied_attempts ORDER BY timestamp DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        denied = []
        for row in rows:
            denied.append({
                'id': row['id'],
                'token': row['token'],
                'fingerprint_hash': row['fingerprint_hash'][:8] + '...' if row['fingerprint_hash'] else 'N/A',
                'timestamp': row['timestamp'],
                'created_at': row['created_at'],
                'reason': row['reason'],
                'name': row['name'],
                'course': row['course'],
                'year': row['year'],
                'device_info': row['device_info']
            })
        
        return jsonify(denied)
    except Exception as e:
        print(f"Error getting denied attempts: {e}")
        return jsonify([])

@app.route('/api/device_fingerprints')
def api_device_fingerprints():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM device_fingerprints ORDER BY last_seen DESC')
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to list of dicts
        fingerprints = []
        for row in rows:
            fingerprints.append({
                'id': row['id'],
                'fingerprint_hash': row['fingerprint_hash'][:8] + '...',  # Show only first 8 chars
                'first_seen': row['first_seen'],
                'last_seen': row['last_seen'],
                'usage_count': row['usage_count'],
                'device_info': row['device_info']
            })
        
        return jsonify(fingerprints)
    except Exception as e:
        print(f"Error getting device fingerprints: {e}")
        return jsonify([])

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    try:
        if request.method == 'GET':
            return jsonify(get_settings())
        
        data = request.json or {}
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update settings
        max_uses = int(data.get('max_uses_per_device', DEFAULT_SETTINGS['max_uses_per_device']))
        time_window = int(data.get('time_window_minutes', DEFAULT_SETTINGS['time_window_minutes']))
        enable_blocking = bool(data.get('enable_fingerprint_blocking', DEFAULT_SETTINGS['enable_fingerprint_blocking']))
        
        cursor.execute('''
            UPDATE settings 
            SET max_uses_per_device = ?, time_window_minutes = ?, enable_fingerprint_blocking = ?
            WHERE id = ?
        ''', (max_uses, time_window, enable_blocking, 'config'))
        
        conn.commit()
        conn.close()
        
        return jsonify(get_settings())
    
    except Exception as e:
        print(f"Error with settings: {e}")
        return jsonify(get_settings())

@app.route('/api/export_data')
def export_data():
    """Export all data for backup or transfer"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all data
        cursor.execute('SELECT * FROM attendances')
        attendances = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM denied_attempts')
        denied = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM settings')
        settings = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM device_fingerprints')
        fingerprints = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        export_data = {
            'attendances': attendances,
            'denied_attempts': denied,
            'settings': settings,
            'device_fingerprints': fingerprints,
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(export_data)
    except Exception as e:
        print(f"Error exporting data: {e}")
        return jsonify({'error': str(e)})

def get_hotspot_ip():
    """Get the correct IP for Windows hotspot"""
    if platform.system() == "Windows":
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            # Look for Microsoft Wi-Fi Direct Virtual Adapter
            for i, line in enumerate(lines):
                if 'Microsoft Wi-Fi Direct Virtual Adapter' in line or 'Local Area Connection* 1' in line:
                    # Look for IPv4 address in next few lines
                    for j in range(i, min(i+10, len(lines))):
                        if 'IPv4 Address' in lines[j]:
                            ip = lines[j].split(':')[1].strip()
                            return ip
                            
            # Fallback: look for 192.168.137.x (typical Windows hotspot range)
            for line in lines:
                if 'IPv4 Address' in line and '192.168.137.' in line:
                    ip = line.split(':')[1].strip()
                    return ip
                    
        except Exception as e:
            print(f"Error getting hotspot IP: {e}")
    
    # Fallback to default method
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_all_network_interfaces():
    """Get all possible network interfaces"""
    interfaces = []
    
    # Primary IP
    primary_ip = get_hotspot_ip()
    interfaces.append(primary_ip)
    
    # Common Windows hotspot IPs
    common_ips = ['192.168.137.1', '192.168.173.1', '192.168.43.1']
    for ip in common_ips:
        if ip not in interfaces:
            interfaces.append(ip)
    
    return interfaces

def debug_database_state():
    """Debug function to check database state"""
    import os
    import sqlite3
    
    print("\n=== DATABASE DEBUG INFO ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database file exists: {os.path.exists('attendance.db')}")
    
    if os.path.exists('attendance.db'):
        print(f"Database file size: {os.path.getsize('attendance.db')} bytes")
        try:
            conn = sqlite3.connect('attendance.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"Tables in database: {[table[0] for table in tables]}")
            conn.close()
        except Exception as e:
            print(f"Error reading database: {e}")
    print("=========================\n")

def init_db():
    """Initialize SQLite database with required tables"""
    try:
        debug_database_state()  # Add this line
        
        print("Attempting to initialize database...")
        
        # Check if database file exists
        if os.path.exists('attendance.db'):
            print("✓ Database file exists")
        else:
            print("⚠ Database file doesn't exist, will be created")
        
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        print("✓ Connected to database")
        
        # Enable foreign keys and WAL mode for better reliability
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute('PRAGMA journal_mode = WAL')
        
        # Create tables with detailed logging
        print("Creating active_tokens table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                timestamp REAL NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                opened BOOLEAN DEFAULT FALSE,
                device_signature TEXT,
                fingerprint_hash TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        print("✓ active_tokens table created")
        
        print("Creating attendances table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                fingerprint_hash TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                year TEXT NOT NULL,
                device_info TEXT
            )
        ''')
        print("✓ attendances table created")
        
        print("Creating denied_attempts table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS denied_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                fingerprint_hash TEXT,
                timestamp REAL NOT NULL,
                created_at TEXT NOT NULL,
                reason TEXT NOT NULL,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                year TEXT NOT NULL,
                device_info TEXT
            )
        ''')
        print("✓ denied_attempts table created")
        
        print("Creating device_fingerprints table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint_hash TEXT UNIQUE NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                device_info TEXT
            )
        ''')
        print("✓ device_fingerprints table created")
        
        print("Creating settings table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id TEXT PRIMARY KEY,
                max_uses_per_device INTEGER DEFAULT 1,
                time_window_minutes INTEGER DEFAULT 1440,
                enable_fingerprint_blocking BOOLEAN DEFAULT TRUE
            )
        ''')
        print("✓ settings table created")
        
        # Insert default settings if not exists
        print("Checking for default settings...")
        cursor.execute('SELECT * FROM settings WHERE id = ?', ('config',))
        if not cursor.fetchone():
            print("Inserting default settings...")
            cursor.execute('''
                INSERT INTO settings (id, max_uses_per_device, time_window_minutes, enable_fingerprint_blocking)
                VALUES (?, ?, ?, ?)
            ''', ('config', 1, 1440, True))
            print("✓ Default settings inserted")
        else:
            print("✓ Default settings already exist")
        
        # Verify tables were created
        print("Verifying table creation...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✓ Tables in database: {[table[0] for table in tables]}")
        
        conn.commit()
        print("✓ Database changes committed")
        conn.close()
        print("✓ Database initialization completed successfully!")
        
        debug_database_state()  # Add this line
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
            conn.close()

# Also add better error handling to get_db_connection
def get_db_connection():
    """Get database connection with better error handling"""
    try:
        if not os.path.exists('attendance.db'):
            print("⚠ Database file missing, reinitializing...")
            init_db()
        
        conn = sqlite3.connect('attendance.db')
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        
        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = ['active_tokens', 'attendances', 'denied_attempts', 'device_fingerprints', 'settings']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠ Missing tables: {missing_tables}, reinitializing database...")
            conn.close()
            init_db()
            conn = sqlite3.connect('attendance.db')
            conn.row_factory = sqlite3.Row
        
        return conn
    except Exception as e:
        print(f"Error getting database connection: {e}")
        raise

if __name__ == '__main__':
    print("Starting Flask Attendance System with FingerprintJS")
    print("=" * 50)
    
    init_db()
    migrate_database()
    
    # Get network information
    interfaces = get_all_network_interfaces()
    primary_ip = interfaces[0]
    
    print(f"Detected Primary IP: {primary_ip}")
    print("\nTry these URLs from your phone:")
    for ip in interfaces:
        print(f"  → http://{ip}:5000")
    
    print(f"\nIf none work, try these troubleshooting steps:")
    print("1. Disable Windows Firewall temporarily")
    print("2. Check if hotspot is actually running")
    print("3. Try phone → laptop hotspot instead")
    print("4. Use 'ipconfig' to find the correct hotspot IP")
    
    print(f"\nStarting server on all interfaces...")
    
    try:
        # Try to run on all interfaces
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # Prevents issues with network detection
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Try running as administrator or check firewall settings")