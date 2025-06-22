// main.js - External JavaScript file for attendance check-in system
// Bug: landing page wont load properly if index.html is seperated files

let fingerprintHash = '';
let deviceInfo = {};

// Enhanced device signature extraction
function extractDeviceSignature(userAgent) {
    const ua = userAgent.toLowerCase();
    const deviceInfo = {
        type: 'desktop',
        brand: 'unknown',
        model: 'unknown',
        os: 'unknown',
        browser: 'unknown'
    };
    
    // Android device detection
    if (ua.includes('android')) {
        deviceInfo.type = 'mobile';
        deviceInfo.os = 'android';
        
        // Extract Android version
        const androidVersion = ua.match(/android (\d+(?:\.\d+)*)/);
        if (androidVersion) {
            deviceInfo.os_version = androidVersion[1];
        }
        
        // Extract device model for popular brands
        const androidPatterns = {
            'samsung': [
                /samsung[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
                /sm-(\w+)/,
                /galaxy[\s\-]+([\w\s]+?)(?:\s|;|$)/
            ],
            'huawei': [
                /huawei[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
                /(p\d+|mate\d+|nova\d+|honor\d+)/,
            ],
            'xiaomi': [
                /xiaomi[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
                /(mi\s?\d+|redmi[\s\w]*|poco[\s\w]*)/,
            ],
            'oppo': [
                /oppo[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
            ],
            'vivo': [
                /vivo[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
            ],
            'oneplus': [
                /oneplus[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
            ],
            'lg': [
                /lg[;\s\-]+([\w\-\s]+?)(?:\s|;|$)/,
            ],
            'sony': [
                /sony[;\s]+([\w\-\s]+?)(?:\s|;|$)/,
            ]
        };
        
        for (const [brand, patterns] of Object.entries(androidPatterns)) {
            if (ua.includes(brand)) {
                deviceInfo.brand = brand;
                for (const pattern of patterns) {
                    const match = ua.match(pattern);
                    if (match) {
                        deviceInfo.model = match[1].trim();
                        break;
                    }
                }
                break;
            }
        }
    }
    
    // iPhone detection
    else if (ua.includes('iphone')) {
        deviceInfo.type = 'mobile';
        deviceInfo.brand = 'apple';
        deviceInfo.model = 'iphone';
        deviceInfo.os = 'ios';
        
        // Extract iOS version
        const iosVersion = ua.match(/os (\d+(?:_\d+)*)/);
        if (iosVersion) {
            deviceInfo.os_version = iosVersion[1].replace(/_/g, '.');
        }
        
        // Try to determine iPhone model
        const iPhoneModels = {
            'iphone15': /iphone15/,
            'iphone14': /iphone14/,
            'iphone13': /iphone13/,
            'iphone12': /iphone12/,
            'iphone11': /iphone11/,
            'iphonex': /iphonex/,
        };
        
        for (const [model, pattern] of Object.entries(iPhoneModels)) {
            if (pattern.test(ua)) {
                deviceInfo.model = model;
                break;
            }
        }
    }
    
    // iPad detection
    else if (ua.includes('ipad')) {
        deviceInfo.type = 'tablet';
        deviceInfo.brand = 'apple';
        deviceInfo.model = 'ipad';
        deviceInfo.os = 'ios';
        
        const iosVersion = ua.match(/os (\d+(?:_\d+)*)/);
        if (iosVersion) {
            deviceInfo.os_version = iosVersion[1].replace(/_/g, '.');
        }
    }
    
    // Desktop detection
    else {
        if (ua.includes('windows')) {
            deviceInfo.os = 'windows';
        } else if (ua.includes('mac') && !ua.includes('iphone') && !ua.includes('ipad')) {
            deviceInfo.os = 'macOS';
            deviceInfo.brand = 'apple';
        } else if (ua.includes('linux')) {
            deviceInfo.os = 'linux';
        }
    }
    
    // Browser detection
    const browserPatterns = {
        'chrome': /chrome\/(\d+)/,
        'firefox': /firefox\/(\d+)/,
        'safari': /safari\/(\d+)/,
        'edge': /edge\/(\d+)/,
        'opera': /opera\/(\d+)/,
    };
    
    for (const [browser, pattern] of Object.entries(browserPatterns)) {
        const match = ua.match(pattern);
        if (match) {
            deviceInfo.browser = browser;
            deviceInfo.browser_version = match[1];
            break;
        }
    }
    
    return deviceInfo;
}

// Enhanced fingerprinting function
function generateEnhancedFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Canvas fingerprinting
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('Device fingerprint', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Device fingerprint', 4, 17);
    
    // WebGL fingerprinting
    let webglInfo = 'not_supported';
    try {
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (gl) {
            webglInfo = [
                gl.getParameter(gl.VERSION),
                gl.getParameter(gl.VENDOR),
                gl.getParameter(gl.RENDERER)
            ].join('|');
        }
    } catch (e) {
        webglInfo = 'webgl_error';
    }
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height + 'x' + screen.colorDepth,
        new Date().getTimezoneOffset(),
        navigator.platform,
        navigator.cookieEnabled,
        typeof(navigator.doNotTrack),
        window.devicePixelRatio || 1,
        'ontouchstart' in window,
        canvas.toDataURL(),
        webglInfo,
        Intl.DateTimeFormat().resolvedOptions().timeZone
    ].join('|');
    
    // Enhanced hash function
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

// Fallback fingerprinting function (keeping original for compatibility)
window.generateFallbackFingerprint = function() {
    return generateEnhancedFingerprint();
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeFingerprinting();
    setupForm();
});

async function initializeFingerprinting() {
    try {
        showLoading('Generating device fingerprint...');
        
        // Extract detailed device signature
        const deviceSignature = extractDeviceSignature(navigator.userAgent);
        
        // Collect enhanced device information
        deviceInfo = {
            userAgent: navigator.userAgent,
            device_signature: deviceSignature,
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen_resolution: `${screen.width}x${screen.height}`,
            color_depth: screen.colorDepth,
            pixel_ratio: window.devicePixelRatio || 1,
            touch_support: 'ontouchstart' in window,
            timestamp: new Date().toISOString()
        };

        // Try FingerprintJS Pro first (if API key is configured)
        if (window.FingerprintJS && window.FingerprintJS.load) {
            try {
                const fp = await FingerprintJS.load();
                const result = await fp.get();
                fingerprintHash = result.visitorId;
            } catch (fpError) {
                console.log('FingerprintJS Pro failed, using enhanced fallback:', fpError);
                fingerprintHash = generateEnhancedFingerprint();
            }
        } else {
            // Use enhanced fingerprinting
            fingerprintHash = generateEnhancedFingerprint();
        }

        // Update UI
        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        document.getElementById('device-info').textContent = getEnhancedDeviceDescription();
        
        // Enable form
        enableForm();
        hideLoading();
        
    } catch (error) {
        console.error('Fingerprinting failed:', error);
        showError('Device fingerprinting failed. Using basic security mode.');
        
        // Fallback: use a simple hash based on user agent and timestamp
        fingerprintHash = btoa(navigator.userAgent + Date.now()).substring(0, 16);
        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        document.getElementById('device-info').textContent = getEnhancedDeviceDescription();
        
        enableForm();
        hideLoading();
    }
}

function getEnhancedDeviceDescription() {
    if (deviceInfo.device_signature) {
        const device = deviceInfo.device_signature;
        
        let description = '';
        
        // Build a readable device description
        if (device.brand && device.brand !== 'unknown') {
            description += device.brand.charAt(0).toUpperCase() + device.brand.slice(1);
        }
        
        if (device.model && device.model !== 'unknown') {
            description += ` ${device.model}`;
        }
        
        if (device.os && device.os !== 'unknown') {
            description += ` (${device.os}`;
            if (device.os_version) {
                description += ` ${device.os_version}`;
            }
            description += ')';
        }
        
        if (description) {
            return description;
        }
    }
    
    // Fallback to original method
    return getDeviceDescription();
}

function getDeviceDescription() {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes('android')) return 'Android Device';
    if (ua.includes('iphone')) return 'iPhone';
    if (ua.includes('ipad')) return 'iPad';
    if (ua.includes('mobile')) return 'Mobile Device';
    return 'Desktop';
}

function setupForm() {
    const form = document.getElementById('checkin-form');
    form.addEventListener('submit', handleSubmit);
}

async function handleSubmit(event) {
    event.preventDefault();
    
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    
    submitBtn.disabled = true;
    submitText.textContent = 'Checking in...';
    hideMessages();
    
    try {
        const formData = new FormData(event.target);
        const data = {
            token: formData.get('token'),
            student_id: formData.get('student_id'), // Make sure this matches your form field
            fingerprint_hash: fingerprintHash,
            device_info: JSON.stringify(deviceInfo)
        };
        
        const response = await fetch('/checkin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showSuccess(result.message || 'Check-in successful!');
            document.getElementById('student_id').value = ''; // Clear form
        } else {
            showError(result.message || 'Check-in failed');
        }
        
    } catch (error) {
        console.error('Check-in error:', error);
        showError('Check-in failed. Please try again.');
    } finally {
        // Re-enable form
        submitBtn.disabled = false;
        submitText.textContent = 'Check In';
        submitBtn.className = 'w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg font-medium transition-colors';
    }
}

function enableForm() {
    const submitBtn = document.getElementById('submit-btn');
    const submitText = document.getElementById('submit-text');
    
    submitBtn.disabled = false;
    submitText.textContent = 'Check In';
    submitBtn.className = 'w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-6 rounded-lg font-medium transition-colors';
}

function showLoading(message) {
    const loadingEl = document.getElementById('loading-message');
    loadingEl.querySelector('span').textContent = message;
    loadingEl.classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-message').classList.add('hidden');
}

function showError(message) {
    document.getElementById('error-text').textContent = message;
    document.getElementById('error-message').classList.remove('hidden');
}

function showSuccess(message) {
    document.getElementById('success-message').querySelector('span').textContent = message;
    document.getElementById('success-message').classList.remove('hidden');
}

function hideMessages() {
    document.getElementById('error-message').classList.add('hidden');
    document.getElementById('success-message').classList.add('hidden');
}

// Handle page visibility changes (prevent issues when app is backgrounded)
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
        // Page became visible again - could refresh fingerprint if needed
        console.log('Page visible again');
    }
});

// Debug function to show detailed device info 
window.showDeviceDebugInfo = function() {
    console.log('Device Info:', deviceInfo);
    console.log('Fingerprint Hash:', fingerprintHash);
    console.log('Device Description:', getEnhancedDeviceDescription());
};


// Add this to your frontend form submission
function collectDeviceData() {
  return {
    user_agent: navigator.userAgent,
    screen_resolution: `${screen.width}x${screen.height}`,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language,
    platform: navigator.platform,
    color_depth: screen.colorDepth.toString(),
    pixel_ratio: window.devicePixelRatio.toString(),
    touch_support: 'ontouchstart' in window
  };
}

function submitAttendance() {
  const formData = {
    token: document.getElementById('token').value,
    name: document.getElementById('name').value,
    course: document.getElementById('course').value,
    year: document.getElementById('year').value,
    timestamp: Date.now() / 1000,
    ...collectDeviceData() 
  };
  
  fetch('/checkin', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(formData)
  })
  .then(response => response.json())
  .then(data => {
    // Handle response
    console.log(data);
  });
}