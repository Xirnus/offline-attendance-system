// Global variables
let attendanceData = [];
let deniedAttempts = [];
let sessionProfiles = [];
let lastUpdateTime = 0;
let loadDataTimeout;
let classList = [];
let currentToken = null;
let autoRegenerateEnabled = true;

// Track previous data to detect actual new data
let previousAttendanceCount = 0;
let previousDeniedCount = 0;

// Track token regeneration to prevent spam
let lastTokenRegeneratedTime = 0;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
  loadSettings();
  loadSessionProfiles();
  setupEventListeners();
  setupSettingsEventListeners();
  checkSessionStatusWithExpiration();
  
  // Refresh intervals
  setInterval(loadData, 5000);
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

// Helper to get current session ID from backend
async function getCurrentSessionId() {
  try {
    const res = await fetch('/api/session_status');
    const data = await res.json();
    console.log('Session status response:', data); // Debug log
    if (data && data.active_session && data.active_session.id) {
      console.log('Found active session ID:', data.active_session.id); // Debug log
      return data.active_session.id;
    }
    console.log('No active session found in response'); // Debug log
  } catch (e) {
    console.error('Error getting session ID:', e); // Debug log
  }
  return null;
}

// Override loadData to always fetch fresh data from server
function loadData() {
  if (loadDataTimeout) clearTimeout(loadDataTimeout);

  loadDataTimeout = setTimeout(async () => {
    try {
      // Get the current active session ID
      const sessionId = await getCurrentSessionId();
      console.log('Current session ID:', sessionId);

      // Always fetch fresh data from backend to ensure real-time updates
      const [attendanceRes, deniedRes] = await Promise.all([
        fetchWithLoading('/api/attendances'),
        fetchWithLoading('/api/denied')
      ]);
      
      console.log('Raw data counts:', {
        attendances: attendanceRes?.length || 0,
        denied: deniedRes?.length || 0
      });

      // Only show data from current active session (no data if no active session)
      if (sessionId) {
        attendanceData = (attendanceRes || []).filter(a => a.session_id == sessionId);
        deniedAttempts = (deniedRes || []).filter(d => d.session_id == sessionId);
        
        console.log('Filtered data counts for session', sessionId, ':', {
          attendances: attendanceData.length,
          denied: deniedAttempts.length
        });
      } else {
        // No active session - show no data
        attendanceData = [];
        deniedAttempts = [];
        console.log('No active session - showing no data');
      }
      
      // Check for actually new data by comparing counts
      const hasNewAttendance = attendanceData.length > previousAttendanceCount;
      const hasNewDenied = deniedAttempts.length > previousDeniedCount;
      const hasAnyNewData = hasNewAttendance || hasNewDenied;

      // Check if current token has been used
      if (currentToken && autoRegenerateEnabled) {
        checkTokenUsageAndRegenerate(attendanceData, deniedAttempts);
      }

      updateAttendanceTable();
      updateDeniedTable();
      updateStatisticsGrid(); 
      
      // Only show notification for actually new data, and only after initial load
      if (hasAnyNewData && lastUpdateTime > 0) {
        let notificationMessage = 'New activity detected: ';
        let activities = [];
        if (hasNewAttendance) activities.push('check-ins');
        if (hasNewDenied) activities.push('denied attempts');
        notificationMessage += activities.join(', ');
        
        showNotification(notificationMessage, 'info', 2000);
      }
      
      // Update previous counts for next comparison
      previousAttendanceCount = attendanceData.length;
      previousDeniedCount = deniedAttempts.length;
      
      lastUpdateTime = Date.now();
    } catch (error) {
      console.error('Error loading data:', error);
    }
  }, 100);
}

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

// Add this new function to update the statistics grid
function updateStatisticsGrid() {
  try {
    // Update total check-ins
    const totalAttendances = attendanceData.length;
    document.getElementById('total-attendances').textContent = totalAttendances;
    
    // Update failed attempts
    const totalDenied = deniedAttempts.length;
    document.getElementById('total-denied').textContent = totalDenied;
    
    // Update unique students count instead of devices
    const uniqueStudents = new Set(attendanceData.map(item => item.name)).size;
    document.getElementById('unique-devices').textContent = uniqueStudents;
    
    // Calculate recent activity (last hour)
    const oneHourAgo = Date.now() - (60 * 60 * 1000);
    const recentActivity = attendanceData.filter(item => {
      const itemTime = item.timestamp * 1000; // Convert to milliseconds
      return itemTime > oneHourAgo;
    }).length;
    document.getElementById('recent-activity').textContent = recentActivity;
    
  } catch (error) {
    console.error('Error updating statistics grid:', error);
  }
}

