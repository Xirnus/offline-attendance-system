"""
Device Fingerprinting Service Module for Offline Attendance System

This module provides comprehensive device fingerprinting capabilities for the SQLite-based attendance tracking system. It generates unique device signatures to prevent duplicate check-ins and ensure attendance integrity through advanced browser fingerprinting techniques.

Main Features:
- Device Signature Extraction: Parse User-Agent strings for device/OS/browser info
- Comprehensive Fingerprinting: Collect multiple device characteristics for uniqueness
- Hash Generation: Create unique, consistent hashes for device identification
- Uniqueness Scoring: Calculate how distinctive a device fingerprint is
- Cross-Platform Support: Handle mobile, tablet, and desktop devices

Key Functions:
- extract_device_signature(): Parse User-Agent for basic device information
- generate_comprehensive_fingerprint(): Collect extensive device characteristics
- create_fingerprint_hash(): Generate unique SHA256 hash from device data
- get_device_uniqueness_score(): Calculate fingerprint uniqueness (0-100 scale)

Fingerprinting Components:
- Device Type: Mobile, tablet, desktop classification
- Operating System: Windows, macOS, Linux, iOS, Android detection
- Browser Information: Chrome, Firefox, Safari, Edge identification
- Screen Properties: Resolution, color depth, pixel ratio
- System Settings: Timezone, language, platform details
- Hardware Features: Touch support, CPU cores, memory info
- Advanced Fingerprints: Canvas, WebGL, audio fingerprinting

Security Features:
- SHA256 hashing for consistent device identification
- Multiple fingerprinting layers for enhanced uniqueness
- Graceful degradation when fingerprinting data is unavailable
- Privacy-conscious data collection (no personal information)

Used by: API routes, attendance validation, security checks
Dependencies: Standard library (hashlib, re), request data parsing
"""

import re
import hashlib

def extract_device_signature(user_agent):
    """Extract basic device signature from User-Agent"""
    ua = user_agent.lower()
    device_info = {
        'type': 'desktop',
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
    
    # iPhone detection 
    elif 'iphone' in ua:
        device_info['type'] = 'mobile'
        device_info['os'] = 'ios'
        
        # Extract iOS version
        ios_version = re.search(r'os (\d+(?:_\d+)*)', ua)
        if ios_version:
            device_info['os_version'] = ios_version.group(1).replace('_', '.')
    
    # iPad detection
    elif 'ipad' in ua:
        device_info['type'] = 'tablet'
        device_info['os'] = 'ios'
        
        ios_version = re.search(r'os (\d+(?:_\d+)*)', ua)
        if ios_version:
            device_info['os_version'] = ios_version.group(1).replace('_', '.')
    
    # Desktop/Laptop detection
    else:
        if 'windows' in ua:
            device_info['os'] = 'windows'
        elif 'mac' in ua and 'iphone' not in ua and 'ipad' not in ua:
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
            device_info['browser'] = browser
            device_info['browser_version'] = match.group(1)
            break
    
    return device_info

def generate_comprehensive_fingerprint(request_data):
    """Generate comprehensive device fingerprint"""
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

def create_fingerprint_hash(request_data):
    """Create a unique hash for device fingerprinting"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    
    # Primary fingerprint components 
    primary_components = [
        str(fingerprint['device_signature']),
        fingerprint['screen_resolution'],
        fingerprint['timezone'],
        fingerprint['language'],
        fingerprint['platform'],
        fingerprint['color_depth'],
        str(fingerprint['pixel_ratio']),
        str(fingerprint['touch_support'])
    ]
    
    # Combine components
    fingerprint_string = '|'.join([str(comp) for comp in primary_components if comp])
    
    # Generate hash
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def get_device_uniqueness_score(request_data):
    """Calculate how unique this device fingerprint is (0-100 scale)"""
    fingerprint = generate_comprehensive_fingerprint(request_data)
    
    uniqueness_factors = {
        'device_signature': 30,
        'screen_resolution': 20,
        'timezone': 15,
        'language': 10,
        'platform': 10,
        'color_depth': 8,
        'pixel_ratio': 7
    }
    
    score = 0
    for component, weight in uniqueness_factors.items():
        if fingerprint.get(component) and str(fingerprint[component]).strip():
            score += weight
    
    return min(score, 100)