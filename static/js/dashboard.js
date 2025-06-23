// Global variables
let attendanceData = [];
let deniedAttempts = [];
let deviceFingerprints = [];
let lastUpdateTime = 0;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
  loadSettings();
  loadData();
  setupEventListeners();
  
  // Add session status check here
  checkSessionStatusWithExpiration();
  
  // REDUCED refresh frequency to prevent database locks
  setInterval(loadData, 15000); // Refresh every 15 seconds instead of 5
  
  // Check session status every 60 seconds instead of 30
  setInterval(checkSessionStatusWithExpiration, 60000);

  // Also add visibility change listener to refresh when tab becomes active
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      // Add a small delay to prevent immediate database contention
      setTimeout(() => {
        loadData();
        checkSessionStatusWithExpiration();
      }, 500);
    }
  });
});

// Add debouncing to prevent rapid API calls
let loadDataTimeout;
async function loadData() {
  // Clear any pending loadData calls
  if (loadDataTimeout) {
    clearTimeout(loadDataTimeout);
  }
  
  loadDataTimeout = setTimeout(async () => {
    try {
      const [attendanceRes, deniedRes, devicesRes] = await Promise.all([
        fetch('/api/attendances'),
        fetch('/api/denied'),
        fetch('/api/device_fingerprints')
      ]);
      
      const newAttendanceData = await attendanceRes.json();
      const newDeniedAttempts = await deniedRes.json();
      const newDeviceFingerprints = await devicesRes.json();
      
      // Check if we have new data
      const hasNewData = 
        newAttendanceData.length !== attendanceData.length ||
        newDeniedAttempts.length !== deniedAttempts.length ||
        newDeviceFingerprints.length !== deviceFingerprints.length;
      
      // Update data
      attendanceData = newAttendanceData;
      deniedAttempts = newDeniedAttempts;
      deviceFingerprints = newDeviceFingerprints;
      
      // Update displays
      updateStatistics();
      updateAttendanceTable();
      updateDeniedTable();
      updateDeviceTable();
      
      // Show notification for new check-ins
      if (hasNewData && lastUpdateTime > 0) {
        showNotification('New activity detected!', 'info');
      }
      
      lastUpdateTime = Date.now();
      
    } catch (error) {
      console.error('Error loading data:', error);
    }
  }, 100); // Small delay to prevent rapid calls
}

function setupEventListeners() {
  document.getElementById('generate-btn').addEventListener('click', generateQR);
  document.getElementById('save-settings').addEventListener('click', saveSettings);
  document.getElementById('refresh-data').addEventListener('click', loadData);
  document.getElementById('export-data').addEventListener('click', exportData);
  document.getElementById('clear-old-data').addEventListener('click', clearOldData);
  
  // Add session event listeners here
  const createSessionBtn = document.getElementById('create-session-btn');
  const stopSessionBtn = document.getElementById('stop-session-btn');
  
  console.log('Setting up event listeners...');
  console.log('Create button found:', !!createSessionBtn);
  console.log('Stop button found:', !!stopSessionBtn);
  
  if (createSessionBtn) {
    createSessionBtn.addEventListener('click', function(e) {
      console.log('Create session button clicked!');
      e.preventDefault();
      
      const sessionName = prompt('Enter session name:');
      if (!sessionName) return;
      
      const startTime = new Date().toISOString();
      
      // Simplified time input - just hours and minutes
      const endTimeInput = prompt('Enter end time (HH:MM) - example: 14:30 for 2:30 PM:');
      if (!endTimeInput) return;
      
      // Parse the time input and create full datetime
      const timeMatch = endTimeInput.match(/^(\d{1,2}):(\d{2})$/);
      if (!timeMatch) {
        alert('Invalid time format. Please use HH:MM format (e.g., 14:30)');
        return;
      }
      
      const hours = parseInt(timeMatch[1]);
      const minutes = parseInt(timeMatch[2]);
      
      if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) {
        alert('Invalid time. Hours must be 0-23 and minutes must be 0-59');
        return;
      }
      
      // Create end time for today with the specified time
      const endTime = new Date();
      endTime.setHours(hours, minutes, 0, 0);
      
      // If the end time is earlier than now, assume it's for tomorrow
      if (endTime <= new Date()) {
        endTime.setDate(endTime.getDate() + 1);
      }
      
      createSession(sessionName, startTime, endTime.toISOString());
    });
  }
  
  if (stopSessionBtn) {
    stopSessionBtn.addEventListener('click', function(e) {
      console.log('Stop session button clicked!');
      e.preventDefault();
      
      if (confirm('Are you sure you want to stop the current session?')) {
        stopSession();
      }
    });
  }
}

