// Sessions Management JavaScript

let currentProfiles = [];
let activeSession = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeSessionsPage();
    setupEventListeners();
    loadActiveSession();
    fetchProfiles();
});

function setupEventListeners() {
    // Profile form submission
    document.getElementById('profileForm').addEventListener('submit', handleCreateProfile);
    
    // Search functionality
    document.getElementById('searchProfiles').addEventListener('input', function(e) {
        filterProfiles(e.target.value);
    });
    
    // Session creation form (commented out since modal removed)
    // document.getElementById('createSessionForm')?.addEventListener('submit', handleCreateSession);
    
    // Edit profile form
    document.getElementById('editProfileForm').addEventListener('submit', handleEditProfile);
    
    // Modal controls
    setupModalControls();
    
    // Auto-refresh every 30 seconds
    setInterval(loadActiveSession, 30000);
}

function setupModalControls() {
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close');
    
    // Close modal when clicking X
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
}

function initializeSessionsPage() {
    // Session page initialization
    // Note: Session creation modal elements removed
}

function formatDateTime(date) {
    return date.toISOString().slice(0, 16);
}

async function loadActiveSession() {
    try {
        const response = await fetch('/api/session_status');
        const data = await response.json();
        activeSession = data.active_session;
        updateActiveSessionDisplay();
    } catch (error) {
        console.error('Error loading active session:', error);
        showMessage('Failed to load session status', 'error');
    }
}

function updateActiveSessionDisplay() {
    const section = document.getElementById('activeSessionSection');
    
    if (activeSession) {
        section.className = 'active-session-section';
        section.innerHTML = `
            <div class="active-session-header">
                <h2 class="active-session-title">${activeSession.session_name || 'Active Session'}</h2>
                <span class="session-status-badge">ACTIVE</span>
            </div>
            <div class="session-details">
                <div class="session-detail">
                    <div class="session-detail-label">Start Time</div>
                    <div class="session-detail-value">${formatDisplayTime(activeSession.start_time)}</div>
                </div>
                <div class="session-detail">
                    <div class="session-detail-label">End Time</div>
                    <div class="session-detail-value">${formatDisplayTime(activeSession.end_time)}</div>
                </div>
                <div class="session-detail">
                    <div class="session-detail-label">Duration</div>
                    <div class="session-detail-value">${calculateDuration(activeSession.start_time, activeSession.end_time)}</div>
                </div>
                ${activeSession.class_table ? `
                <div class="session-detail">
                    <div class="session-detail-label">Course</div>
                    <div class="session-detail-value">${activeSession.class_table}</div>
                </div>
                ` : ''}
            </div>
            <div class="session-actions">
                <button class="btn-stop-session" onclick="stopActiveSession()">Stop Session</button>
            </div>
        `;
    } else {
        section.className = 'active-session-section no-session';
        section.innerHTML = `
            <div class="active-session-header">
                <h2 class="active-session-title">No Active Session</h2>
                <span class="session-status-badge">INACTIVE</span>
            </div>
            <p>Start a new session using a session profile or create a new session from scratch.</p>
        `;
    }
}

function formatDisplayTime(timeString) {
    if (!timeString) return 'N/A';
    try {
        const date = new Date(timeString);
        return date.toLocaleString();
    } catch (error) {
        return timeString;
    }
}

function calculateDuration(startTime, endTime) {
    try {
        const start = new Date(startTime);
        const end = new Date(endTime);
        const diffMs = end - start;
        const hours = Math.floor(diffMs / (1000 * 60 * 60));
        const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
        return `${hours}h ${minutes}m`;
    } catch (error) {
        return 'N/A';
    }
}

async function stopActiveSession() {
    if (!activeSession) return;
    
    if (!confirm('Are you sure you want to stop the active session? This will mark absent students and end attendance tracking.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/stop_session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            showMessage(result.message, 'success');
            loadActiveSession(); // Refresh the display
        } else {
            showMessage(result.message || 'Failed to stop session', 'error');
        }
    } catch (error) {
        console.error('Error stopping session:', error);
        showMessage('Failed to stop session', 'error');
    }
}

