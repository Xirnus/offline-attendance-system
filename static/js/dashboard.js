// Global variables
let attendanceData = [];
let deniedAttempts = [];
let deviceFingerprints = [];
let sessionProfiles = [];
let lastUpdateTime = 0;
let loadDataTimeout;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
  loadSettings();
  loadData();
  loadSessionProfiles();
  setupEventListeners();
  checkSessionStatusWithExpiration();
  
  // Refresh intervals
  setInterval(loadData, 15000);
  setInterval(checkSessionStatusWithExpiration, 60000);

  // Refresh when tab becomes active
  document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
      setTimeout(() => {
        loadData();
        checkSessionStatusWithExpiration();
      }, 500);
    }
  });
});

// Load session profiles
async function loadSessionProfiles() {
  try {
    const response = await fetch('/api/session_profiles');
    const data = await response.json();
    sessionProfiles = data.profiles || [];
    console.log('Loaded session profiles:', sessionProfiles);
  } catch (error) {
    console.error('Error loading session profiles:', error);
    sessionProfiles = [];
  }
}

// Load data with debouncing
async function loadData() {
  if (loadDataTimeout) clearTimeout(loadDataTimeout);
  
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
      
      const hasNewData = 
        newAttendanceData.length !== attendanceData.length ||
        newDeniedAttempts.length !== deniedAttempts.length ||
        newDeviceFingerprints.length !== deviceFingerprints.length;
      
      attendanceData = newAttendanceData;
      deniedAttempts = newDeniedAttempts;
      deviceFingerprints = newDeviceFingerprints;
      
      updateStatistics();
      updateAttendanceTable();
      updateDeniedTable();
      updateDeviceTable();
      
      if (hasNewData && lastUpdateTime > 0) {
        showNotification('New activity detected!', 'info');
      }
      
      lastUpdateTime = Date.now();
      
    } catch (error) {
      console.error('Error loading data:', error);
    }
  }, 100);
}

function setupEventListeners() {
  const elements = {
    'generate-btn': generateQR,
    'save-settings': saveSettings,
    'refresh-data': loadData,
    'export-data': exportData,
    'clear-old-data': clearOldData
  };
  Object.entries(elements).forEach(([id, handler]) => {
    const element = document.getElementById(id);
    if (element) element.addEventListener('click', handler);
  });
  
  // Export & Reports Event Listeners
  const exportElements = {
    'export-pdf': exportPDF,
    'export-excel': exportExcel,
    'export-csv': exportCSV,
    'generate-report': generateCustomReport,
    'send-email-report': sendEmailReport,
    'view-analytics': viewAnalytics,
    'setup-schedule': setupScheduledReports
  };

  Object.entries(exportElements).forEach(([id, handler]) => {
    const element = document.getElementById(id);
    if (element) element.addEventListener('click', handler);
  });
  
  // Session event listeners
  const createSessionBtn = document.getElementById('create-session-btn');
  const stopSessionBtn = document.getElementById('stop-session-btn');
  
  if (createSessionBtn) {
    createSessionBtn.addEventListener('click', function(e) {
      e.preventDefault();
      showSessionCreationModal();
    });
  }
  
  if (stopSessionBtn) {
    stopSessionBtn.addEventListener('click', function(e) {
      e.preventDefault();
      if (confirm('Are you sure you want to stop the current session?')) {
        stopSession();
      }
    });
  }
}