// New function to check token usage and auto-regenerate
function checkTokenUsageAndRegenerate(attendanceData, deniedAttempts) {
  if (!currentToken) return;
  
  // Check if current token appears in successful attendances
  const tokenUsedInAttendance = attendanceData.some(item => 
    item.token === currentToken
  );
  
  // Check if current token appears in denied attempts with "already_used" reason
  const tokenDeniedAsUsed = deniedAttempts.some(item => 
    item.token === currentToken && item.reason === 'already_used'
  );
  
  if (tokenUsedInAttendance || tokenDeniedAsUsed) {
    console.log('Current token has been used, auto-regenerating QR code...');
    
    // Only show notification if it's been more than 10 seconds since last regeneration
    const now = Date.now();
    if (now - lastTokenRegeneratedTime > 10000) {
      showNotification('Token used - Generating new QR code automatically', 'info', 2000);
      lastTokenRegeneratedTime = now;
    }
    
    // Auto-regenerate QR code
    setTimeout(() => {
      generateQR(true); // Pass true to indicate auto-regeneration
    }, 1000);
  }
}

function setupEventListeners() {
  addEventListeners({
    'generate-btn': () => generateQR(false),
    'save-settings': saveSettings,
    'refresh-data': loadData
  });

  // Add auto-regeneration toggle if it exists
  const autoRegenToggle = getElement('auto-regenerate-qr');
  if (autoRegenToggle) {
    autoRegenToggle.addEventListener('change', function() {
      autoRegenerateEnabled = this.checked;
      console.log('Auto-regeneration:', autoRegenerateEnabled ? 'enabled' : 'disabled');
    });
  }
  
  // Session event listeners
  addEventListenerSafe('create-session-btn', 'click', function(e) {
    e.preventDefault();
    showSessionCreationModal();
  });
  
  addEventListenerSafe('stop-session-btn', 'click', async function(e) {
    e.preventDefault();
    const confirmed = await customConfirm('Are you sure you want to stop the current session?', 'Stop Session');
    if (confirmed) {
      stopSession();
    }
  });
}

// Add manual student input UI to the right column

document.addEventListener('DOMContentLoaded', function() {
  const manualStudentForm = document.getElementById('manual-student-form');
  if (manualStudentForm) {
    manualStudentForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      
      const studentId = this.student_id.value.trim();
      const studentName = this.student_name.value.trim();
      const studentCourse = this.student_course.value.trim();
      const studentYear = this.student_year.value.trim();
      const messageBox = document.getElementById('manual-student-message');
      
      // Basic validation
      if (!studentId || !studentName) {
        messageBox.textContent = 'Student ID and Name are required.';
        messageBox.style.color = 'red';
        return;
      }
      
      messageBox.textContent = 'Adding student...';
      messageBox.style.color = '#007bff';
      
      try {
        // Send data to server
        const response = await fetch('/api/add_student_manual', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: studentId,
            student_name: studentName,
            student_course: studentCourse,
            student_year: studentYear
          })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
          messageBox.textContent = 'Student added successfully!';
          messageBox.style.color = 'green';
          
          // Optionally, clear the form
          this.reset();
        } else {
          throw new Error(result.message || 'Unknown error');
        }
      } catch (error) {
        console.error('Error adding student:', error);
        messageBox.textContent = 'Error adding student: ' + error.message;
        messageBox.style.color = 'red';
      }
    });
  }
});

