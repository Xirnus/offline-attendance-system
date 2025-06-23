let fingerprintHash = '';
let deviceInfo = {};

// Generate fallback fingerprint
function generateFallbackFingerprint() {
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
    
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

// Simple message function
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `alert-${type}`;
    messageDiv.style.display = 'block';
    
    // Keep success messages visible longer
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.backgroundColor = '#c8e6c9';
        }, 100);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeFingerprinting();
    setupFormHandler();
});

async function initializeFingerprinting() {
    const submitBtn = document.getElementById('submitBtn');
    
    try {
        showMessage('Generating device fingerprint...', 'info');
        
        deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            }
        };

        if (window.FingerprintJS && window.FingerprintJS.load) {
            try {
                const fp = await FingerprintJS.load();
                const result = await fp.get();
                fingerprintHash = result.visitorId;
            } catch (fpError) {
                fingerprintHash = generateFallbackFingerprint();
            }
        } else {
            fingerprintHash = generateFallbackFingerprint();
        }

        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        document.getElementById('device-info').textContent = getDeviceDescription();
        
        // Enable form
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check In';
        
        // Clear initialization message
        document.getElementById('message').style.display = 'none';
        
    } catch (error) {
        console.error('Fingerprinting failed:', error);
        showMessage('Device fingerprinting failed. Using basic security mode.', 'danger');
        
        fingerprintHash = btoa(navigator.userAgent + Date.now()).substring(0, 16);
        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        document.getElementById('device-info').textContent = getDeviceDescription();
        
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check In';
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

function setupFormHandler() {
    // Form submission
    document.getElementById('attendanceForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const studentId = document.getElementById('student_id').value.trim();
        const submitBtn = document.getElementById('submitBtn');
        
        if (!studentId) {
            showMessage('Please enter your Student ID', 'danger');
            return;
        }
        
        try {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Checking in...';
            showMessage('Processing check-in...', 'info');
            
            const pathParts = window.location.pathname.split('/');
            const token = pathParts[pathParts.length - 1];
            
            const deviceData = {
                token: token,
                student_id: studentId,
                fingerprint_hash: fingerprintHash,
                user_agent: navigator.userAgent,
                screen_resolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                language: navigator.language,
                platform: navigator.platform,
                color_depth: screen.colorDepth,
                pixel_ratio: window.devicePixelRatio,
                touch_support: 'ontouchstart' in window
            };
            
            const response = await fetch('/checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(deviceData)
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                showMessage(result.message, 'success');
                document.getElementById('attendanceForm').style.display = 'none';
            } else {
                showMessage(result.message || 'Check-in failed', 'danger');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Check In';
            }
            
        } catch (error) {
            console.error('Error:', error);
            showMessage('Network error. Please try again.', 'danger');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Check In';
        }
    });
}