function createSession(sessionName, startTime, endTime) {
    console.log('Creating session:', { sessionName, startTime, endTime });
    
    // Show loading state
    const createBtn = document.getElementById('create-session-btn');
    const originalText = createBtn.textContent;
    createBtn.disabled = true;
    createBtn.textContent = 'Creating Session...';
    
    fetch('/api/create_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_name: sessionName,
            start_time: startTime,
            end_time: endTime
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Create session response:', data);
        if (data.status === 'success') {
            showNotification('Session created successfully', 'success');
            // IMMEDIATELY force the button update with session details
            console.log('Forcing immediate button update...');
            const sessionData = {
                session_name: sessionName,
                start_time: startTime,
                end_time: endTime
            };
            updateButtonVisibility(true, sessionName);
            displaySessionDetails(sessionData);
        } else {
            showNotification('Error creating session: ' + data.message, 'error');
            // Reset button state on error
            createBtn.disabled = false;
            createBtn.textContent = originalText;
        }
    })
    .catch(error => {
        showNotification('Error creating session', 'error');
        console.error('Error:', error);
        // Reset button state on error
        createBtn.disabled = false;
        createBtn.textContent = originalText;
    });
}

function stopSession() {
    console.log('stopSession function called');
    
    const stopBtn = document.getElementById('stop-session-btn');
    if (!stopBtn) {
        console.error('Stop button not found!');
        return;
    }
    
    const originalText = stopBtn.textContent;
    stopBtn.disabled = true;
    stopBtn.textContent = 'Stopping...';
    
    console.log('Making API call to stop session...');
    
    fetch('/api/stop_session', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('Stop session response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Stop session response data:', data);
        if (data.status === 'success' || data.success) {
            const absentCount = data.absent_marked || 0;
            const message = absentCount > 0 
                ? `Session stopped successfully. ${absentCount} students marked absent.`
                : 'Session stopped successfully';
            
            showNotification(message, 'success');
            updateButtonVisibility(false, '');
            
            // Refresh data to show updated student statuses
            setTimeout(() => {
                loadData();
            }, 500);
        } else {
            showNotification('Error stopping session: ' + (data.message || 'Unknown error'), 'error');
            stopBtn.disabled = false;
            stopBtn.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showNotification('Error stopping session', 'error');
        stopBtn.disabled = false;
        stopBtn.textContent = originalText;
    });
}