async function fetchProfiles(filter = '') {
    console.log('Fetching profiles...'); // Debug log
    try {
        const response = await fetch('/api/session_profiles');
        const data = await response.json();
        console.log('Profiles data:', data); // Debug log
        currentProfiles = Array.isArray(data.profiles) ? data.profiles : [];
        
        if (filter) {
            filterProfiles(filter);
        } else {
            renderProfiles(currentProfiles);
        }
    } catch (error) {
        console.error('Error fetching profiles:', error);
        renderProfiles([]);
        showMessage('Failed to load session profiles', 'error');
    }
}

function filterProfiles(filter) {
    if (!filter.trim()) {
        renderProfiles(currentProfiles);
        return;
    }
    
    const f = filter.toLowerCase();
    const filtered = currentProfiles.filter(p =>
        (p.profile_name || '').toLowerCase().includes(f) ||
        (p.organizer || '').toLowerCase().includes(f) ||
        (p.building || '').toLowerCase().includes(f) ||
        (p.room_type || '').toLowerCase().includes(f) ||
        (p.capacity + '').includes(f)
    );
    
    renderProfiles(filtered);
}

function renderProfiles(profiles) {
    const container = document.getElementById('profilesList');
    console.log('Rendering profiles:', profiles, 'Container:', container); // Debug log
    
    if (!profiles || profiles.length === 0) {
        container.innerHTML = `
            <div class="no-profiles-message">
                <p>📝 No session profiles found</p>
                <p>Create your first profile to get started with session management.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = profiles.map(profile => `
        <div class="profile-card" data-profile-id="${profile.id}">
            <div class="profile-name">${escapeHtml(profile.profile_name || 'Unnamed Profile')}</div>
            <div class="profile-details">
                <strong>Organizer:</strong> ${escapeHtml(profile.organizer || 'N/A')}<br>
                <strong>Location:</strong> ${escapeHtml(profile.building || 'N/A')}<br>
                <strong>Type:</strong> ${escapeHtml(profile.room_type || 'N/A')} | 
                <strong>Capacity:</strong> ${profile.capacity || 'N/A'} people
            </div>
            <div class="profile-actions">
                <button class="btn-manage-students" onclick="openManageStudentsModal(${profile.id})">
                    👥 Manage Students
                </button>
                <button class="btn-edit-profile" onclick="openEditProfileModal(${profile.id})">
                    ✏️ Edit
                </button>
                <button class="btn-delete-profile" onclick="deleteProfile(${profile.id})">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function handleCreateProfile(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const profileData = Object.fromEntries(formData);
    
    // Validate required fields
    if (!profileData.profile_name || !profileData.organizer || !profileData.building || 
        !profileData.room_type || !profileData.capacity) {
        showMessage('Please fill in all required fields', 'error');
        return;
    }
    
    // Validate capacity
    const capacity = parseInt(profileData.capacity);
    if (isNaN(capacity) || capacity < 1 || capacity > 1000) {
        showMessage('Room capacity must be between 1 and 1000', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/session_profiles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            showMessage('Session profile created successfully!', 'success');
            e.target.reset();
            fetchProfiles(document.getElementById('searchProfiles').value);
        } else {
            showMessage(result.error || 'Failed to create profile', 'error');
        }
    } catch (error) {
        console.error('Error creating profile:', error);
        showMessage('Failed to create profile', 'error');
    }
}

function openEditProfileModal(profileId) {
    const profile = currentProfiles.find(p => p.id === profileId);
    if (!profile) return;
    
    // Populate form fields
    document.getElementById('editProfileId').value = profile.id;
    document.getElementById('editProfileName').value = profile.profile_name || '';
    document.getElementById('editProfessorName').value = profile.organizer || '';
    document.getElementById('editBuildingRoom').value = profile.building || '';
    document.getElementById('editRoomType').value = profile.room_type || '';
    document.getElementById('editRoomCapacity').value = profile.capacity || '';
    
    document.getElementById('editProfileModal').style.display = 'block';
}

async function handleEditProfile(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const profileData = Object.fromEntries(formData);
    const profileId = profileData.profile_id;
    
    delete profileData.profile_id; // Remove ID from data to send
    
    try {
        const response = await fetch(`/api/session_profiles/${profileId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            showMessage('Profile updated successfully!', 'success');
            document.getElementById('editProfileModal').style.display = 'none';
            fetchProfiles(document.getElementById('searchProfiles').value);
        } else {
            showMessage(result.error || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showMessage('Failed to update profile', 'error');
    }
}

async function deleteProfile(profileId) {
    const profile = currentProfiles.find(p => p.id === profileId);
    if (!profile) return;
    
    if (!confirm(`Are you sure you want to delete the profile "${profile.profile_name}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/session_profiles/${profileId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            showMessage('Profile deleted successfully!', 'success');
            fetchProfiles(document.getElementById('searchProfiles').value);
        } else {
            showMessage(result.error || 'Failed to delete profile', 'error');
        }
    } catch (error) {
        console.error('Error deleting profile:', error);
        showMessage('Failed to delete profile', 'error');
    }
}

function refreshData() {
    loadActiveSession();
    fetchProfiles(document.getElementById('searchProfiles').value);
    showMessage('Data refreshed', 'success');
}

function showMessage(message, type = 'info') {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.error-message, .success-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
    messageDiv.textContent = message;
    
    // Insert at the top of content
    const content = document.querySelector('.content');
    content.insertBefore(messageDiv, content.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.remove();
        }
    }, 5000);
}