document.addEventListener('DOMContentLoaded', function() {
  // Manual student input form handler
  const manualStudentForm = document.getElementById('manual-student-form');
  const manualStudentMessage = document.getElementById('manual-student-message');
  if (manualStudentForm) {
    manualStudentForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      if (manualStudentMessage) manualStudentMessage.textContent = '';
      const student_id = document.getElementById('manual-student-id').value.trim();
      const student_name = document.getElementById('manual-student-name').value.trim();
      const student_course = document.getElementById('manual-student-course').value.trim();
      const student_year = document.getElementById('manual-student-year').value.trim();
      if (!student_id || !student_name) {
        manualStudentMessage.textContent = 'Student ID and Name are required.';
        manualStudentMessage.style.color = '#b22222';
        return;
      }
      try {
        const res = await fetch('/api/manual_attendance', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id,
            student_name,
            student_course,
            student_year
          })
        });
        const data = await res.json();
        if (res.ok && data.success) {
          manualStudentMessage.textContent = 'Student attendance recorded!';
          manualStudentMessage.style.color = '#28a745';
          manualStudentForm.reset();
          loadData && loadData();
        } else {
          manualStudentMessage.textContent = data.message || 'Failed to record attendance.';
          manualStudentMessage.style.color = '#b22222';
        }
      } catch (err) {
        manualStudentMessage.textContent = 'Error connecting to server.';
        manualStudentMessage.style.color = '#b22222';
      }
    });
  }
});

async function showSessionCreationModal() {
  // Fetch class list for the dropdown
  if (classList.length === 0) {
    try {
      const res = await fetch('/api/optimized/classes');
      const data = await res.json();
      classList = data.classes || [];
    } catch (e) {
      classList = [];
    }
  }

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
            <button id="classSessionBtn" onclick="selectSessionType('class')" style="
              padding: 10px 20px; border: 2px solid #007bff; background: white; 
              color: #007bff; border-radius: 5px; cursor: pointer;
            ">Class</button>
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
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Allowed Minutes Before Late:</label>
            <input type="number" id="manualLateMinutes" min="1" max="120" value="15" 
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
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Allowed Minutes Before Late:</label>
            <input type="number" id="profileLateMinutes" min="1" max="120" value="15" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
        </div>

        <!-- Class Session Form -->
        <div id="classSessionForm" style="display: none;">
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Select Class:</label>
            <select id="classSelect" style="
              width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;
            ">
              <option value="">Choose a class...</option>
              ${classList.map(cls => `
                <option value="${cls.class_id}">${escapeHtml(`${cls.class_name} - ${cls.professor_name}`)}</option>
              `).join('')}
            </select>
          </div>
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">End Time:</label>
            <input type="time" id="classEndTime" value="${getDefaultEndTime()}" 
                   style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
          </div>
          <div style="margin-bottom: 15px;">
            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Allowed Minutes Before Late:</label>
            <input type="number" id="classLateMinutes" min="1" max="120" value="15" 
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
  // Default to manual
  selectSessionType('manual');
}