function updateButtonVisibility(hasActiveSession, sessionName = '') {
    const createSessionBtn = document.getElementById('create-session-btn');
    const stopSessionBtn = document.getElementById('stop-session-btn');
    const sessionStatus = document.getElementById('session-status');
    
    console.log('updateButtonVisibility called with:', { hasActiveSession, sessionName });
    
    if (hasActiveSession) {
        console.log('Setting up for active session...');
        if (sessionStatus) {
            sessionStatus.innerHTML = `
                <strong>Active: ${sessionName}</strong><br>
                <small id="session-details">Loading session details...</small>
            `;
        }
        if (createSessionBtn) {
            createSessionBtn.style.display = 'none';
            createSessionBtn.disabled = false;
            createSessionBtn.textContent = 'Create Attendance Session';
        }
        if (stopSessionBtn) {
            stopSessionBtn.style.display = 'inline-block';
            stopSessionBtn.disabled = false;
            stopSessionBtn.textContent = 'Stop Session';
        }
    } else {
        console.log('Setting up for no active session...');
        if (sessionStatus) {
            sessionStatus.innerHTML = '<span>No active session</span>';
        }
        if (createSessionBtn) {
            createSessionBtn.style.display = 'inline-block';
            createSessionBtn.disabled = false;
            createSessionBtn.textContent = 'Create Attendance Session';
        }
        if (stopSessionBtn) {
            stopSessionBtn.style.display = 'none';
            stopSessionBtn.disabled = false;
            stopSessionBtn.textContent = 'Stop Session';
        }
    }
    
    console.log('Button visibility updated. Create visible:', createSessionBtn?.style.display !== 'none', 'Stop visible:', stopSessionBtn?.style.display !== 'none');
}


function displaySessionDetails(session) {
    console.log('Displaying session details:', session);
    const sessionDetailsElement = document.getElementById('session-details');
    if (!sessionDetailsElement) {
        console.log('Session details element not found');
        return;
    }
    
    try {
        const startTime = new Date(session.start_time);
        const endTime = new Date(session.end_time);
        const now = new Date();
        
        console.log('Times:', { startTime, endTime, now });
        
        // Calculate time remaining
        const timeRemaining = endTime - now;
        const hoursRemaining = Math.floor(timeRemaining / (1000 * 60 * 60));
        const minutesRemaining = Math.floor((timeRemaining % (1000 * 60 * 60)) / (1000 * 60));
        
        let timeRemainingText = '';
        if (timeRemaining > 0) {
            if (hoursRemaining > 0) {
                timeRemainingText = `${hoursRemaining}h ${minutesRemaining}m remaining`;
            } else if (minutesRemaining > 0) {
                timeRemainingText = `${minutesRemaining}m remaining`;
            } else {
                timeRemainingText = 'Less than 1 minute remaining';
            }
        } else {
            timeRemainingText = 'Session expired';
        }
        
        const detailsHTML = `
            Started: ${startTime.toLocaleString()}<br>
            Ends: ${endTime.toLocaleString()}<br>
            <span style="color: ${timeRemaining > 0 ? '#28a745' : '#dc3545'};">
                ${timeRemainingText}
            </span>
        `;
        
        console.log('Setting session details HTML:', detailsHTML);
        sessionDetailsElement.innerHTML = detailsHTML;
        
    } catch (error) {
        console.error('Error in displaySessionDetails:', error);
        sessionDetailsElement.innerHTML = 'Error loading session details';
    }
}

function checkSessionStatus() {
    console.log('Checking session status...');
    fetch('/api/session_status')
    .then(response => response.json())
    .then(data => {
        console.log('Session status response:', data);
        
        if (data.active_session) {
            console.log('Active session found:', data.active_session);
            
            // Check if session has expired
            const endTime = new Date(data.active_session.end_time);
            const now = new Date();
            
            if (endTime <= now) {
                console.log('Session has expired, updating buttons...');
                updateButtonVisibility(false, '');
                showNotification('Session has expired', 'info');
            } else {
                updateButtonVisibility(true, data.active_session.session_name);
                // Update session details after setting up buttons
                setTimeout(() => {
                    displaySessionDetails(data.active_session);
                }, 100);
            }
        } else {
            console.log('No active session found');
            updateButtonVisibility(false);
        }
    })
    .catch(error => {
        console.error('Error checking session status:', error);
        // On error, assume no active session to prevent stuck UI
        updateButtonVisibility(false);
    });
}