function showSessionCreationModal() {
  const modalHTML = `
    <div id="createSessionModal" style="
      position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
      background: rgba(0,0,0,0.5); display: flex; justify-content: center; 
      align-items: center; z-index: 1000;
    ">
      <div style="
        background: white; padding: 30px; border-radius: 10px; 
        width: 90%; max-width: 600px; max-height: 80vh; overflow-y: auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
      ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
          <h3 style="margin: 0; color: #333;">Create Attendance Session</h3>
          <button onclick="closeCreateSessionModal()" style="
            border: none; background: #ccc; border-radius: 50%; 
            width: 30px; height: 30px; cursor: pointer; font-size: 18px;
          ">×</button>
        </div>
        
        <div style="margin-bottom: 20px;">
          <label style="display: block; margin-bottom: 10px; font-weight: bold;">Session Type:</label>
          <div style="display: flex; gap: 10px; margin-bottom: 15px;">
            <button id="manualSessionBtn" onclick="selectSessionType('manual')" style="
              padding: 10px 20px; border: 2px solid #007bff; background: #007bff; 
              color: white; border-radius: 5px; cursor: pointer;
            ">Manual Setup</button>
            <button id="profileSessionBtn" onclick="selectSessionType('profile')" style="
              padding: 10px 20px; border: 2px solid #007bff; background: white; 
              color: #007bff; border-radius: 5px; cursor: pointer;
            ">Use Profile</button>
          </div>
        </div>
        
        <!-- Manual Session Form -->
        <div id="manualSessionForm" style="display: block;">
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Session Name:</label>
            <input type="text" id="manualSessionName" placeholder="Enter session name" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">End Time:</label>
            <input type="time" id="manualEndTime" value="${getDefaultEndTime()}" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
        </div>
        
        <!-- Profile Session Form -->
        <div id="profileSessionForm" style="display: none;">
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Select Profile:</label>
            <select id="profileSelect" onchange="updateProfilePreview()" style="
              width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;
            ">
              <option value="">Choose a session profile...</option>
              ${sessionProfiles.map(profile => `
                <option value="${profile.id}">${escapeHtml(profile.profile_name)} - ${escapeHtml(profile.room_type.replace('-', ' '))}</option>
              `).join('')}
            </select>
          </div>
          
          <div id="profilePreview" style="
            background: #f8f9fa; padding: 15px; border-radius: 5px; 
            margin-bottom: 15px; display: none;
          ">
            <h4 style="margin-bottom: 10px; color: #555;">Profile Details:</h4>
            <div id="profileDetails"></div>
          </div>
          
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Session Name (Optional):</label>
            <input type="text" id="profileSessionName" placeholder="Leave empty to use profile name + date" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
          
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">End Time:</label>
            <input type="time" id="profileEndTime" value="${getDefaultEndTime()}" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
        </div>
        
        <div style="display: flex; gap: 10px; justify-content: flex-end; margin-top: 20px;">
          <button onclick="closeCreateSessionModal()" style="
            background: #6c757d; color: white; padding: 10px 20px; 
            border: none; border-radius: 3px; cursor: pointer;
          ">Cancel</button>
          <button onclick="executeCreateSession()" style="
            background: #28a745; color: white; padding: 10px 20px; 
            border: none; border-radius: 3px; cursor: pointer;
          ">Create Session</button>
        </div>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function selectSessionType(type) {
  const manualBtn = document.getElementById('manualSessionBtn');
  const profileBtn = document.getElementById('profileSessionBtn');
  const manualForm = document.getElementById('manualSessionForm');
  const profileForm = document.getElementById('profileSessionForm');
  
  if (type === 'manual') {
    manualBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: #007bff; color: white; border-radius: 5px; cursor: pointer;';
    profileBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    manualForm.style.display = 'block';
    profileForm.style.display = 'none';
  } else {
    profileBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: #007bff; color: white; border-radius: 5px; cursor: pointer;';
    manualBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    profileForm.style.display = 'block';
    manualForm.style.display = 'none';
  }
}

function updateProfilePreview() {
  const profileSelect = document.getElementById('profileSelect');
  const profilePreview = document.getElementById('profilePreview');
  const profileDetails = document.getElementById('profileDetails');
  const profileSessionName = document.getElementById('profileSessionName');
  
  const selectedProfileId = profileSelect.value;
  
  if (!selectedProfileId) {
    profilePreview.style.display = 'none';
    return;
  }
  
  const profile = sessionProfiles.find(p => p.id == selectedProfileId);
  
  if (profile) {
    profileDetails.innerHTML = `
      <p><strong>Room:</strong> ${escapeHtml(profile.profile_name)}</p>
      <p><strong>Type:</strong> ${escapeHtml(profile.room_type.replace('-', ' ').toUpperCase())}</p>
      <p><strong>Building:</strong> ${escapeHtml(profile.building || 'Not specified')}</p>
      <p><strong>Capacity:</strong> ${profile.capacity || 'Not specified'} students</p>
    `;
    profileSessionName.placeholder = `${profile.profile_name} - ${new Date().toLocaleDateString()}`;
    profilePreview.style.display = 'block';
  }
}

function closeCreateSessionModal() {
  const modal = document.getElementById('createSessionModal');
  if (modal) modal.remove();
}

async function executeCreateSession() {
  const manualForm = document.getElementById('manualSessionForm');
  let sessionName, endTime, profileId = null;
  
  if (manualForm.style.display !== 'none') {
    // Manual session
    sessionName = document.getElementById('manualSessionName').value;
    endTime = document.getElementById('manualEndTime').value;
    
    if (!sessionName || !endTime) {
      alert('Please fill in all fields');
      return;
    }
  } else {
    // Profile-based session
    const profileSelect = document.getElementById('profileSelect');
    profileId = profileSelect.value;
    sessionName = document.getElementById('profileSessionName').value;
    endTime = document.getElementById('profileEndTime').value;
    
    if (!profileId || !endTime) {
      alert('Please select a profile and set end time');
      return;
    }
    
    if (!sessionName) {
      const profile = sessionProfiles.find(p => p.id == profileId);
      sessionName = `${profile.profile_name} - ${new Date().toLocaleDateString()}`;
    }
  }
  
  // Create end time
  const now = new Date();
  const endDateTime = new Date();
  const [hours, minutes] = endTime.split(':');
  endDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
  
  if (endDateTime <= now) {
    endDateTime.setDate(endDateTime.getDate() + 1);
  }
  
  closeCreateSessionModal();
  createSession(sessionName, now.toISOString(), endDateTime.toISOString(), profileId);
}

function createSession(sessionName, startTime, endTime, profileId = null) {
  const createBtn = document.getElementById('create-session-btn');
  const originalText = createBtn.textContent;
  createBtn.disabled = true;
  createBtn.textContent = 'Creating Session...';
  
  const requestBody = {
    session_name: sessionName,
    start_time: startTime,
    end_time: endTime
  };
  
  if (profileId) requestBody.profile_id = parseInt(profileId);
  
  fetch('/api/create_session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody)
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success') {
      let message = 'Session created successfully';
      if (profileId) {
        const profile = sessionProfiles.find(p => p.id == profileId);
        if (profile) message += ` using ${profile.profile_name} profile`;
      }
      showNotification(message, 'success');
      
      const sessionData = {
        session_name: sessionName,
        start_time: startTime,
        end_time: endTime,
        profile_id: profileId
      };
      updateButtonVisibility(true, sessionName);
      displaySessionDetails(sessionData);
    } else {
      showNotification('Error creating session: ' + data.message, 'error');
      createBtn.disabled = false;
      createBtn.textContent = originalText;
    }
  })
  .catch(error => {
    showNotification('Error creating session', 'error');
    console.error('Error:', error);
    createBtn.disabled = false;
    createBtn.textContent = originalText;
  });
}

function stopSession() {
  const stopBtn = document.getElementById('stop-session-btn');
  if (!stopBtn) return;
  
  const originalText = stopBtn.textContent;
  stopBtn.disabled = true;
  stopBtn.textContent = 'Stopping...';
  
  fetch('/api/stop_session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  })
  .then(response => response.json())
  .then(data => {
    if (data.status === 'success' || data.success) {
      const absentCount = data.absent_marked || 0;
      const message = absentCount > 0 
        ? `Session stopped successfully. ${absentCount} students marked absent.`
        : 'Session stopped successfully';
      
      showNotification(message, 'success');
      updateButtonVisibility(false, '');
      setTimeout(() => loadData(), 500);
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
  
  if (hasActiveSession) {
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
    if (sessionStatus) sessionStatus.innerHTML = '<span>No active session</span>';
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
}

function displaySessionDetails(session) {
  const sessionDetailsElement = document.getElementById('session-details');
  if (!sessionDetailsElement) return;
  
  try {
    const startTime = new Date(session.start_time);
    const endTime = new Date(session.end_time);
    const now = new Date();
    
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
    
    let detailsHTML = `
      Started: ${startTime.toLocaleString()}<br>
      Ends: ${endTime.toLocaleString()}<br>
    `;
    
    if (session.profile_id) {
      const profile = sessionProfiles.find(p => p.id == session.profile_id);
      if (profile) {
        detailsHTML += `Room: ${escapeHtml(profile.profile_name)} (${escapeHtml(profile.room_type.replace('-', ' '))})<br>`;
      }
    }
    
    detailsHTML += `
      <span style="color: ${timeRemaining > 0 ? '#28a745' : '#dc3545'};">
        ${timeRemainingText}
      </span>
    `;
    
    sessionDetailsElement.innerHTML = detailsHTML;
    
  } catch (error) {
    console.error('Error in displaySessionDetails:', error);
    sessionDetailsElement.innerHTML = 'Error loading session details';
  }
}

function checkSessionStatusWithExpiration() {
  fetch('/api/session_status')
  .then(response => response.json())
  .then(data => {
    if (data.active_session) {
      const endTime = new Date(data.active_session.end_time);
      const now = new Date();
      
      if (endTime <= now) {
        // Session expired, auto-stop
        fetch('/api/stop_session', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(stopData => {
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

function getDefaultEndTime() {
  const now = new Date();
  now.setHours(now.getHours() + 2);
  return now.toTimeString().slice(0, 5);
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
      headers: { 'Content-Type': 'application/json' },
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
      if (device.os_version) details += ` ${device.os_version}`;
      details += `<br>Browser: ${device.browser || 'Unknown'}`;
      if (device.browser_version) details += ` ${device.browser_version}`;
      details += `<br><br>`;
    }
    
    details += `<strong>Technical Info:</strong><br>`;
    details += `Screen: ${info.screen_resolution || 'Unknown'}<br>`;
    details += `Timezone: ${info.timezone || 'Unknown'}<br>`;
    details += `Language: ${info.language || 'Unknown'}<br>`;
    details += `Platform: ${info.platform || 'Unknown'}<br>`;
    
    if (info.color_depth) details += `Color Depth: ${info.color_depth}<br>`;
    if (info.pixel_ratio) details += `Pixel Ratio: ${info.pixel_ratio}<br>`;
    if (info.touch_support !== undefined) details += `Touch Support: ${info.touch_support ? 'Yes' : 'No'}<br>`;
    
    showDeviceModal(details);
    
  } catch (error) {
    console.error('Error showing device details:', error);
  }
}

function showDeviceModal(content) {
  const modal = document.createElement('div');
  modal.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5); display: flex; justify-content: center;
    align-items: center; z-index: 1000;
  `;
  
  const modalContent = document.createElement('div');
  modalContent.style.cssText = `
    background: white; padding: 20px; border-radius: 8px;
    max-width: 500px; max-height: 80vh; overflow-y: auto;
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
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.remove();
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
    
    if (info.device_signature) {
      const device = info.device_signature;
      let deviceString = '';
      
      if (device.type === 'mobile' || device.type === 'tablet') {
        if (device.brand && device.brand !== 'unknown') {
          deviceString += device.brand.charAt(0).toUpperCase() + device.brand.slice(1);
        }
        if (device.model && device.model !== 'unknown') {
          deviceString += ` ${device.model}`;
        }
        if (device.os && device.os !== 'unknown') {
          deviceString += ` (${device.os}`;
          if (device.os_version) deviceString += ` ${device.os_version}`;
          deviceString += ')';
        }
      } else {
        if (device.os && device.os !== 'unknown') {
          deviceString += device.os.charAt(0).toUpperCase() + device.os.slice(1);
        }
        if (device.browser && device.browser !== 'unknown') {
          deviceString += ` ${device.browser.charAt(0).toUpperCase() + device.browser.slice(1)}`;
          if (device.browser_version) deviceString += ` ${device.browser_version}`;
        }
      }
      
      if (deviceString.trim()) return deviceString.trim();
    }
    
    if (info.user_agent) {
      const ua = info.user_agent.toLowerCase();
      
      if (ua.includes('iphone')) return 'iPhone (iOS)';
      if (ua.includes('ipad')) return 'iPad (iOS)';
      if (ua.includes('android')) {
        const brands = ['samsung', 'huawei', 'xiaomi', 'oppo', 'vivo', 'oneplus'];
        for (const brand of brands) {
          if (ua.includes(brand)) return `${brand.charAt(0).toUpperCase() + brand.slice(1)} Android`;
        }
        return 'Android Device';
      }
      if (ua.includes('windows')) {
        const browsers = ['chrome', 'firefox', 'edge'];
        for (const browser of browsers) {
          if (ua.includes(browser)) return `Windows ${browser.charAt(0).toUpperCase() + browser.slice(1)}`;
        }
        return 'Windows PC';
      }
      if (ua.includes('mac') && !ua.includes('iphone') && !ua.includes('ipad')) {
        const browsers = ['chrome', 'safari', 'firefox'];
        for (const browser of browsers) {
          if (ua.includes(browser)) return `Mac ${browser.charAt(0).toUpperCase() + browser.slice(1)}`;
        }
        return 'Mac Computer';
      }
      if (ua.includes('linux')) return 'Linux Desktop';
    }
    
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
  notification.textContent = message;
  
  const colors = {
    success: '#28a745',
    error: '#dc3545',
    info: '#17a2b8',
    default: '#6c757d'
  };
  
  notification.style.cssText = `
    position: fixed; top: 20px; right: 20px; padding: 10px 20px;
    border-radius: 4px; color: white; z-index: 1000; font-weight: bold;
    background-color: ${colors[type] || colors.default};
  `;
  
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

// Export and reporting functions
async function exportPDF() {
  try {
    showNotification('Generating PDF report...', 'info');
    const reportType = document.getElementById('report-type').value;
    const response = await fetch(`/api/export/pdf?type=${reportType}`);
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_report_${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showNotification('PDF report downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate PDF report');
    }
  } catch (error) {
    console.error('Error exporting PDF:', error);
    showNotification('Error generating PDF report', 'error');
  }
}

async function exportExcel() {
  try {
    showNotification('Generating Excel report...', 'info');
    const response = await fetch('/api/export/excel');
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_data_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showNotification('Excel report downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate Excel report');
    }
  } catch (error) {
    console.error('Error exporting Excel:', error);
    showNotification('Error generating Excel report', 'error');
  }
}

async function exportCSV() {
  try {
    showNotification('Generating CSV export...', 'info');
    const response = await fetch('/api/export/csv?type=all');
    
    if (response.ok) {
      const result = await response.json();
      if (result.files) {
        showNotification(`CSV files generated: ${result.files.length} files`, 'success');
        // For 'all' type, we get info about generated files
        console.log('Generated CSV files:', result.files);
      } else {
        // Single file download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attendance_data_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        showNotification('CSV export downloaded successfully', 'success');
      }
    } else {
      throw new Error('Failed to generate CSV export');
    }
  } catch (error) {
    console.error('Error exporting CSV:', error);
    showNotification('Error generating CSV export', 'error');
  }
}

async function generateCustomReport() {
  try {
    const reportType = document.getElementById('report-type').value;
    showNotification(`Generating ${reportType} report...`, 'info');
    
    // For now, use PDF export with selected type
    const response = await fetch(`/api/export/pdf?type=${reportType}`);
    
    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_${reportType}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showNotification(`${reportType} report downloaded successfully`, 'success');
    } else {
      throw new Error('Failed to generate custom report');
    }
  } catch (error) {
    console.error('Error generating custom report:', error);
    showNotification('Error generating custom report', 'error');
  }
}

async function sendEmailReport() {
  try {
    const recipientEmail = document.getElementById('recipient-email').value;
    const reportType = document.getElementById('email-report-type').value;
    
    if (!recipientEmail) {
      showNotification('Please enter recipient email address', 'error');
      return;
    }
    
    if (!isValidEmail(recipientEmail)) {
      showNotification('Please enter a valid email address', 'error');
      return;
    }
    
    showNotification('Sending email report...', 'info');
    
    const response = await fetch('/api/reports/email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        recipient_email: recipientEmail,
        report_type: reportType
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification('Email report sent successfully', 'success');
      document.getElementById('recipient-email').value = ''; // Clear input
    } else {
      throw new Error(result.error || 'Failed to send email report');
    }
  } catch (error) {
    console.error('Error sending email report:', error);
    showNotification('Error sending email report', 'error');
  }
}

async function viewAnalytics() {
  try {
    showNotification('Loading analytics...', 'info');
    const response = await fetch('/api/reports/analytics');
    
    if (response.ok) {
      const analytics = await response.json();
      displayAnalytics(analytics);
      document.getElementById('analytics-preview').classList.remove('hidden');
      showNotification('Analytics loaded successfully', 'success');
    } else {
      throw new Error('Failed to load analytics');
    }
  } catch (error) {
    console.error('Error loading analytics:', error);
    showNotification('Error loading analytics', 'error');
  }
}

function displayAnalytics(analytics) {
  const content = document.getElementById('analytics-content');
  
  let html = '<h4>Attendance Overview</h4>';
  html += '<div class="analytics-stats">';
  
  // Overview stats
  const overview = analytics.overview;
  html += `
    <div class="analytics-stat">
      <h4>Total Students</h4>
      <div class="value">${overview.total_students}</div>
    </div>
    <div class="analytics-stat">
      <h4>Total Sessions</h4>
      <div class="value">${overview.total_sessions}</div>
    </div>
    <div class="analytics-stat">
      <h4>Total Check-ins</h4>
      <div class="value">${overview.total_checkins}</div>
    </div>
    <div class="analytics-stat">
      <h4>Active Sessions</h4>
      <div class="value">${overview.active_sessions}</div>
    </div>
  `;
  
  html += '</div>';
  
  // Course breakdown
  if (analytics.course_breakdown && Object.keys(analytics.course_breakdown).length > 0) {
    html += '<h4>Students by Course</h4>';
    html += '<div class="analytics-stats">';
    
    for (const [course, data] of Object.entries(analytics.course_breakdown)) {
      html += `
        <div class="analytics-stat">
          <h4>${course}</h4>
          <div class="value">${data.students} students</div>
          <small>${data.checkins} check-ins</small>
        </div>
      `;
    }
    
    html += '</div>';
  }
  
  // Top attendance rates
  if (analytics.attendance_rates && Object.keys(analytics.attendance_rates).length > 0) {
    html += '<h4>Top Attendance Rates</h4>';
    html += '<table style="width: 100%; margin-top: 10px;">';
    html += '<tr><th>Student</th><th>Rate</th><th>Present</th><th>Absent</th></tr>';
    
    const sortedRates = Object.entries(analytics.attendance_rates)
      .sort(([,a], [,b]) => b.rate - a.rate)
      .slice(0, 10); // Top 10
    
    for (const [studentId, data] of sortedRates) {
      html += `
        <tr>
          <td>${data.name}</td>
          <td>${data.rate}%</td>
          <td>${data.present}</td>
          <td>${data.absent}</td>
        </tr>
      `;
    }
    
    html += '</table>';
  }
  
  content.innerHTML = html;
}

async function setupScheduledReports() {
  try {
    const email = document.getElementById('schedule-email').value;
    const frequency = document.getElementById('schedule-frequency').value;
    const time = document.getElementById('schedule-time').value;
    
    if (!email) {
      showNotification('Please enter recipient email address', 'error');
      return;
    }
    
    if (!isValidEmail(email)) {
      showNotification('Please enter a valid email address', 'error');
      return;
    }
    
    if (!time) {
      showNotification('Please select a time for scheduled reports', 'error');
      return;
    }
    
    showNotification('Setting up scheduled reports...', 'info');
    
    const response = await fetch('/api/reports/schedule', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        recipient_email: email,
        frequency: frequency,
        time: time,
        report_type: 'pdf'
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(`Scheduled ${frequency} reports set up successfully`, 'success');
      // Clear form
      document.getElementById('schedule-email').value = '';
      document.getElementById('schedule-time').value = '09:00';
    } else {
      throw new Error(result.error || 'Failed to setup scheduled reports');
    }
  } catch (error) {
    console.error('Error setting up scheduled reports:', error);
    showNotification('Error setting up scheduled reports', 'error');
  }
}

function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}