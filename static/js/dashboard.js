
// Global variables
let attendanceData = [];
let deniedAttempts = [];
let deviceFingerprints = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
  loadSettings();
  loadData();
  setupEventListeners();
  
  // Auto-refresh data every 30 seconds
  setInterval(loadData, 30000);
});

function setupEventListeners() {
  document.getElementById('generate-btn').addEventListener('click', generateQR);
  document.getElementById('save-settings').addEventListener('click', saveSettings);
  document.getElementById('refresh-data').addEventListener('click', loadData);
  document.getElementById('export-data').addEventListener('click', exportData);
  document.getElementById('clear-old-data').addEventListener('click', clearOldData);
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
    
    attendanceData = await attendanceRes.json();
    deniedAttempts = await deniedRes.json();
    deviceFingerprints = await devicesRes.json();
    
    updateStatistics();
    updateAttendanceTable();
    updateDeniedTable();
    updateDeviceTable();
  } catch (error) {
    console.error('Error loading data:', error);
  }
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
      <td>${getDeviceInfo(item.device_info)}</td>
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

function updateDeviceTable() {
  const tbody = document.getElementById('device-fingerprints');
  
  if (deviceFingerprints.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">No device data available</td></tr>';
    return;
  }
  
  tbody.innerHTML = deviceFingerprints.map(item => `
    <tr>
      <td>${item.fingerprint_hash}</td>
      <td>${formatDateTime(item.first_seen)}</td>
      <td>${formatDateTime(item.last_seen)}</td>
      <td>${item.usage_count}</td>
      <td>${getDeviceInfo(item.device_info)}</td>
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
    return info.platform || info.userAgent?.split(' ')[0] || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

function escapeHtml(text) {
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
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    document.body.removeChild(notification);
  }, 3000);
}