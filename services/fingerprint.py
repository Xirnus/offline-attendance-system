import re
import json
import hashlib
import time

def extract_device_signature(user_agent):
    """Extract detailed device signature from User-Agent"""
    ua = user_agent.lower()
    device_info = {
        'type': 'desktop',
        'brand': 'unknown',
        'model': 'unknown',
        'os': 'unknown',
        'browser': 'unknown'
    }
    
    # Android device detection
    if 'android' in ua:
        device_info['type'] = 'mobile'
        device_info['os'] = 'android'
        
        # Extract Android version
        android_version = re.search(r'android (\d+(?:\.\d+)*)', ua)
        if android_version:
            device_info['os_version'] = android_version.group(1)
        
        # Improved Android device detection with more comprehensive patterns
        android_patterns = {
            'samsung': [
                r'samsung[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(sm-[a-z]\d+[a-z]*)',
                r'(galaxy[\s\-]*[a-z]*\d*[a-z]*)',
                r'gt-([a-z]\d+)',
                r'sch-([a-z]\d+)'
            ],
            'huawei': [
                r'huawei[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(p\d+[a-z]*)',
                r'(mate\d+[a-z]*)',
                r'(nova\d+[a-z]*)',
                r'(honor\d+[a-z]*)',
                r'(y\d+[a-z]*)',
                r'([a-z]{2,3}-[a-z]\d+[a-z]*)'
            ],
            'xiaomi': [
                r'xiaomi[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(mi[\s\-]*\d+[a-z]*)',
                r'(redmi[\s\-]*[\w\d]*)',
                r'(poco[\s\-]*[\w\d]*)',
                r'(mix[\s\-]*\d*[a-z]*)',
                r'(note[\s\-]*\d*[a-z]*)'
            ],
            'oppo': [
                r'oppo[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(cph\d+)',
                r'(find[\s\-]*[a-z]*\d*)',
                r'(reno\d*[a-z]*)',
                r'(a\d+[a-z]*)'
            ],
            'vivo': [
                r'vivo[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(v\d+[a-z]*)',
                r'(y\d+[a-z]*)',
                r'(x\d+[a-z]*)',
                r'(s\d+[a-z]*)'
            ],
            'oneplus': [
                r'oneplus[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(one[\s\-]*plus[\s\-]*\d*[a-z]*)',
                r'(hd\d+[a-z]*)',
                r'(ac\d+[a-z]*)',
                r'(gm\d+[a-z]*)'
            ],
            'lg': [
                r'lg[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'lg-([a-z]\d+[a-z]*)',
                r'(nexus[\s\-]*\d*[a-z]*)',
                r'(g\d+[a-z]*)'
            ],
            'sony': [
                r'sony[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(xperia[\s\-]*[\w\d]*)',
                r'(c\d+[a-z]*)',
                r'(d\d+[a-z]*)',
                r'(e\d+[a-z]*)'
            ],
            'motorola': [
                r'motorola[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(moto[\s\-]*[\w\d]*)',
                r'(xt\d+[a-z]*)',
                r'(droid[\s\-]*[\w\d]*)'
            ],
            'htc': [
                r'htc[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(one[\s\-]*[\w\d]*)',
                r'(desire[\s\-]*[\w\d]*)',
                r'(sensation[\s\-]*[\w\d]*)'
            ],
            'google': [
                r'(pixel[\s\-]*\d*[a-z]*)',
                r'(nexus[\s\-]*\d*[a-z]*)'
            ],
            'realme': [
                r'realme[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(rmx\d+[a-z]*)'
            ],
            'tcl': [
                r'tcl[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(t\d+[a-z]*)'
            ],
            'asus': [
                r'asus[;\s/\-]*([\w\-\s]+?)(?:[;\s/]|$)',
                r'(zenfone[\s\-]*[\w\d]*)',
                r'(rog[\s\-]*[\w\d]*)'
            ]
        }
        
        # Try to detect brand and model
        brand_found = False
        for brand, patterns in android_patterns.items():
            # Check if brand name appears in user agent (case insensitive)
            if brand in ua or any(re.search(pattern, ua, re.IGNORECASE) for pattern in patterns):
                device_info['brand'] = brand
                brand_found = True
                
                # Try to extract model using patterns
                for pattern in patterns:
                    match = re.search(pattern, ua, re.IGNORECASE)
                    if match:
                        model = match.group(1).strip()
                        # Clean up the model string
                        model = re.sub(r'[;\s/]+$', '', model)  # Remove trailing separators
                        model = re.sub(r'^[;\s/]+', '', model)  # Remove leading separators
                        if model and len(model) > 1:
                            device_info['model'] = model
                            break
                break
        
        # If no specific brand found, try generic Android model detection
        if not brand_found:
            # Look for common Android model patterns
            generic_patterns = [
                r';\s*([a-z]{2,4}-[a-z]\d+[a-z]*)',  # Generic model codes like SM-G975F
                r';\s*([\w\-]{3,15})\s*build',       # Model before "Build"
                r'android[^;)]*;\s*([^;)]+)',        # Anything after Android version
            ]
            
            for pattern in generic_patterns:
                match = re.search(pattern, ua, re.IGNORECASE)
                if match:
                    model = match.group(1).strip()
                    # Filter out common non-model strings
                    if model and len(model) > 2 and not any(x in model.lower() for x in ['mobile', 'webkit', 'build', 'version']):
                        device_info['model'] = model
                        # Try to guess brand from model
                        if model.lower().startswith('sm-'):
                            device_info['brand'] = 'samsung'
                        elif model.lower().startswith('pixel'):
                            device_info['brand'] = 'google'
                        break
    
    # iPhone detection 
    elif 'iphone' in ua:
        device_info['type'] = 'mobile'
        device_info['brand'] = 'apple'
        device_info['model'] = 'iphone'
        device_info['os'] = 'ios'
        
        # Extract iOS version
        ios_version = re.search(r'os (\d+(?:_\d+)*)', ua)
        if ios_version:
            device_info['os_version'] = ios_version.group(1).replace('_', '.')
    
    # iPad detection
    elif 'ipad' in ua:
        device_info['type'] = 'tablet'
        device_info['brand'] = 'apple'
        device_info['model'] = 'ipad'
        device_info['os'] = 'ios'
        
        ios_version = re.search(r'os (\d+(?:_\d+)*)', ua)
        if ios_version:
            device_info['os_version'] = ios_version.group(1).replace('_', '.')
    
    # Desktop/Laptop detection
    else:
        if 'windows' in ua:
            device_info['os'] = 'windows'
        elif 'mac' in ua and 'iphone' not in ua and 'ipad' not in ua:
            device_info['os'] = 'macOS'
            device_info['brand'] = 'apple'
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
            device_info['browser'] = browser
            device_info['browser_version'] = match.group(1)
            break
    
    return device_info

