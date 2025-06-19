from flask import Blueprint, request, render_template, send_file, jsonify
import json
import time
from datetime import datetime

# Safe imports with error handling
try:
    from database.operations import (
        get_settings, update_settings, create_token, get_token, 
        update_token, record_attendance, record_denied_attempt, get_all_data
    )
    print("✓ Database operations imported successfully")
except ImportError as e:
    print(f"✗ Database operations import failed: {e}")
    # Create dummy functions for testing
    def get_all_data(table_name):
        return [{"test": "data", "table": table_name}]
    def get_settings():
        return {"test": "settings"}
    def update_settings(data):
        pass
    def create_token(token):
        pass
    def get_token(token):
        return {"test": "token", "opened": False, "used": False}
    def update_token(token, **kwargs):
        pass
    def record_attendance(data):
        pass
    def record_denied_attempt(data, reason):
        pass

try:
    from services.attendance import is_fingerprint_allowed, store_device_fingerprint, validate_attendance_data
    print("✓ Services.attendance imported successfully")
except ImportError as e:
    print(f"✗ Services.attendance import failed: {e}")
    # Create dummy functions
    def is_fingerprint_allowed(fingerprint_hash):
        return True, "Allowed"
    def store_device_fingerprint(fingerprint_hash, device_info):
        pass
    def validate_attendance_data(data):
        return True

try:
    from services.token import generate_token, validate_token_access
    print("✓ Services.token imported successfully")
except ImportError as e:
    print(f"✗ Services.token import failed: {e}")
    def generate_token():
        return "test_token_123"
    def validate_token_access(token_data, device_sig):
        return True, "Valid"

try:
    from services.rate_limiting import is_rate_limited, get_client_ip
    print("✓ Services.rate_limiting imported successfully")
except ImportError as e:
    print(f"✗ Services.rate_limiting import failed: {e}")
    def is_rate_limited(ip):
        return False
    def get_client_ip(request):
        return "127.0.0.1"

try:
    from utils.qr_generator import generate_qr_code, build_qr_url
    print("✓ Utils.qr_generator imported successfully")
except ImportError as e:
    print(f"✗ Utils.qr_generator import failed: {e}")
    def generate_qr_code(url):
        return None
    def build_qr_url(request, token):
        return f"http://test.com/{token}"

try:
    from utils.validation import sanitize_input
    print("✓ Utils.validation imported successfully")
except ImportError as e:
    print(f"✗ Utils.validation import failed: {e}")
    def sanitize_input(text):
        return text

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

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
        print(f"QR generation error: {e}")
        return "Error generating QR code", 500

@api_bp.route('/scan/<token>')
def scan(token):
    try:
        token_data = get_token(token)
        
        # Simple device signature extraction
        ua = request.headers.get('User-Agent', '').lower()
        if 'iphone' in ua:
            device_sig = 'iphone'
        elif 'android' in ua:
            device_sig = 'android'
        elif 'ipad' in ua:
            device_sig = 'ipad'
        elif 'mobile' in ua:
            device_sig = 'mobile'
        else:
            device_sig = 'desktop'
        
        valid, message = validate_token_access(token_data, device_sig)
        if not valid:
            return f"<h3>{message}</h3>", 400
        
        # Update token on first open
        if not token_data['opened']:
            update_token(token, opened=True, device_signature=device_sig)
        
        return render_template('index.html', token=token)
    except Exception as e:
        print(f"Scan error: {e}")
        return "Error processing QR code", 500

@api_bp.route('/checkin', methods=['POST'])
def checkin():
    try:
        data = request.json or {}
        
        # Validate required fields
        if not validate_attendance_data(data):
            return jsonify(status='error', message='Missing required fields')
        
        # Sanitize inputs
        for key in ['name', 'course', 'year']:
            if key in data:
                data[key] = sanitize_input(data[key])
        
        token = data.get('token', '')
        fingerprint_hash = data.get('fingerprint_hash', '')
        device_info = json.dumps(data.get('device_info', {}))
        
        # Validate token
        token_data = get_token(token)
        if not token_data:
            record_denied_attempt(data, 'invalid_token')
            return jsonify(status='error', message='Invalid token')
        
        if token_data.get('used'):
            record_denied_attempt(data, 'already_used')
            return jsonify(status='error', message='Token already used')
        
        # Check fingerprint
        allowed, reason = is_fingerprint_allowed(fingerprint_hash)
        if not allowed:
            record_denied_attempt(data, 'fingerprint_blocked')
            return jsonify(status='error', message=reason)
        
        # Record attendance
        update_token(token, used=True, fingerprint_hash=fingerprint_hash)
        data['device_info'] = device_info
        record_attendance(data)
        store_device_fingerprint(fingerprint_hash, device_info)
        
        return jsonify(status='success', message='Attendance recorded successfully')
    
    except Exception as e:
        print(f"Checkin error: {e}")
        return jsonify(status='error', message='Server error'), 500

@api_bp.route('/api/attendances')
def api_attendances():
    print("=== API_ATTENDANCES CALLED ===")
    try:
        attendances = get_all_data('attendances')
        print(f"Got {len(attendances) if attendances else 0} attendances")
        
        # Hide full fingerprint hash for privacy
        for attendance in attendances:
            if 'fingerprint_hash' in attendance and attendance['fingerprint_hash']:
                attendance['fingerprint_hash'] = attendance['fingerprint_hash'][:8] + '...'
        
        return jsonify(attendances)
    except Exception as e:
        print(f"Error getting attendances: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@api_bp.route('/api/denied')
def api_denied():
    print("=== API_DENIED CALLED ===")
    try:
        denied = get_all_data('denied_attempts')
        print(f"Got {len(denied) if denied else 0} denied attempts")
        
        # Hide full fingerprint hash for privacy
        for attempt in denied:
            if 'fingerprint_hash' in attempt and attempt['fingerprint_hash']:
                attempt['fingerprint_hash'] = attempt['fingerprint_hash'][:8] + '...'
        
        return jsonify(denied)
    except Exception as e:
        print(f"Error getting denied attempts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@api_bp.route('/api/device_fingerprints', methods=['GET'])
def api_device_fingerprints():
    print("=== API_DEVICE_FINGERPRINTS CALLED ===")
    print(f"Request method: {request.method}")
    
    try:
        fingerprints = get_all_data('device_fingerprints')
        print(f"Got {len(fingerprints) if fingerprints else 0} device fingerprints")
        
        # Hide full fingerprint hash for privacy
        for fp in fingerprints:
            if 'fingerprint_hash' in fp and fp['fingerprint_hash']:
                fp['fingerprint_hash'] = fp['fingerprint_hash'][:8] + '...'
        
        print("Returning fingerprints data")
        return jsonify(fingerprints)
    except Exception as e:
        print(f"Error getting device fingerprints: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@api_bp.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    print(f"=== API_SETTINGS CALLED ({request.method}) ===")
    try:
        if request.method == 'GET':
            settings = get_settings()
            return jsonify(settings)
        
        data = request.json or {}
        update_settings(data)
        return jsonify(get_settings())
    
    except Exception as e:
        print(f"Settings error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(get_settings())

@api_bp.route('/api/export_data')
def export_data():
    print("=== EXPORT_DATA CALLED ===")
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
        print(f"Export error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})