// Global functions for button handlers
window.openEditProfileModal = openEditProfileModal;
window.openManageStudentsModal = openManageStudentsModal;
window.deleteProfile = deleteProfile;
window.stopActiveSession = stopActiveSession;
window.refreshData = refreshData;
window.refreshEnrolledStudents = refreshEnrolledStudents;
window.refreshAvailableStudents = refreshAvailableStudents;
window.enrollSelectedStudents = enrollSelectedStudents;
window.toggleSelectAllAvailable = toggleSelectAllAvailable;
window.unenrollStudent = unenrollStudent;

// Student enrollment management functions
let currentManageProfileId = null;
let enrolledStudents = [];
let availableStudents = [];

function openManageStudentsModal(profileId) {
    const profile = currentProfiles.find(p => p.id === profileId);
    if (!profile) return;
    
    currentManageProfileId = profileId;
    document.getElementById('manageProfileId').value = profileId;
    document.getElementById('modalProfileName').textContent = profile.profile_name;
    
    // Setup search functionality
    setupStudentSearch();
    
    // Load students data
    refreshEnrolledStudents();
    refreshAvailableStudents();
    
    document.getElementById('manageStudentsModal').style.display = 'block';
}

function setupStudentSearch() {
    // Search enrolled students
    document.getElementById('searchEnrolledStudents').addEventListener('input', function(e) {
        filterEnrolledStudents(e.target.value);
    });
    
    // Search available students
    document.getElementById('searchAvailableStudents').addEventListener('input', function(e) {
        filterAvailableStudents(e.target.value);
    });
}

