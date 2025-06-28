import hashlib
import re
import json

def extract_device_signature(user_agent):
    """Extract basic device signature from User-Agent"""
    ua = user_agent.lower()
    device_info = {
        'type': 'desktop',
        'os': 'unknown',
        'browser': 'unknown',
        'brand': 'unknown',
        'model': 'unknown'
    }
    
    # Android device detection with brand/model extraction
    if 'android' in ua:
        device_info['type'] = 'mobile'
        device_info['os'] = 'android'
        
        # Extract brand and model for Android devices
        android_patterns = [
            (r'(oppo|realme|vivo|xiaomi|samsung|huawei|oneplus|lg|sony|motorola|nokia)\s+([a-zA-Z0-9\-_\s]+)', 'brand_model'),
            (r'(sm-[a-zA-Z0-9]+)', 'samsung_model'),
            (r'(cph[0-9]+)', 'oppo_model'),
            (r'(rmx[0-9]+)', 'realme_model'),
            (r'(mi\s+[a-zA-Z0-9\s]+)', 'xiaomi_model')
        ]
        
        for pattern, device_type in android_patterns:
            match = re.search(pattern, ua)
            if match:
                if device_type == 'brand_model':
                    device_info['brand'] = match.group(1).lower()
                    device_info['model'] = match.group(2).strip()
                else:
                    device_info['model'] = match.group(1)
                break
                
    elif 'iphone' in ua:
        device_info['type'] = 'mobile'
        device_info['os'] = 'ios'
        device_info['brand'] = 'apple'
        device_info['model'] = 'iphone'
        
    elif 'ipad' in ua:
        device_info['type'] = 'tablet'
        device_info['os'] = 'ios'
        device_info['brand'] = 'apple'
        device_info['model'] = 'ipad'
        
    else:
        # Desktop OS detection
        if 'windows' in ua:
            device_info['os'] = 'windows'
        elif 'mac' in ua:
            device_info['os'] = 'macos'
        elif 'linux' in ua:
            device_info['os'] = 'linux'
    
    # Browser detection 
    browser_patterns = {
        'chrome': r'chrome/(\d+)',
        'firefox': r'firefox/(\d+)',
        'safari': r'safari/(\d+)',
        'edge': r'edge/(\d+)',
        'opera': r'opera/(\d+)',
    }
    
    for browser, pattern in browser_patterns.items():
        match = re.search(pattern, ua)
        if match:
            device_info['browser'] = f"{browser}_{match.group(1)}"
            break
    
    return device_info

def generate_comprehensive_fingerprint(request_data):
    """Generate comprehensive device fingerprint, including visitor_id if present"""
    device_sig = extract_device_signature(request_data.get('user_agent', ''))
    
    fingerprint_data = {
        'visitor_id': request_data.get('visitor_id', ''),  # Add visitor_id from FingerprintJS
        'device_signature': device_sig,
        'screen_resolution': request_data.get('screen_resolution', ''),
        'timezone': request_data.get('timezone', ''),
        'language': request_data.get('language', ''),
        'platform': request_data.get('platform', ''),
        'color_depth': request_data.get('color_depth', ''),
        'pixel_ratio': request_data.get('pixel_ratio', ''),
        'touch_support': request_data.get('touch_support', False),
        'timestamp': request_data.get('timestamp', ''),
        'available_fonts': request_data.get('available_fonts', ''),
        'canvas_fingerprint': request_data.get('canvas_fingerprint', ''),
        'webgl_fingerprint': request_data.get('webgl_fingerprint', ''),
        'audio_fingerprint': request_data.get('audio_fingerprint', ''),
        'battery_level': request_data.get('battery_level', ''),
        'memory_info': request_data.get('memory_info', ''),
        'connection_type': request_data.get('connection_type', ''),
        'installed_plugins': request_data.get('installed_plugins', ''),
        'do_not_track': request_data.get('do_not_track', ''),
        'cpu_cores': request_data.get('cpu_cores', ''),
        'max_touch_points': request_data.get('max_touch_points', ''),
        'detailed_hardware': request_data.get('detailed_hardware', ''),
        'advanced_canvas': request_data.get('advanced_canvas', ''),
        'timing_fingerprint': request_data.get('timing_fingerprint', ''),
        'storage_fingerprint': request_data.get('storage_fingerprint', ''),
        'virtual_environment': request_data.get('virtual_environment', False),
        'device_consistency': request_data.get('device_consistency', [])
    }
    
    return fingerprint_data


