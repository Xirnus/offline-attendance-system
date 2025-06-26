let fingerprintHash = '';
let deviceInfo = {};
let sessionId = '';
let hasCheckedIn = false;

// Generate a unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Check if device has already checked in this session
function checkSessionStatus() {
    const sessionKey = 'attendance_session_' + fingerprintHash;
    const sessionData = localStorage.getItem(sessionKey);
    
    if (sessionData) {
        const data = JSON.parse(sessionData);
        // Check if session is still valid (e.g., within last 24 hours)
        const sessionAge = Date.now() - data.timestamp;
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours
        
        if (sessionAge < maxAge && data.checkedIn) {
            return true;
        }
    }
    return false;
}

// Mark device as checked in for this session
function markCheckedIn() {
    const sessionKey = 'attendance_session_' + fingerprintHash;
    const sessionData = {
        sessionId: sessionId,
        checkedIn: true,
        timestamp: Date.now(),
        fingerprint: fingerprintHash
    };
    localStorage.setItem(sessionKey, JSON.stringify(sessionData));
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
        // Generate session ID first
        sessionId = generateSessionId();
        
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
            },
            // Enhanced device characteristics
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

        // Generate fingerprint first
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

        // After fingerprint is generated, check session status
        if (checkSessionStatus()) {
            showMessage('This device has already checked in during this session.', 'warning');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Already Checked In';
            document.getElementById('student_id').disabled = true;
            return;
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
                session_id: sessionId, // Add session ID
                
                // Enhanced fingerprinting
                detailed_hardware: getDetailedHardwareInfo(),
                advanced_canvas: getAdvancedCanvasFingerprint(),
                timing_fingerprint: getTimingBasedFingerprint(),
                storage_fingerprint: getStorageFingerprint(),
                
                // Security checks
                virtual_environment: detectVirtualEnvironment(),
                device_consistency: checkDeviceConsistency(),
                
                // Existing data
                user_agent: navigator.userAgent,
                screen_resolution: `${screen.width}x${screen.height}`,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                language: navigator.language,
                platform: navigator.platform,
                color_depth: screen.colorDepth,
                pixel_ratio: window.devicePixelRatio,
                touch_support: 'ontouchstart' in window,
                canvas_fingerprint: getCanvasFingerprint(),
                webgl_fingerprint: getWebGLFingerprint(),
                audio_fingerprint: getAudioFingerprint(),
                available_fonts: getAvailableFonts(),
                memory_info: getMemoryInfo(),
                cpu_cores: getCPUCores(),
                max_touch_points: getMaxTouchPoints(),
                battery_level: await getBatteryLevel(),
                connection_type: getConnectionType(),
                installed_plugins: getInstalledPlugins(),
                do_not_track: getDoNotTrack(),
                
                // Additional unique identifiers
                timestamp: Date.now(),
                random_seed: Math.random().toString(36)
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
                markCheckedIn(); // Mark as checked in locally
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