function selectSessionType(type) {
  const manualBtn = document.getElementById('manualSessionBtn');
  const profileBtn = document.getElementById('profileSessionBtn');
  const classBtn = document.getElementById('classSessionBtn');
  const manualForm = document.getElementById('manualSessionForm');
  const profileForm = document.getElementById('profileSessionForm');
  const classForm = document.getElementById('classSessionForm');
  
  if (type === 'manual') {
    manualBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: #007bff; color: white; border-radius: 5px; cursor: pointer;';
    profileBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    classBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    manualForm.style.display = 'block';
    profileForm.style.display = 'none';
    classForm.style.display = 'none';
  } else if (type === 'profile') {
    profileBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: #007bff; color: white; border-radius: 5px; cursor: pointer;';
    manualBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    classBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    profileForm.style.display = 'block';
    manualForm.style.display = 'none';
    classForm.style.display = 'none';
  } else if (type === 'class') {
    classBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: #007bff; color: white; border-radius: 5px; cursor: pointer;';
    manualBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    profileBtn.style.cssText = 'padding: 10px 20px; border: 2px solid #007bff; background: white; color: #007bff; border-radius: 5px; cursor: pointer;';
    classForm.style.display = 'block';
    manualForm.style.display = 'none';
    profileForm.style.display = 'none';
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
      <p><strong>Session Name:</strong> ${escapeHtml(profile.profile_name)}</p>
            <p><strong>Organizer:</strong> ${escapeHtml(profile.organizer || 'Not specified')}</p>
      <p><strong>Type:</strong> ${escapeHtml(profile.room_type.replace('-', ' ').toUpperCase())}</p>
      <p><strong>Venue:</strong> ${escapeHtml(profile.building || 'Not specified')}</p>
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
  const profileForm = document.getElementById('profileSessionForm');
  const classForm = document.getElementById('classSessionForm');
  let sessionName, endTime, profileId = null, classId = null, lateMinutes = 15;

  if (manualForm.style.display !== 'none') {
    // Manual session
    sessionName = document.getElementById('manualSessionName').value;
    endTime = document.getElementById('manualEndTime').value;
    lateMinutes = Number(document.getElementById('manualLateMinutes').value) || 15;
    if (!sessionName || !endTime) {
      await customAlert('Please fill in all fields', 'Missing Information');
      return;
    }
  } else if (profileForm.style.display !== 'none') {
    // Profile-based session
    const profileSelect = document.getElementById('profileSelect');
    profileId = profileSelect.value;
    sessionName = document.getElementById('profileSessionName').value;
    endTime = document.getElementById('profileEndTime').value;
    lateMinutes = Number(document.getElementById('profileLateMinutes').value) || 15;
    if (!profileId || !endTime) {
      await customAlert('Please select a profile and set end time', 'Missing Information');
      return;
    }
    if (!sessionName) {
      const profile = sessionProfiles.find(p => p.id == profileId);
      sessionName = `${profile.profile_name} - ${new Date().toLocaleDateString()}`;
    }
  } else if (classForm.style.display !== 'none') {
    // Class session
    const classSelect = document.getElementById('classSelect');
    classId = classSelect.value;
    endTime = document.getElementById('classEndTime').value;
    lateMinutes = Number(document.getElementById('classLateMinutes').value) || 15;
    if (!classId || !endTime) {
      await customAlert('Please select a class and set end time', 'Missing Information');
      return;
    }
    // Find display name for session name
    const cls = classList.find(c => c.class_id == classId);
    sessionName = cls ? `${cls.class_name} - ${cls.professor_name}` : classId;
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

  // Add class_id to request if class session
  createSession(sessionName, now.toISOString(), endDateTime.toISOString(), profileId, classId, lateMinutes);
}

function createSession(sessionName, startTime, endTime, profileId = null, classId = null, lateMinutes = 15) {
  const createBtn = document.getElementById('create-session-btn');
  const originalText = createBtn ? createBtn.textContent : '';
  if (createBtn) {
    createBtn.disabled = true;
    createBtn.textContent = 'Creating Session...';
  }

  const requestBody = {
    session_name: sessionName,
    start_time: startTime,
    end_time: endTime,
    late_minutes: lateMinutes
  };

  // Only send one of profile_id or class_table
  if (classId) {
    requestBody.class_table = classId;
    requestBody.profile_id = null;
  } else if (profileId) {
    requestBody.profile_id = parseInt(profileId);
  }

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
      if (classId) {
        const cls = classList.find(c => c.class_id == classId);
        if (cls) message += ` for class ${cls.class_name} - ${cls.professor_name}`;
      }
      showNotification(message, 'success');

      const sessionData = {
        session_name: sessionName,
        start_time: startTime,
        end_time: endTime,
        profile_id: profileId,
        class_table: classId,
        late_minutes: lateMinutes
      };
      updateButtonVisibility(true, sessionName);
      displaySessionDetails(sessionData);
    } else {
      showNotification('Error creating session: ' + data.message, 'error');
      if (createBtn) {
        createBtn.disabled = false;
        createBtn.textContent = originalText;
      }
    }
  })
  .catch(error => {
    showNotification('Error creating session', 'error');
    console.error('Error:', error);
    if (createBtn) {
      createBtn.disabled = false;
      createBtn.textContent = originalText;
    }
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
      const dataCleared = data.data_cleared || false;
      const clearedCounts = data.cleared_counts || {};
      
      let message = '';
      if (absentCount > 0) {
        message += `Session stopped successfully. ${absentCount} students marked absent.`;
      } else {
        message += 'Session stopped successfully.';
      }
      
      if (dataCleared) {
        message += ` All session data cleared: ${clearedCounts.attendances || 0} attendances, ${clearedCounts.denied_attempts || 0} failed attempts.`;
        
        // Clear the tables immediately since data was cleared
        document.getElementById('attendances').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No attendance data</td></tr>';
        document.getElementById('denied-attendances').innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No failed attempts</td></tr>';
        
        // Reset statistics grid
        document.getElementById('total-attendances').textContent = '0';
        document.getElementById('total-denied').textContent = '0';
        document.getElementById('unique-devices').textContent = '0';
        document.getElementById('recent-activity').textContent = '0';
      }
      
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
      // Remove file extension from sessionName for display
      let displaySessionName = sessionName.replace(/\.[^/.]+$/, '');
      sessionStatus.innerHTML = `
        <div class="modern-session-card">
          <div class="modern-session-title">Active Session</div>
          <strong>${displaySessionName}</strong>
          <div id="session-details">Loading session details...</div>
        </div>
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
    const lateMinutes = session.late_minutes !== undefined ? Number(session.late_minutes) : 15;
    const lateThreshold = new Date(startTime.getTime() + lateMinutes * 60000);

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

    let statusHTML = '';
    if (now >= lateThreshold && now < endTime) {
      statusHTML = `<span class="modern-session-status late">Late attendance is now active. Students will be marked late.</span>`;
    } else if (now < lateThreshold) {
      const mins = Math.ceil((lateThreshold - now) / 60000);
      statusHTML = `<span class="modern-session-status upcoming">Late attendance will be active in ${mins} min${mins !== 1 ? 's' : ''}.</span>`;
    } else if (now >= endTime) {
      statusHTML = `<span class="modern-session-status expired">Session expired</span>`;
    }

    let detailsHTML = '';
    detailsHTML += `<div class="modern-session-row"><span>Started:</span><span>${startTime.toLocaleString()}</span></div>`;
    detailsHTML += `<div class="modern-session-row"><span>Ends:</span><span>${endTime.toLocaleString()}</span></div>`;
    if (session.profile_id) {
      const profile = sessionProfiles.find(p => p.id == session.profile_id);
      if (profile) {
        detailsHTML += `<div class="modern-session-row"><span>Room:</span><span>${escapeHtml(profile.profile_name)} (${escapeHtml(profile.room_type.replace('-', ' '))})</span></div>`;
      }
    }
    detailsHTML += statusHTML;
    detailsHTML += `<div class="modern-session-timer">${timeRemainingText}</div>`;

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
          
          let message = '';
          if (stopData.absent_marked > 0) {
            message = `Session ended. ${stopData.absent_marked} students marked absent`;
          } else {
            message = 'Session automatically ended (expired)';
          }
          
          if (stopData.data_cleared) {
            const counts = stopData.cleared_counts || {};
            message += `. Data cleared: ${counts.attendances || 0} attendances, ${counts.denied_attempts || 0} failed attempts, ${counts.device_fingerprints || 0} devices`;
            
            // Clear the tables immediately since data was cleared
            document.getElementById('attendances').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No attendance data</td></tr>';
            document.getElementById('denied-attendances').innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No failed attempts</td></tr>';
            document.getElementById('device-fingerprints').innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No device data available</td></tr>';
            
            // Reset statistics grid
            document.getElementById('total-attendances').textContent = '0';
            document.getElementById('total-denied').textContent = '0';
            document.getElementById('unique-devices').textContent = '0';
            document.getElementById('recent-activity').textContent = '0';
          }
          
          showNotification(message, 'info');
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

async function generateQR(isAutoRegeneration = false) {
  try {
    const btn = getElement('generate-btn');
    const status = getElement('qr-status');
    const img = getElement('qr-img');
    
    if (!isAutoRegeneration && btn) {
      setButtonLoading(btn, true, 'Generating...');
    }
    
    if (status) {
      status.textContent = isAutoRegeneration ? 'Auto-regenerating QR code...' : 'Generating QR code...';
    }
    
    const response = await fetch('/generate_qr');
    if (response.ok) {
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      if (img) img.src = url;
      
      await updateCurrentToken();
      
      const statusMessage = isAutoRegeneration ? 
        'QR code auto-regenerated successfully' : 
        'QR code generated successfully';
      if (status) status.textContent = statusMessage;
      
      if (isAutoRegeneration) {
        showNotification('New QR code ready for use', 'success');
      }
    } else {
      throw new Error('Failed to generate QR code');
    }
  } catch (error) {
    console.error('Error generating QR:', error);
    const errorMessage = isAutoRegeneration ? 
      'Error auto-regenerating QR code' : 
      'Error generating QR code';
    const status = getElement('qr-status');
    if (status) status.textContent = errorMessage;
    
    if (isAutoRegeneration) {
      showNotification('Failed to auto-regenerate QR code', 'error');
    }
  } finally {
    if (!isAutoRegeneration) {
      const btn = getElement('generate-btn');
      if (btn) setButtonLoading(btn, false, 'Generate New QR Code');
    }
  }
}

async function updateCurrentToken() {
  try {
    const data = await fetchWithLoading('/api/current_token');
    currentToken = data.token;
    console.log('Updated current token:', currentToken);
  } catch (error) {
    console.error('Error getting current token:', error);
  }
}

async function loadSettings() {
  try {
    const settings = await fetchWithLoading('/api/settings');
    
    console.log('Loaded settings from server:', settings);
    
    const maxUsesEl = getElement('max-uses');
    const timeWindowEl = getElement('time-window');
    const enableBlockingEl = getElement('enable-blocking');
    const autoRegenToggle = getElement('auto-regenerate-qr');
    
    if (maxUsesEl) maxUsesEl.value = settings.max_uses_per_device || 1;
    if (timeWindowEl) timeWindowEl.value = (settings.time_window_minutes || 1440) / 60;
    if (enableBlockingEl) enableBlockingEl.checked = settings.enable_fingerprint_blocking === true;
    
    if (autoRegenToggle) {
      autoRegenToggle.checked = settings.auto_regenerate_qr !== false;
      autoRegenerateEnabled = settings.auto_regenerate_qr !== false;
    }
    
    console.log('Settings applied to form:');
    console.log('- Max uses:', maxUsesEl?.value);
    console.log('- Time window:', timeWindowEl?.value);
    console.log('- Enable blocking:', enableBlockingEl?.checked);
    
    updateDeviceBlockingStatus();
    await updateCurrentToken();
    
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

async function saveSettings() {
  try {
    const autoRegenToggle = document.getElementById('auto-regenerate-qr');
    const enableBlocking = document.getElementById('enable-blocking').checked;
    const maxUses = parseInt(document.getElementById('max-uses').value);
    const timeWindow = parseInt(document.getElementById('time-window').value) * 60;
    
    const settings = {
      max_uses_per_device: maxUses,
      time_window_minutes: timeWindow,
      enable_fingerprint_blocking: enableBlocking,
      auto_regenerate_qr: autoRegenToggle ? autoRegenToggle.checked : true
    };
    
    console.log('Saving settings:', settings);
    
    const response = await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
      if (response.ok) {
      const savedSettings = await response.json();
      console.log('Settings saved successfully:', savedSettings);
      showNotification('Settings saved successfully', 'success');
      autoRegenerateEnabled = settings.auto_regenerate_qr;
      
      // Update the visual status indicator
      updateDeviceBlockingStatus();
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

function updateAttendanceTable() {
  const tbody = document.getElementById('attendances');
  
  if (attendanceData.length === 0) {
    // Check if there's an active session to show appropriate message
    getCurrentSessionId().then(sessionId => {
      if (sessionId) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No check-ins for current session yet</td></tr>';
      } else {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: #666;">No active session - Create a session to see attendance data</td></tr>';
      }
    });
    return;
  }
  
  tbody.innerHTML = attendanceData.slice(0, 50).map(item => `
    <tr>
      <td>${formatTimestamp(item.timestamp)}</td>
      <td>${escapeHtml(item.name || 'Unknown')}</td>
      <td>${escapeHtml(item.course || 'Unknown')}</td>
      <td>${escapeHtml(item.year || 'Unknown')}</td>
      <td>
        <span 
          style="cursor: pointer; color: #007bff; text-decoration: underline;" 
          onclick="showDetailedDeviceInfo('${escapeHtml(item.device_info || '{}')}')"
          title="Click for detailed device information"
        >
          ${getDeviceInfo(item.device_info)}
        </span>
      </td>
      <td>${item.token ? item.token.substring(0, 8) + '...' : 'N/A'}</td>
    </tr>
  `).join('');
}

function updateDeniedTable() {
  const tbody = document.getElementById('denied-attendances');
  
  if (deniedAttempts.length === 0) {
    // Check if there's an active session to show appropriate message
    getCurrentSessionId().then(sessionId => {
      if (sessionId) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No failed attempts for current session</td></tr>';
      } else {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px; color: #666;">No active session</td></tr>';
      }
    });
    return;
  }
  
  tbody.innerHTML = deniedAttempts.slice(0, 50).map(item => `
    <tr>
      <td>${formatTimestamp(item.timestamp)}</td>
      <td>${escapeHtml(item.name)}</td>
      <td>${formatReason(item.reason)}</td>
      <td>${item.token ? item.token.substring(0, 8) + '...' : 'N/A'}</td>
      <td>${item.device_signature ? item.device_signature.substring(0, 12) + '...' : 'N/A'}</td>
    </tr>
  `).join('');
}

function formatTimestamp(timestamp) {
  // Handle different timestamp formats and always show local time in 12-hour format
  if (!timestamp) return 'Unknown';

  let date;
  if (typeof timestamp === 'number') {
    // Unix timestamp (seconds or ms)
    if (timestamp > 1e12) {
      // Already ms
      date = new Date(timestamp);
    } else {
      // Seconds
      date = new Date(timestamp * 1000);
    }
  } else if (typeof timestamp === 'string') {
    // Normalize: replace space with T if needed
    let normalized = timestamp.trim();
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/.test(normalized)) {
      normalized = normalized.replace(' ', 'T');
    }
    date = new Date(normalized);
    if (isNaN(date.getTime())) {
      // Try parsing as float (unix seconds)
      const numTimestamp = parseFloat(timestamp);
      if (!isNaN(numTimestamp)) {
        date = new Date(numTimestamp * 1000);
      } else {
        return 'Invalid Date';
      }
    }
  } else {
    return 'Invalid Date';
  }

  // Use 12-hour format, local time
  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
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

// Add visual indicator for device blocking status
function updateDeviceBlockingStatus() {
  const enableBlockingEl = document.getElementById('enable-blocking');
  if (!enableBlockingEl) return; // Exit if element doesn't exist
  
  const enableBlocking = enableBlockingEl.checked;
  const maxUsesEl = document.getElementById('max-uses');
  const timeWindowEl = document.getElementById('time-window');
  const maxUses = maxUsesEl ? maxUsesEl.value : null;
  const timeWindow = timeWindowEl ? timeWindowEl.value : null;
  
  // Create or update status indicator
  let statusIndicator = document.getElementById('device-blocking-status');
  if (!statusIndicator) {
    statusIndicator = document.createElement('div');
    statusIndicator.id = 'device-blocking-status';
    statusIndicator.style.cssText = `
      margin-top: 10px; padding: 8px; border-radius: 4px; font-size: 12px;
      text-align: center; font-weight: bold;
    `;
    
    const enableBlockingElement = document.getElementById('enable-blocking');
    if (enableBlockingElement && enableBlockingElement.parentElement) {
      enableBlockingElement.parentElement.appendChild(statusIndicator);
    } else {
      return; // Exit if we can't find where to append the status
    }
  }
  
  if (enableBlocking) {
    statusIndicator.style.backgroundColor = '#d4edda';
    statusIndicator.style.color = '#155724';
    statusIndicator.style.border = '1px solid #c3e6cb';
    statusIndicator.textContent = `Device blocking ENABLED: Per-session blocking (one device per session)`;
  } else {
    statusIndicator.style.backgroundColor = '#f8d7da';
    statusIndicator.style.color = '#721c24';
    statusIndicator.style.border = '1px solid #f5c6cb';
    statusIndicator.textContent = 'Device blocking DISABLED: Multiple devices allowed per session';
  }
}

// Add event listeners for settings form changes
function setupSettingsEventListeners() {
  const elements = ['max-uses', 'time-window', 'enable-blocking'];
  
  elements.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('change', updateDeviceBlockingStatus);
      element.addEventListener('input', updateDeviceBlockingStatus);
    }
  });
}