def get_canonical_device_id(request_data):
    """
    Return the canonical device ID for this request: prefer visitor_id, fallback to hash.
    """
    visitor_id = request_data.get('visitor_id')
    if visitor_id:
        return visitor_id
    return create_fingerprint_hash(request_data)


def create_fingerprint_hash(request_data):
    """Create a unique hash for device fingerprinting (used if visitor_id is not present)"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    
    # Extract device signature for enhanced processing
    device_sig = fingerprint['device_signature']
    
    # Enhanced fingerprint components for better device distinction
    primary_components = [
        str(fingerprint['device_signature']),
        fingerprint['screen_resolution'],
        fingerprint['timezone'],
        fingerprint['language'],
        fingerprint['platform'],
        fingerprint['color_depth'],
        str(fingerprint['pixel_ratio']),
        str(fingerprint['touch_support']),
        fingerprint['canvas_fingerprint'][:100] if fingerprint['canvas_fingerprint'] else '',
        fingerprint['webgl_fingerprint'],
        fingerprint['audio_fingerprint'][:50] if fingerprint['audio_fingerprint'] else '',
        fingerprint['memory_info'],
        str(fingerprint['cpu_cores']),
        str(fingerprint['max_touch_points']),
        fingerprint['available_fonts'][:100] if fingerprint['available_fonts'] else '',
        fingerprint['detailed_hardware'][:200] if fingerprint['detailed_hardware'] else '',
        fingerprint['advanced_canvas'][:100] if fingerprint['advanced_canvas'] else '',
        fingerprint['timing_fingerprint'],
        fingerprint['storage_fingerprint']
    ]
    
    # Enhanced mobile device differentiation
    if device_sig['type'] in ['mobile', 'tablet']:
        mobile_components = [
            device_sig.get('brand', ''),
            device_sig.get('model', ''),
            fingerprint.get('timing_fingerprint', ''),
            str(fingerprint.get('virtual_environment', False)),
            json.dumps(fingerprint.get('device_consistency', []))
        ]
        primary_components.extend(mobile_components)
    
    # Create composite fingerprint string
    fingerprint_string = '|'.join(str(comp) for comp in primary_components if comp)
    
    # Generate SHA256 hash
    hash_object = hashlib.sha256(fingerprint_string.encode('utf-8'))
    return hash_object.hexdigest()

def get_device_uniqueness_score(request_data):
    """Calculate device uniqueness score (0-100)"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    score = 0
    
    # Base scoring criteria
    scoring_criteria = [
        ('canvas_fingerprint', 20),
        ('webgl_fingerprint', 15),
        ('audio_fingerprint', 10),
        ('available_fonts', 10),
        ('detailed_hardware', 15),
        ('timing_fingerprint', 10),
        ('device_signature', 10),
        ('advanced_canvas', 10)
    ]
    
    for field, points in scoring_criteria:
        value = fingerprint.get(field, '')
        if value and value not in ['error', 'unknown', 'not_supported']:
            score += points
    
    # Bonus for mobile device specificity
    device_sig = fingerprint['device_signature']
    if device_sig['type'] in ['mobile', 'tablet']:
        if device_sig.get('brand') != 'unknown':
            score += 5
        if device_sig.get('model') != 'unknown':
            score += 5
    
    return min(score, 100)