def generate_comprehensive_fingerprint(request_data):
    """Generate comprehensive device fingerprint with enhanced uniqueness"""
    device_sig = extract_device_signature(request_data.get('user_agent', ''))
    
    fingerprint_data = {
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
        'max_touch_points': request_data.get('max_touch_points', '')
    }
    
    return fingerprint_data

def create_enhanced_fingerprint_hash(request_data):
    """Create a highly unique hash for device fingerprinting"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    
    # Primary fingerprint components 
    primary_components = [
        str(fingerprint['device_signature']),
        fingerprint['screen_resolution'],
        fingerprint['timezone'],
        fingerprint['language'],
        fingerprint['platform'],
        fingerprint['color_depth'],
        str(fingerprint['pixel_ratio'])
    ]
    
    # Secondary components
    secondary_components = [
        fingerprint['available_fonts'],
        fingerprint['canvas_fingerprint'],
        fingerprint['webgl_fingerprint'],
        str(fingerprint['touch_support']),
        str(fingerprint['cpu_cores']),
        str(fingerprint['max_touch_points']),
        fingerprint['connection_type']
    ]
    
    # Combine all components
    all_components = primary_components + secondary_components
    fingerprint_string = '|'.join([str(comp) for comp in all_components if comp])
    
    # Generate multiple hashes for different purposes
    sha256_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    # Add timestamp salt for additional security
    timestamp_salt = str(int(time.time() // 3600))  # Changes every hour
    salted_string = fingerprint_string + timestamp_salt
    salted_hash = hashlib.sha256(salted_string.encode()).hexdigest()
    
    return {
        'primary_hash': sha256_hash,
        'salted_hash': salted_hash,
        'fingerprint_components': fingerprint
    }

def generate_device_info(request_data):
    """Generate device information object (backward compatibility)"""
    comprehensive = generate_comprehensive_fingerprint(request_data)
    
    return {
        'user_agent': request_data.get('user_agent', ''),
        'device_signature': comprehensive['device_signature'],
        'screen_resolution': request_data.get('screen_resolution', ''),
        'timezone': request_data.get('timezone', ''),
        'language': request_data.get('language', ''),
        'platform': request_data.get('platform', ''),
        'timestamp': request_data.get('timestamp', ''),
        'color_depth': request_data.get('color_depth', ''),
        'pixel_ratio': request_data.get('pixel_ratio', ''),
        'touch_support': request_data.get('touch_support', False),
        'canvas_fingerprint': request_data.get('canvas_fingerprint', ''),
        'webgl_fingerprint': request_data.get('webgl_fingerprint', ''),
        'available_fonts': request_data.get('available_fonts', ''),
        'cpu_cores': request_data.get('cpu_cores', ''),
        'memory_info': request_data.get('memory_info', '')
    }

def create_fingerprint_hash(request_data):
    """Create a unique hash for device fingerprinting (backward compatibility)"""
    enhanced = create_enhanced_fingerprint_hash(request_data)
    return enhanced['primary_hash']

def get_device_uniqueness_score(request_data):
    """Calculate how unique this device fingerprint is (0-100 scale)"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    
    uniqueness_factors = {
        'device_signature': 30,  # Brand/model/OS combination
        'screen_resolution': 15,  # Screen resolution
        'canvas_fingerprint': 20,  # Canvas rendering fingerprint
        'webgl_fingerprint': 15,  # WebGL fingerprint
        'available_fonts': 10,    # Font list
        'timezone': 5,            # Timezone
        'language': 3,            # Language setting
        'cpu_cores': 2            # CPU information
    }
    
    score = 0
    for component, weight in uniqueness_factors.items():
        if fingerprint.get(component) and str(fingerprint[component]).strip():
            score += weight
    
    return min(score, 100)
