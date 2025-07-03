/*
 * Check-in JavaScript Module
 * 
 * This module handles student attendance check-in functionality with device fingerprinting.
 * 
 * Key Changes from localStorage to Database reliance:
 * - Session status checking now queries the database via API instead of localStorage
 * - Device identity (visitor_id) is still stored in localStorage for consistency across sessions
 * - Check-in validation is performed server-side using database records
 * - Removed localStorage-based session tracking in favor of database validation
 * - Removed pop-up notifications; all feedback now uses persistent error log in #message div
 */

let fingerprintHash = '';
let deviceInfo = {};
let sessionId = '';
let hasCheckedIn = false;

// Utility function to validate API response format
function validateDeviceStatusResponse(data) {
    return data && 
           typeof data === 'object' && 
           typeof data.status === 'string' && 
           typeof data.has_checked_in === 'boolean';
}

// Generate a unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Check if device has already checked in this session using database
async function checkSessionStatus() {
    try {
        if (!fingerprintHash) {
            console.log('No fingerprint hash available for session check');
            return false;
        }
        
        // Show loading state
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.textContent = 'Checking device status...';
            submitBtn.disabled = true;
        }
        
        const response = await fetch('/api/check_device_status', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fingerprint_hash: fingerprintHash
            })
        });
        
        if (!response.ok) {
            console.error('Failed to check device status:', response.status, response.statusText);
            // On error, allow check-in attempt (fail-safe)
            return false;
        }
        
        const data = await response.json();
        
        if (validateDeviceStatusResponse(data) && data.status === 'success') {
            console.log('Device status check result:', data);
            return data.has_checked_in;
        } else {
            console.error('Error checking device status:', data.message);
            // On error, allow check-in attempt (fail-safe)
            return false;
        }
    } catch (error) {
        console.error('Error checking session status:', error);
        // On error, allow check-in attempt (fail-safe)
        return false;
    } finally {
        // Reset button state if it was changed
        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn && submitBtn.textContent === 'Checking device status...') {
            submitBtn.textContent = 'Check In';
            submitBtn.disabled = false;
        }
    }
}

// Generate fallback fingerprint with enhanced characteristics
function generateFallbackFingerprint() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Fingerprint test', 2, 2);
    
    const fingerprint = [
        navigator.userAgent,
        navigator.language,
    ].join('|');
    
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
        const char = fingerprint.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
}

// Enhanced message function with better styling for device blocking
function showMessage(text, type) {
    // Show persistent message in the message div (no pop-up notifications)
    const messageElement = document.getElementById('message');
    if (messageElement) {
        messageElement.innerHTML = text;
        messageElement.style.display = 'block';
        
        // Add special styling for device blocking messages
        if (text.includes('DEVICE BLOCKED')) {
            messageElement.style.cssText = `
                display: block !important;
                background-color: #f8d7da;
                color: #721c24;
                border: 2px solid #f5c6cb;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                font-weight: bold;
                font-size: 16px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            `;
        } else if (type === 'danger') {
            messageElement.style.cssText = `
                display: block !important;
                background-color: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
                padding: 10px;
                margin: 15px 0;
                font-weight: normal;
            `;
        } else if (type === 'warning') {
            messageElement.style.cssText = `
                display: block !important;
                background-color: #fff3cd;
                color: #856404;
                border: 1px solid #ffeaa7;
                border-radius: 4px;
                padding: 10px;
                margin: 15px 0;
                font-weight: normal;
            `;
        } else if (type === 'success') {
            messageElement.style.cssText = `
                display: block !important;
                background-color: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
                padding: 10px;
                margin: 15px 0;
                font-weight: normal;
            `;
        } else {
            // Default/info styling
            messageElement.style.cssText = `
                display: block !important;
                background-color: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
                border-radius: 4px;
                padding: 10px;
                margin: 15px 0;
                font-weight: normal;
            `;
        }
    }
}

// Function to clear persistent messages
function clearMessage() {
    const messageElement = document.getElementById('message');
    if (messageElement) {
        messageElement.style.display = 'none';
        messageElement.innerHTML = '';
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
        sessionId = generateSessionId();
        deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            screen: {
                width: screen.width,
                height: screen.height,
                colorDepth: screen.colorDepth
            },
            pixelRatio: window.devicePixelRatio,
            touchSupport: 'ontouchstart' in window,
            maxTouchPoints: navigator.maxTouchPoints || 0,
            cpuCores: navigator.hardwareConcurrency || 'unknown',
            deviceMemory: navigator.deviceMemory || 'unknown',
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink
            } : 'unknown'
        };

        let storedVisitorId = localStorage.getItem('visitor_id');
        if (storedVisitorId) {
            fingerprintHash = storedVisitorId;
        } else {
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
            localStorage.setItem('visitor_id', fingerprintHash);
        }

        // Only check session status if we have a valid fingerprint hash
        if (fingerprintHash && fingerprintHash.length > 0) {
            const hasCheckedIn = await checkSessionStatus();
            if (hasCheckedIn) {
                showMessage('This device has already checked in during this session.', 'warning');
                submitBtn.disabled = true;
                submitBtn.textContent = 'Already Checked In';
                document.getElementById('student_id').disabled = true;
                return;
            }
        } else {
            console.warn('No valid fingerprint hash generated, proceeding with caution');
        }

        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check In';
        clearMessage();  // Clear any existing error messages
    } catch (error) {
        console.error('Fingerprinting failed:', error);
        showMessage('Device fingerprinting failed. Using basic security mode.', 'danger');
        fingerprintHash = btoa(navigator.userAgent + Date.now()).substring(0, 16);
        document.getElementById('fingerprint_hash').value = fingerprintHash;
        document.getElementById('security-id').textContent = fingerprintHash.substring(0, 8) + '...';
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check In';
    }
}

