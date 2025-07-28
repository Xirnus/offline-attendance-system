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
let hasCheckedIn = false;

// Utility function to validate API response format
function validateDeviceStatusResponse(data) {
    return data && 
           typeof data === 'object' && 
           typeof data.status === 'string' && 
           typeof data.has_checked_in === 'boolean';
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

// Mark device as checked in - database handles this automatically, no localStorage needed
function markCheckedIn() {
    // Database automatically records the check-in when the API call succeeds
    // No need to store in localStorage as we now rely on database
    console.log('Check-in recorded in database for device:', fingerprintHash);
}

// Enhanced fingerprinting functions for better device distinction
function getCanvasFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = 200;
        canvas.height = 50;
        
        // Draw text with different styles
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
        ctx.fillText('Canvas fingerprint 🔒', 2, 2);
        
        ctx.font = '18px serif';
        ctx.fillStyle = 'rgba(255, 0, 102, 0.8)';
        ctx.fillText('Device ID', 4, 20);
        
        // Add some geometric shapes
        ctx.globalCompositeOperation = 'multiply';
        ctx.fillStyle = 'rgb(255,0,255)';
        ctx.beginPath();
        ctx.arc(50, 25, 20, 0, Math.PI * 2);
        ctx.fill();
        
        return canvas.toDataURL();
    } catch (e) {
        return 'canvas_error';
    }
}

function getAdvancedCanvasFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        canvas.width = 280;
        canvas.height = 60;
        const ctx = canvas.getContext('2d');
        
        // More complex drawing that varies by GPU/driver
        const gradient = ctx.createLinearGradient(0, 0, 280, 60);
        gradient.addColorStop(0, 'rgb(255,0,0)');
        gradient.addColorStop(0.5, 'rgb(0,255,0)');
        gradient.addColorStop(1, 'rgb(0,0,255)');
        
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 280, 60);
        
        // Text rendering variations
        ctx.font = 'bold 16px Arial';
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.fillText('Device ID: ' + Date.now().toString().slice(-6), 10, 25);
        
        // Complex shapes that render differently on different devices
        ctx.beginPath();
        ctx.arc(200, 30, 15, 0, 2 * Math.PI);
        ctx.strokeStyle = 'yellow';
        ctx.lineWidth = 3;
        ctx.stroke();
        
        // Shadow effects
        ctx.shadowColor = 'black';
        ctx.shadowBlur = 10;
        ctx.fillStyle = 'white';
        ctx.fillRect(230, 15, 30, 30);
        
        return canvas.toDataURL();
    } catch (e) {
        return 'advanced_canvas_error';
    }
}

function getWebGLFingerprint() {
    try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        
        if (!gl) return 'webgl_not_supported';
        
        const renderer = gl.getParameter(gl.RENDERER);
        const vendor = gl.getParameter(gl.VENDOR);
        const version = gl.getParameter(gl.VERSION);
        const shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
        
        return `${renderer}|${vendor}|${version}|${shadingLanguageVersion}`;
    } catch (e) {
        return 'webgl_error';
    }
}

function getAudioFingerprint() {
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const analyser = audioContext.createAnalyser();
        const gainNode = audioContext.createGain();
        
        oscillator.type = 'triangle';
        oscillator.frequency.value = 10000;
        
        gainNode.gain.value = 0;
        oscillator.connect(analyser);
        analyser.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.start(0);
        
        const frequencyData = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(frequencyData);
        
        oscillator.stop();
        audioContext.close();
        
        return Array.from(frequencyData).slice(0, 30).join(',');
    } catch (e) {
        return 'audio_error';
    }
}

function getAvailableFonts() {
    try {
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testFonts = [
            'Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 'Georgia',
            'Helvetica', 'Impact', 'Lucida Console', 'Tahoma', 'Times New Roman',
            'Trebuchet MS', 'Verdana', 'Webdings', 'Wingdings'
        ];
        
        const testString = 'mmmmmmmmmmlli';
        const testSize = '72px';
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const baselines = {};
        baseFonts.forEach(font => {
            ctx.font = testSize + ' ' + font;
            baselines[font] = ctx.measureText(testString).width;
        });
        
        const availableFonts = [];
        testFonts.forEach(font => {
            baseFonts.forEach(baseFont => {
                ctx.font = testSize + ' ' + font + ', ' + baseFont;
                const width = ctx.measureText(testString).width;
                if (width !== baselines[baseFont]) {
                    availableFonts.push(font);
                    return;
                }
            });
        });
        
        return availableFonts.join(',');
    } catch (e) {
        return 'fonts_error';
    }
}

function getMemoryInfo() {
    try {
        if (navigator.deviceMemory) {
            return navigator.deviceMemory.toString();
        }
        if (performance && performance.memory) {
            return `${performance.memory.jsHeapSizeLimit},${performance.memory.totalJSHeapSize}`;
        }
        return 'memory_unknown';
    } catch (e) {
        return 'memory_error';
    }
}

function getCPUCores() {
    try {
        return navigator.hardwareConcurrency ? navigator.hardwareConcurrency.toString() : 'cpu_unknown';
    } catch (e) {
        return 'cpu_error';
    }
}

function getMaxTouchPoints() {
    try {
        return navigator.maxTouchPoints ? navigator.maxTouchPoints.toString() : '0';
    } catch (e) {
        return 'touch_error';
    }
}

async function getBatteryLevel() {
    try {
        if (navigator.getBattery) {
            const battery = await navigator.getBattery();
            return `${battery.level},${battery.charging}`;
        }
        return 'battery_unknown';
    } catch (e) {
        return 'battery_error';
    }
}