function checkSessionStatusWithExpiration() {
    fetch('/api/session_status')
    .then(response => response.json())
    .then(data => {
        if (data.active_session) {
            const endTime = new Date(data.active_session.end_time);
            const now = new Date();
            
            if (endTime <= now) {
                // Session has expired, automatically stop it
                console.log('Session expired, automatically stopping...');
                
                // Call the backend to stop session and mark absents
                fetch('/api/stop_session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(stopData => {
                    console.log('Auto-stopped expired session:', stopData);
                    updateButtonVisibility(false, '');
                    
                    if (stopData.absent_marked > 0) {
                        showNotification(`Session ended. ${stopData.absent_marked} students marked absent`, 'info');
                    } else {
                        showNotification('Session automatically ended (expired)', 'info');
                    }
                });
            } else {
                updateButtonVisibility(true, data.active_session.session_name);
                displaySessionDetails(data.active_session);
            }
        } else {
            updateButtonVisibility(false);
        }
    })
    .catch(error => {
        console.error('Error checking session status:', error);
        updateButtonVisibility(false);
    });
}


async function generateQR() {
  try {
    const btn = document.getElementById('generate-btn');
    const status = document.getElementById('qr-status');
    const img = document.getElementById('qr-img');
    
    btn.disabled = true;
    btn.textContent = 'Generating...';
    status.textContent = 'Generating QR code...';
    
    const response = await fetch('/generate_qr');
    if (response.ok) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      img.src = url;
      status.textContent = 'QR code generated successfully';
    } else {
      throw new Error('Failed to generate QR code');
    }
  } catch (error) {
    console.error('Error generating QR:', error);
    document.getElementById('qr-status').textContent = 'Error generating QR code';
  } finally {
    const btn = document.getElementById('generate-btn');
    btn.disabled = false;
    btn.textContent = 'Generate New QR Code';
  }
}