function setupFormHandler() {
    // Form submission using common utility
    addEventListenerSafe('attendanceForm', 'submit', async function(e) {
        e.preventDefault();
        const studentId = getElement('student_id')?.value.trim();
        if (!studentId) {
            showEnhancedErrorMessage('missing_student_id');
            return;
        }
        try {
            setButtonLoading('submitBtn', true, 'Checking in...');
            const pathParts = window.location.pathname.split('/');
            const token = pathParts[pathParts.length - 1];

            // --- Use visitor_id from localStorage for device identity consistency ---
            // Note: visitor_id is still stored in localStorage for device identity,
            // but session validation is now handled by database
            let visitorId = localStorage.getItem('visitor_id');
            if (!visitorId) {
                if (window.FingerprintJS && window.FingerprintJS.load) {
                    try {
                        const fp = await FingerprintJS.load();
                        const result = await fp.get();
                        visitorId = result.visitorId;
                    } catch (fpError) {
                        visitorId = fingerprintHash || generateFallbackFingerprint();
                    }
                } else {
                    visitorId = fingerprintHash || generateFallbackFingerprint();
                }
                localStorage.setItem('visitor_id', visitorId);
            }

            if (!visitorId || typeof visitorId !== 'string' || visitorId.trim() === '') {
                visitorId = fingerprintHash || generateFallbackFingerprint();
            }

            const deviceData = {
                visitor_id: visitorId,
                screen_size: `${screen.width}x${screen.height}`,
                user_agent: navigator.userAgent,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                token: token,
                student_id: studentId,
                session_id: sessionId
            };
            console.log('Check-in payload:', deviceData); // Debug log
            
            // Handle the check-in request with simple error handling
            let result;
            try {
                result = await postJSON('/checkin', deviceData);
            } catch (error) {
                console.error('Check-in request failed:', error);
                
                // Simple approach: just throw the raw error message from the server
                // This will capture the actual server response without complex parsing
                throw error;
            }
            
            if (result.status === 'success') {
                showMessage(result.message || 'Check-in successful!', 'success');
                setButtonLoading('submitBtn', false, 'Checked In');
                document.getElementById('student_id').disabled = true;
            } else {
                throw new Error(result.message || 'Unknown error');
            }
        } catch (error) {
            console.error('Check-in error:', error);
            
            // Get the error message - simplified approach
            let errorMessage = error.message || 'Unknown error';
            let messageType = 'danger';
            
            console.log('Raw error message:', errorMessage);
            
            // Try to extract clean message from JSON error responses
            try {
                // Check if the error message contains JSON
                if (errorMessage.includes('{ "message":') || errorMessage.includes('{"message":')) {
                    const jsonMatch = errorMessage.match(/\{.*\}/);
                    if (jsonMatch) {
                        const errorObj = JSON.parse(jsonMatch[0]);
                        if (errorObj.message) {
                            errorMessage = errorObj.message;
                        }
                    }
                }
            } catch (parseError) {
                console.log('Could not parse JSON from error message, using raw message');
            }
            
            console.log('Cleaned error message:', errorMessage);
            
            // Check for device blocking messages
            if (errorMessage.toLowerCase().includes('device already used') || 
                errorMessage.toLowerCase().includes('device blocked') ||
                errorMessage.toLowerCase().includes('maximum allowed')) {
                messageType = 'warning';
                // Make device blocking messages more prominent
                showMessage('⚠️ DEVICE BLOCKED: ' + errorMessage, messageType);
                
                // Also disable the form to prevent repeated attempts
                document.getElementById('student_id').disabled = true;
                document.getElementById('submitBtn').disabled = true;
                document.getElementById('submitBtn').textContent = 'Device Blocked';
                
                return; // Exit early to avoid the generic error message below
            }
            
            // Check for other specific error types
            if (errorMessage.toLowerCase().includes('invalid token') || 
                errorMessage.toLowerCase().includes('token')) {
                errorMessage = '🔒 Invalid or expired QR code. Please scan a new QR code.';
            } else if (errorMessage.toLowerCase().includes('student not found')) {
                errorMessage = '👤 Student ID not found. Please check your student ID and try again.';
            } else if (errorMessage.toLowerCase().includes('session')) {
                errorMessage = '📅 Session error. Please contact the instructor.';
            }
            
            showMessage('❌ Check-in failed: ' + errorMessage, messageType);
            setButtonLoading('submitBtn', false);
        }
    });
    
    // Clear error messages when user starts typing again (unless device is blocked)
    addEventListenerSafe('student_id', 'input', function() {
        const submitBtn = document.getElementById('submitBtn');
        // Only clear if the device is not blocked
        if (submitBtn && submitBtn.textContent !== 'Device Blocked' && submitBtn.textContent !== 'Already Checked In') {
            // Clear any persistent error messages
            clearMessage();
            
            // Re-enable the submit button if it was disabled due to non-blocking errors
            if (submitBtn.disabled && submitBtn.textContent !== 'Device Blocked' && submitBtn.textContent !== 'Already Checked In') {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Check In';
            }
        }
    });
}