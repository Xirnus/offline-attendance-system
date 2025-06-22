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
  
  // More frequent auto-refresh for better real-time updates
  setInterval(loadData, 5000); // Refresh every 5 seconds

  // Also add visibility change listener to refresh when tab becomes active
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      loadData();
    }
  });
});

function setupEventListeners() {
  document.getElementById('generate-btn').addEventListener('click', generateQR);
  document.getElementById('save-settings').addEventListener('click', saveSettings);
  document.getElementById('refresh-data').addEventListener('click', loadData);
  document.getElementById('export-data').addEventListener('click', exportData);
  document.getElementById('clear-old-data').addEventListener('click', clearOldData);
  document.getElementById('create-session-btn').addEventListener('click', createAttendanceSession);
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