function getConnectionType() {
    try {
        if (navigator.connection) {
            return `${navigator.connection.effectiveType || 'unknown'},${navigator.connection.downlink || 'unknown'}`;
        }
        return 'connection_unknown';
    } catch (e) {
        return 'connection_error';
    }
}

function getInstalledPlugins() {
    try {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push(navigator.plugins[i].name);
        }
        return plugins.slice(0, 10).join(','); // Limit to first 10 plugins
    } catch (e) {
        return 'plugins_error';
    }
}

function getDoNotTrack() {
    try {
        return navigator.doNotTrack || 'unknown';
    } catch (e) {
        return 'dnt_error';
    }
}

function getDetailedHardwareInfo() {
    try {
        const info = {
            // Screen details
            screenDetails: `${screen.width}x${screen.height}x${screen.colorDepth}@${window.devicePixelRatio}`,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            
            // Viewport details
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight,
            
            // Orientation
            orientation: screen.orientation ? screen.orientation.type : 'unknown',
            
            // Touch capabilities
            touchPoints: navigator.maxTouchPoints,
            touchSupport: 'ontouchstart' in window,
            
            // Performance timing (unique per device boot)
            performanceTiming: performance.timing ? 
                (performance.timing.loadEventEnd - performance.timing.navigationStart) : 0,
                
            // Memory pressure indicators
            memoryInfo: navigator.deviceMemory || 'unknown',
            
            // Network information
            connectionType: navigator.connection ? 
                `${navigator.connection.effectiveType}_${navigator.connection.downlink}` : 'unknown'
        };
        
        return JSON.stringify(info);
    } catch (e) {
        return 'hardware_info_error';
    }
}

function getTimingBasedFingerprint() {
    try {
        const start = performance.now();
        
        // CPU-intensive operation that varies by device performance
        let result = 0;
        for (let i = 0; i < 100000; i++) {
            result += Math.sin(i) * Math.cos(i);
        }
        
        const end = performance.now();
        const executionTime = Math.round(end - start);
        
        // Combine with system time for uniqueness
        const timeZoneOffset = new Date().getTimezoneOffset();
        const currentTime = Date.now().toString().slice(-8);
        
        return `${executionTime}_${timeZoneOffset}_${currentTime}`;
    } catch (e) {
        return 'timing_error';
    }
}

function getStorageFingerprint() {
    try {
        // Test local storage capabilities
        const testKey = 'fp_test_' + Date.now();
        const testValue = 'test_value_' + Math.random();
        
        localStorage.setItem(testKey, testValue);
        const retrieved = localStorage.getItem(testKey);
        localStorage.removeItem(testKey);
        
        // Get storage estimates if available
        if (navigator.storage && navigator.storage.estimate) {
            navigator.storage.estimate().then(estimate => {
                return `${estimate.quota}_${estimate.usage}`;
            });
        }
        
        return retrieved === testValue ? 'storage_available' : 'storage_limited';
    } catch (e) {
        return 'storage_error';
    }
}

function detectVirtualEnvironment() {
    try {
        // Check for common emulator indicators
        const ua = navigator.userAgent.toLowerCase();
        const indicators = [
            'android sdk built for x86',
            'bluestacks',
            'noxplayer',
            'memu',
            'ldplayer',
            'virtualbox',
            'vmware'
        ];
        
        return indicators.some(indicator => ua.includes(indicator));
    } catch (e) {
        return false;
    }
}

function checkDeviceConsistency() {
    try {
        // Check for inconsistencies that might indicate spoofing
        const inconsistencies = [];
        
        // Check if touch support matches claimed device type
        const isMobile = /android|iphone|ipad/i.test(navigator.userAgent);
        const hasTouch = 'ontouchstart' in window;
        
        if (isMobile && !hasTouch) {
            inconsistencies.push('mobile_no_touch');
        }
        
        // Check screen resolution consistency
        const pixelRatio = window.devicePixelRatio || 1;
        if (pixelRatio > 3 && screen.width < 400) {
            inconsistencies.push('suspicious_pixel_ratio');
        }
        
        return inconsistencies;
    } catch (e) {
        return ['consistency_check_error'];
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
        screen.width + 'x' + screen.height,
        new Date().getTimezoneOffset(),
        navigator.platform,
        navigator.cookieEnabled,
        typeof(navigator.doNotTrack),
        canvas.toDataURL(),
        // Enhanced characteristics for better mobile distinction
        screen.colorDepth,
        window.devicePixelRatio,
        navigator.hardwareConcurrency || 'unknown',
        navigator.maxTouchPoints || 0,
        navigator.deviceMemory || 'unknown',
        getCanvasFingerprint().substring(0, 50), // Truncated for performance
        getCPUCores(),
        getMaxTouchPoints(),
        getConnectionType()
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
        // Note: sessionId generation removed - backend uses database session ID
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

        // --- Stable visitor_id logic (kept in localStorage for device identity consistency) ---
        // Note: visitor_id represents device identity and is kept in localStorage for consistency
        // across browser sessions, but session status checking now relies on database
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
        document.getElementById('device-info').textContent = getDeviceDescription();
        submitBtn.disabled = false;
        submitBtn.textContent = 'Check In';
        clearMessage();  // Clear any existing error messages
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
                student_id: studentId
                // Note: session_id removed - backend will use database session ID
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
                markCheckedIn();
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
            } else if (errorMessage.toLowerCase().includes('already checked in')) {
                errorMessage = '✅ You have already checked in for this session.';
            } else if (errorMessage.toLowerCase().includes('device has already been used')) {
                errorMessage = '� This device has already been used for check-in. Please use a different device.';
            } else if (errorMessage.toLowerCase().includes('no active attendance session')) {
                errorMessage = '📅 No active session. Please contact the instructor.';
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