async function refreshEnrolledStudents() {
    const container = document.getElementById('enrolledStudentsList');
    container.innerHTML = '<div class="loading">Loading enrolled students...</div>';
    
    try {
        const response = await fetch(`/api/session_profiles/${currentManageProfileId}/students`);
        const data = await response.json();
        
        if (response.ok) {
            enrolledStudents = data.students || [];
            displayEnrolledStudents(enrolledStudents);
            document.getElementById('enrolledCount').textContent = enrolledStudents.length;
        } else {
            container.innerHTML = `<div class="error-message">Error loading enrolled students: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading enrolled students:', error);
        container.innerHTML = '<div class="error-message">Failed to load enrolled students</div>';
    }
}

async function refreshAvailableStudents() {
    const container = document.getElementById('availableStudentsList');
    container.innerHTML = '<div class="loading">Loading available students...</div>';
    
    try {
        const response = await fetch(`/api/session_profiles/${currentManageProfileId}/available_students`);
        const data = await response.json();
        
        if (response.ok) {
            availableStudents = data.students || [];
            displayAvailableStudents(availableStudents);
            document.getElementById('availableCount').textContent = availableStudents.length;
        } else {
            container.innerHTML = `<div class="error-message">Error loading available students: ${data.error}</div>`;
        }
    } catch (error) {
        console.error('Error loading available students:', error);
        container.innerHTML = '<div class="error-message">Failed to load available students</div>';
    }
}

function displayEnrolledStudents(students) {
    const container = document.getElementById('enrolledStudentsList');
    
    if (students.length === 0) {
        container.innerHTML = '<div class="no-students">No students enrolled in this session profile</div>';
        return;
    }
    
    container.innerHTML = students.map(student => `
        <div class="student-item enrolled-student">
            <div class="student-info">
                <div class="student-name">${escapeHtml(student.name)}</div>
                <div class="student-details">
                    <span class="student-id">${escapeHtml(student.student_id)}</span>
                    <span class="student-course">${escapeHtml(student.course || 'N/A')}</span>
                    <span class="student-year">Year ${student.year || 'N/A'}</span>
                </div>
            </div>
            <div class="student-actions">
                <button type="button" class="btn btn-danger btn-sm" onclick="unenrollStudent('${student.student_id}')">
                    ➖ Remove
                </button>
            </div>
        </div>
    `).join('');
}

function displayAvailableStudents(students) {
    const container = document.getElementById('availableStudentsList');
    
    if (students.length === 0) {
        container.innerHTML = '<div class="no-students">No additional students available for enrollment</div>';
        return;
    }
    
    container.innerHTML = students.map(student => `
        <div class="student-item available-student">
            <div class="student-checkbox">
                <input type="checkbox" id="student_${student.student_id}" value="${student.student_id}" class="student-select">
            </div>
            <div class="student-info">
                <div class="student-name">${escapeHtml(student.name)}</div>
                <div class="student-details">
                    <span class="student-id">${escapeHtml(student.student_id)}</span>
                    <span class="student-course">${escapeHtml(student.course || 'N/A')}</span>
                    <span class="student-year">Year ${student.year || 'N/A'}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function filterEnrolledStudents(searchTerm) {
    if (!searchTerm) {
        displayEnrolledStudents(enrolledStudents);
        return;
    }
    
    const filtered = enrolledStudents.filter(student => 
        student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (student.course && student.course.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    
    displayEnrolledStudents(filtered);
}

function filterAvailableStudents(searchTerm) {
    if (!searchTerm) {
        displayAvailableStudents(availableStudents);
        return;
    }
    
    const filtered = availableStudents.filter(student => 
        student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.student_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (student.course && student.course.toLowerCase().includes(searchTerm.toLowerCase()))
    );
    
    displayAvailableStudents(filtered);
}

function toggleSelectAllAvailable() {
    const selectAllCheckbox = document.getElementById('selectAllAvailable');
    const studentCheckboxes = document.querySelectorAll('.student-select');
    
    studentCheckboxes.forEach(checkbox => {
        checkbox.checked = selectAllCheckbox.checked;
    });
}

async function enrollSelectedStudents() {
    const selectedCheckboxes = document.querySelectorAll('.student-select:checked');
    const studentIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (studentIds.length === 0) {
        showMessage('Please select at least one student to enroll', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/session_profiles/${currentManageProfileId}/bulk_enroll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_ids: studentIds })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            showMessage(`Successfully enrolled ${result.enrolled_count} students`, 'success');
            // Refresh both lists
            refreshEnrolledStudents();
            refreshAvailableStudents();
            // Clear selections
            document.getElementById('selectAllAvailable').checked = false;
        } else {
            showMessage(result.error || 'Failed to enroll students', 'error');
        }
    } catch (error) {
        console.error('Error enrolling students:', error);
        showMessage('Failed to enroll students', 'error');
    }
}

async function unenrollStudent(studentId) {
    const student = enrolledStudents.find(s => s.student_id === studentId);
    if (!student) return;
    
    if (!confirm(`Are you sure you want to remove ${student.name} from this session profile?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/session_profiles/${currentManageProfileId}/unenroll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            showMessage('Student removed successfully', 'success');
            // Refresh both lists
            refreshEnrolledStudents();
            refreshAvailableStudents();
        } else {
            showMessage(result.error || 'Failed to remove student', 'error');
        }
    } catch (error) {
        console.error('Error removing student:', error);
        showMessage('Failed to remove student', 'error');
    }
}