async function loadSettings() {
  try {
    const response = await fetch('/api/settings');
    const settings = await response.json();
    
    document.getElementById('max-uses').value = settings.max_uses_per_device || 1;
    document.getElementById('time-window').value = (settings.time_window_minutes || 1440) / 60;
    document.getElementById('enable-blocking').checked = settings.enable_fingerprint_blocking !== false;
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

async function saveSettings() {
  try {
    const settings = {
      max_uses_per_device: parseInt(document.getElementById('max-uses').value),
      time_window_minutes: parseInt(document.getElementById('time-window').value) * 60,
      enable_fingerprint_blocking: document.getElementById('enable-blocking').checked
    };
    
    const response = await fetch('/api/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(settings)
    });
    
    if (response.ok) {
      showNotification('Settings saved successfully', 'success');
    } else {
      throw new Error('Failed to save settings');
    }
  } catch (error) {
    console.error('Error saving settings:', error);
    showNotification('Error saving settings', 'error');
  }
}

async function loadData() {
  try {
    const [attendanceRes, deniedRes, devicesRes] = await Promise.all([
      fetch('/api/attendances'),
      fetch('/api/denied'),
      fetch('/api/device_fingerprints')
    ]);
    
    const newAttendanceData = await attendanceRes.json();
    const newDeniedAttempts = await deniedRes.json();
    const newDeviceFingerprints = await devicesRes.json();
    
    // Check if we have new data
    const hasNewData = 
      newAttendanceData.length !== attendanceData.length ||
      newDeniedAttempts.length !== deniedAttempts.length ||
      newDeviceFingerprints.length !== deviceFingerprints.length;
    
    // Update data
    attendanceData = newAttendanceData;
    deniedAttempts = newDeniedAttempts;
    deviceFingerprints = newDeviceFingerprints;
    
    // Update displays
    updateStatistics();
    updateAttendanceTable();
    updateDeniedTable();
    updateDeviceTable();
    
    // Show notification for new check-ins
    if (hasNewData && lastUpdateTime > 0) {
      showNotification('New activity detected!', 'info');
    }
    
    lastUpdateTime = Date.now();
    
  } catch (error) {
    console.error('Error loading data:', error);
  }
}

// Enhanced function to show detailed device info in a modal or tooltip
function showDetailedDeviceInfo(deviceInfoStr) {
  try {
    if (!deviceInfoStr) return;
    
    const info = JSON.parse(deviceInfoStr);
    
    let details = '';
    
    if (info.device_signature) {
      const device = info.device_signature;
      details += `<strong>Device Details:</strong><br>`;
      details += `Type: ${device.type || 'Unknown'}<br>`;
      details += `Brand: ${device.brand || 'Unknown'}<br>`;
      details += `Model: ${device.model || 'Unknown'}<br>`;
      details += `OS: ${device.os || 'Unknown'}`;
      if (device.os_version) {
        details += ` ${device.os_version}`;
      }
      details += `<br>`;
      details += `Browser: ${device.browser || 'Unknown'}`;
      if (device.browser_version) {
        details += ` ${device.browser_version}`;
      }
      details += `<br><br>`;
    }
    
    details += `<strong>Technical Info:</strong><br>`;
    details += `Screen: ${info.screen_resolution || 'Unknown'}<br>`;
    details += `Timezone: ${info.timezone || 'Unknown'}<br>`;
    details += `Language: ${info.language || 'Unknown'}<br>`;
    details += `Platform: ${info.platform || 'Unknown'}<br>`;
    
    if (info.color_depth) {
      details += `Color Depth: ${info.color_depth}<br>`;
    }
    if (info.pixel_ratio) {
      details += `Pixel Ratio: ${info.pixel_ratio}<br>`;
    }
    if (info.touch_support !== undefined) {
      details += `Touch Support: ${info.touch_support ? 'Yes' : 'No'}<br>`;
    }
    
    // Show in a modal or alert 
    showDeviceModal(details);
    
  } catch (error) {
    console.error('Error showing device details:', error);
  }
}

function showDeviceModal(content) {
  // Create a simple modal 
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  `;
  
  const modalContent = document.createElement('div');
  modalContent.style.cssText = `
    background: white;
    padding: 20px;
    border-radius: 8px;
    max-width: 500px;
    max-height: 80vh;
    overflow-y: auto;
  `;
  
  modalContent.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
      <h3>Device Information</h3>
      <button onclick="this.closest('[style*=fixed]').remove()" style="border: none; background: #ccc; border-radius: 4px; padding: 5px 10px; cursor: pointer;">×</button>
    </div>
    <div>${content}</div>
  `;
  
  modal.appendChild(modalContent);
  document.body.appendChild(modal);
  
  // Close on outside click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

function updateStatistics() {
  const now = Date.now() / 1000;
  const oneHourAgo = now - 3600;
  
  const recentActivity = attendanceData.filter(a => a.timestamp > oneHourAgo).length;
  const uniqueDevices = new Set(attendanceData.map(a => a.fingerprint_hash)).size;
  
  document.getElementById('total-attendances').textContent = attendanceData.length;
  document.getElementById('total-denied').textContent = deniedAttempts.length;
  document.getElementById('unique-devices').textContent = uniqueDevices;
  document.getElementById('recent-activity').textContent = recentActivity;
}

function updateAttendanceTable() {
  const tbody = document.getElementById('attendances');
  
  if (attendanceData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">No check-ins yet</td></tr>';
    return;
  }
  
  tbody.innerHTML = attendanceData.slice(0, 50).map(item => `
    <tr>
      <td>${formatTimestamp(item.timestamp)}</td>
      <td>${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.course)}</td>
      <td>${escapeHtml(item.year)}</td>
      <td>
        <span 
          style="cursor: pointer; color: #007bff; text-decoration: underline;" 
          onclick="showDetailedDeviceInfo('${escapeHtml(item.device_info)}')"
          title="Click for detailed device information"
        >
          ${getDeviceInfo(item.device_info)}
        </span>
      </td>
      <td>${item.token.substring(0, 8)}...</td>
    </tr>
  `).join('');
}

function updateDeniedTable() {
  const tbody = document.getElementById('denied-attendances');
  
  if (deniedAttempts.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">No failed attempts</td></tr>';
    return;
  }
  
  tbody.innerHTML = deniedAttempts.slice(0, 50).map(item => `
    <tr>
      <td>${formatTimestamp(item.timestamp)}</td>
      <td>${escapeHtml(item.name)}</td>
      <td>${escapeHtml(item.course)}</td>
      <td>${escapeHtml(item.year)}</td>
      <td>${formatReason(item.reason)}</td>
      <td>${item.token.substring(0, 8)}...</td>
    </tr>
  `).join('');
}

// Enhanced updateDeviceTable function with clickable device info
function updateDeviceTable() {
  const tbody = document.getElementById('device-fingerprints');
  
  if (deviceFingerprints.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">No device data available</td></tr>';
    return;
  }
  
  tbody.innerHTML = deviceFingerprints.map(item => `
    <tr>
      <td>${item.fingerprint_hash.substring(0, 12)}...</td>
      <td>${formatDateTime(item.first_seen)}</td>
      <td>${formatDateTime(item.last_seen)}</td>
      <td>${item.usage_count}</td>
      <td>
        <span 
          style="cursor: pointer; color: #007bff; text-decoration: underline;" 
          onclick="showDetailedDeviceInfo('${escapeHtml(item.device_info)}')"
          title="Click for detailed device information"
        >
          ${getDeviceInfo(item.device_info)}
        </span>
      </td>
    </tr>
  `).join('');
}

function formatTimestamp(timestamp) {
  return new Date(timestamp * 1000).toLocaleString();
}

function formatDateTime(isoString) {
  return new Date(isoString).toLocaleString();
}

function formatReason(reason) {
  const reasons = {
    'invalid_token': 'Invalid Token',
    'already_used': 'Token Used',
    'fingerprint_blocked': 'Device Blocked'
  };
  return reasons[reason] || reason;
}

function getDeviceInfo(deviceInfoStr) {
  try {
    if (!deviceInfoStr) return 'Unknown';
    
    const info = JSON.parse(deviceInfoStr);
    
    // Handle new enhanced device signature format
    if (info.device_signature) {
      const device = info.device_signature;
      
      // Create a readable device string
      let deviceString = '';
      
      // Prioritize brand and model for mobile devices
      if (device.type === 'mobile' || device.type === 'tablet') {
        if (device.brand && device.brand !== 'unknown') {
          deviceString += device.brand.charAt(0).toUpperCase() + device.brand.slice(1);
        }
        
        if (device.model && device.model !== 'unknown') {
          deviceString += ` ${device.model}`;
        }
        
        // Add OS for mobile devices
        if (device.os && device.os !== 'unknown') {
          deviceString += ` (${device.os}`;
          if (device.os_version) {
            deviceString += ` ${device.os_version}`;
          }
          deviceString += ')';
        }
      } else {
        // For desktop devices, show OS and browser
        if (device.os && device.os !== 'unknown') {
          deviceString += device.os.charAt(0).toUpperCase() + device.os.slice(1);
        }
        
        if (device.browser && device.browser !== 'unknown') {
          deviceString += ` ${device.browser.charAt(0).toUpperCase() + device.browser.slice(1)}`;
          if (device.browser_version) {
            deviceString += ` ${device.browser_version}`;
          }
        }
      }
      
      if (deviceString.trim()) {
        return deviceString.trim();
      }
    }
    
    // Enhanced fallback logic
    if (info.user_agent) {
      const ua = info.user_agent.toLowerCase();
      
      // Better mobile device detection
      if (ua.includes('iphone')) {
        return 'iPhone (iOS)';
      } else if (ua.includes('ipad')) {
        return 'iPad (iOS)';
      } else if (ua.includes('android')) {
        // Try to extract Android device info
        if (ua.includes('samsung')) {
          return 'Samsung Android';
        } else if (ua.includes('huawei')) {
          return 'Huawei Android';
        } else if (ua.includes('xiaomi')) {
          return 'Xiaomi Android';
        } else if (ua.includes('oppo')) {
          return 'OPPO Android';
        } else if (ua.includes('vivo')) {
          return 'Vivo Android';
        } else if (ua.includes('oneplus')) {
          return 'OnePlus Android';
        } else {
          return 'Android Device';
        }
      } else if (ua.includes('windows')) {
        if (ua.includes('chrome')) {
          return 'Windows Chrome';
        } else if (ua.includes('firefox')) {
          return 'Windows Firefox';
        } else if (ua.includes('edge')) {
          return 'Windows Edge';
        } else {
          return 'Windows PC';
        }
      } else if (ua.includes('mac') && !ua.includes('iphone') && !ua.includes('ipad')) {
        if (ua.includes('chrome')) {
          return 'Mac Chrome';
        } else if (ua.includes('safari')) {
          return 'Mac Safari';
        } else if (ua.includes('firefox')) {
          return 'Mac Firefox';
        } else {
          return 'Mac Computer';
        }
      } else if (ua.includes('linux')) {
        return 'Linux Desktop';
      }
    }
    
    // Don't show raw platform info - return generic instead
    return 'Unknown Device';
           
  } catch (error) {
    console.error('Error parsing device info:', error);
    return 'Unknown Device';
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

async function exportData() {
  try {
    const response = await fetch('/api/export_data');
    const data = await response.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_data_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification('Data exported successfully', 'success');
  } catch (error) {
    console.error('Error exporting data:', error);
    showNotification('Error exporting data', 'error');
  }
}

function clearOldData() {
  if (confirm('Are you sure you want to clear old data? This action cannot be undone.')) {
    showNotification('Feature not implemented yet', 'info');
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // Add some basic styling
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 10px 20px;
    border-radius: 4px;
    color: white;
    z-index: 1000;
    font-weight: bold;
  `;
  
  // Set background color based on type
  switch(type) {
    case 'success':
      notification.style.backgroundColor = '#28a745';
      break;
    case 'error':
      notification.style.backgroundColor = '#dc3545';
      break;
    case 'info':
      notification.style.backgroundColor = '#17a2b8';
      break;
    default:
      notification.style.backgroundColor = '#6c757d';
  }
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    if (document.body.contains(notification)) {
      document.body.removeChild(notification);
    }
  }, 3000);
}

async function createAttendanceSession() {
  try {
    const btn = document.getElementById('create-session-btn');
    const status = document.getElementById('session-status');
    
    // Simple session creation - starts now, ends in 2 hours
    const now = new Date();
    const endTime = new Date(now.getTime() + (2 * 60 * 60 * 1000)); // 2 hours from now
    
    const sessionData = {
      session_name: `Session ${now.toLocaleDateString()} ${now.toLocaleTimeString()}`,
      start_time: now.toISOString(),
      end_time: endTime.toISOString()
    };
    
    btn.disabled = true;
    btn.textContent = 'Creating...';
    status.textContent = 'Creating attendance session...';
    
    const response = await fetch('/api/create_session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(sessionData)
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      status.textContent = `Session active until ${endTime.toLocaleTimeString()}`;
      showNotification('Attendance session created successfully!', 'success');
    } else {
      throw new Error(result.message || 'Failed to create session');
    }
    
  } catch (error) {
    console.error('Error creating session:', error);
    document.getElementById('session-status').textContent = 'Error creating session';
    showNotification('Error creating attendance session', 'error');
  } finally {
    const btn = document.getElementById('create-session-btn');
    btn.disabled = false;
    btn.textContent = 'Create Attendance Session';
  }
}