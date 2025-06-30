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
    """Generate simplified device fingerprint using only required fields."""
    device_sig = extract_device_signature(request_data.get('user_agent', ''))
    
    fingerprint_data = {
        'visitor_id': request_data.get('visitor_id', ''),  # Add visitor_id from FingerprintJS
        'user_agent': request_data.get('user_agent', ''),
        # screen_size and timezone removed for stability
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
    """Create a unique hash for device fingerprinting using only visitor_id."""
    visitor_id = request_data.get('visitor_id', '')
    # Only use visitor_id for the hash
    hash_object = hashlib.sha256(str(visitor_id).encode('utf-8'))
    return hash_object.hexdigest()