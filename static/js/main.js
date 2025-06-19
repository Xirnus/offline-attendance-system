// main.js - External JavaScript file for attendance check-in system
// Bug: landing page wont load properly if index.html is seperated files



let fingerprintHash = '';
let deviceInfo = {};

// Fallback fingerprinting function
window.generateFallbackFingerprint = function() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Fingerprint test', 2, 2);
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        navigator.platform,
        navigator.cookieEnabled,
        typeof(navigator.doNotTrack),
        canvas.toDataURL()
    ].join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeFingerprinting();
    setupForm();
});

async function initializeFingerprinting() {
    try {
        showLoading('Generating device fingerprint...');
        
        // Collect device information
        deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            timestamp: new Date().toISOString()
        };

        // Try FingerprintJS Pro first (if API key is configured)
        if (window.FingerprintJS && window.FingerprintJS.load) {
            try {
                const fp = await FingerprintJS.load();
                const result = await fp.get();
                fingerprintHash = result.visitorId;
            } catch (fpError) {
                console.log('FingerprintJS Pro failed, using fallback:', fpError);
                fingerprintHash = window.generateFallbackFingerprint();
            }
        } else {
            // Use fallback fingerprinting
            fingerprintHash = window.generateFallbackFingerprint();
        }

        // Update UI
        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        document.getElementById('device-info').textContent = getDeviceDescription();
        
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
        document.getElementById('device-info').textContent = getDeviceDescription();
        
        enableForm();
        hideLoading();
    }
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
    
    // Disable form
    submitBtn.disabled = true;
    submitText.textContent = 'Checking in...';
    submitBtn.className = 'w-full bg-blue-400 text-white py-3 px-6 rounded-lg font-medium cursor-not-allowed';
    
    hideMessages();
    
    try {
        const formData = new FormData(event.target);
        const data = {
            token: formData.get('token'),
            fingerprint_hash: fingerprintHash,
            name: formData.get('name'),
            course: formData.get('course'),
            year: formData.get('year'),
            device_info: deviceInfo
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
            // Keep form disabled after success
            submitText.textContent = 'Checked In ✓';
            submitBtn.className = 'w-full bg-green-500 text-white py-3 px-6 rounded-lg font-medium cursor-not-allowed';
        } else {
            throw new Error(result.message || 'Check-in failed');
        }
        
    } catch (error) {
        console.error('Check-in error:', error);
        showError(error.message || 'Check-in failed. Please try again.');
        
        // Re-enable form on error
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