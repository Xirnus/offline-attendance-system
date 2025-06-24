document.addEventListener('DOMContentLoaded', function() {
    loadSessionProfiles();
    setupEventListeners();
});

function setupEventListeners() {
    // Create profile form
    const form = document.querySelector('.add-profile form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            createSessionProfile();
        });
    }
    
    // Search functionality
    const searchInput = document.querySelector('.search-bar input');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            filterProfiles(e.target.value);
        });
    }
}

async function createSessionProfile() {
    const profileName = document.getElementById('profileName').value;
    const roomType = document.getElementById('roomType').value;
    const building = document.getElementById('building').value;
    const capacity = document.getElementById('capacity').value;
    const organizer = document.getElementById('organizer').value; // Directly get the value

    if (!profileName || !roomType) {
        alert('Profile name and room type are required');
        return;
    }
    
    try {
        const response = await fetch('/api/session_profiles', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                profile_name: profileName,
                room_type: roomType,
                building: building || '',
                capacity: parseInt(capacity) || 0,
                organizer: organizer || '' // Ensure this is included
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Session profile created successfully!');
            document.querySelector('.add-profile form').reset();
            loadSessionProfiles(); // Reload to show the new profile
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error creating profile: ' + error.message);
        console.error('Error:', error);
    }
}

async function loadSessionProfiles() {
    try {
        const response = await fetch('/api/session_profiles');
        const data = await response.json();
        
        if (data.profiles) {
            displayProfiles(data.profiles);
        } else {
            console.error('No profiles data received');
            displayProfiles([]);
        }
    } catch (error) {
        console.error('Error loading profiles:', error);
        displayProfiles([]);
    }
}

function displayProfiles(profiles) {
    const grid = document.querySelector('.profiles-grid');
    
    if (!grid) {
        console.error('Profiles grid not found');
        return;
    }
    
    if (profiles.length === 0) {
        grid.innerHTML = '<div class="no-profiles" style="text-align: center; padding: 40px; color: #666;">No session profiles created yet</div>';
        return;
    }
    
    grid.innerHTML = profiles.map(profile => `
        <div class="profile-card">
            <div class="profile-name">${escapeHtml(profile.profile_name)}</div>
            <div class="profile-type">${escapeHtml(profile.room_type.replace('-', ' ').toUpperCase())}</div>
            <div class="profile-details">
                <div class="detail-item">
                    <span><strong>Venue:</strong></span>
                    <span>${escapeHtml(
                        (profile.building ? profile.building : 'Not specified')
                    )}</span>
                </div>
                <div class="detail-item">
                    <span><strong>Capacity:</strong></span>
                    <span>${profile.capacity || 'Not specified'} students</span>
                </div>
                <div class="detail-item">
                    <span><strong>Professor:</strong></span>
                    <span>${escapeHtml(profile.organizer || 'Not specified')}</span>
                </div>
                <div class="detail-item">
                    <span><strong>Created:</strong></span>
                    <span>${formatDate(profile.created_at)}</span>
                </div>
            </div>
            <div class="profile-actions">
                <button class="btn btn-sm btn-success" onclick="useProfile(${profile.id})">Create Session</button>
                <button class="btn btn-sm" onclick="editProfile(${profile.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteProfile(${profile.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

async function useProfile(profileId) {
    try {
        // Get profile details first
        const profileResponse = await fetch('/api/session_profiles');
        const profileData = await profileResponse.json();
        const profile = profileData.profiles.find(p => p.id === profileId);
        
        if (!profile) {
            alert('Profile not found');
            return;
        }
        
        // Show session creation modal
        showSessionCreationModal(profile);
        
    } catch (error) {
        alert('Error loading profile: ' + error.message);
    }
}

function showSessionCreationModal(profile) {
    // Create modal HTML
    const modalHTML = `
        <div id="sessionModal" style="
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
        ">
            <div style="
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                width: 90%; 
                max-width: 500px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <h3 style="margin-bottom: 20px; color: #333;">Create Session Using: ${escapeHtml(profile.profile_name)}</h3>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">Session Name:</label>
                    <input type="text" id="modalSessionName" value="${escapeHtml(profile.profile_name)} - ${new Date().toLocaleDateString()}" 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; font-weight: bold;">End Time:</label>
                    <input type="time" id="modalEndTime" value="${getDefaultEndTime()}" 
                           style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                </div>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                    <h4 style="margin-bottom: 10px; color: #555;">Profile Details:</h4>
                    <p><strong>Room:</strong> ${escapeHtml(profile.profile_name)}</p>
                    <p><strong>Type:</strong> ${escapeHtml(profile.room_type.replace('-', ' '))}</p>
                    <p><strong>Building:</strong> ${escapeHtml(profile.building || 'Not specified')}</p>
                    <p><strong>Capacity:</strong> ${profile.capacity || 'Not specified'} students</p>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="closeSessionModal()" style="
                        background: #6c757d; 
                        color: white; 
                        padding: 10px 20px; 
                        border: none; 
                        border-radius: 3px; 
                        cursor: pointer;
                    ">Cancel</button>
                    <button onclick="createSessionFromProfile(${profile.id})" style="
                        background: #28a745; 
                        color: white; 
                        padding: 10px 20px; 
                        border: none; 
                        border-radius: 3px; 
                        cursor: pointer;
                    ">Create Session</button>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

function closeSessionModal() {
    const modal = document.getElementById('sessionModal');
    if (modal) {
        modal.remove();
    }
}

async function createSessionFromProfile(profileId) {
    const sessionName = document.getElementById('modalSessionName').value;
    const endTime = document.getElementById('modalEndTime').value;
    
    if (!sessionName || !endTime) {
        alert('Please fill in all fields');
        return;
    }
    
    // Create end time as today's date with selected time
    const now = new Date();
    const endDateTime = new Date();
    const [hours, minutes] = endTime.split(':');
    endDateTime.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    
    // If end time is before current time, set it for tomorrow
    if (endDateTime <= now) {
        endDateTime.setDate(endDateTime.getDate() + 1);
    }
    
    try {
        const response = await fetch('/api/create_session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_name: sessionName,
                start_time: now.toISOString(),
                end_time: endDateTime.toISOString(),
                profile_id: profileId
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            alert('Session created successfully! Redirecting to dashboard...');
            closeSessionModal();
            // Redirect to dashboard
            window.location.href = '/dashboard';
        } else {
            alert('Error creating session: ' + (result.message || 'Unknown error'));
        }
    } catch (error) {
        alert('Error creating session: ' + error.message);
    }
}

function getDefaultEndTime() {
    // Default to 2 hours from now
    const now = new Date();
    now.setHours(now.getHours() + 2);
    return now.toTimeString().slice(0, 5); // HH:MM format
}

async function deleteProfile(profileId) {
    if (!confirm('Are you sure you want to delete this session profile?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/session_profiles/${profileId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Profile deleted successfully');
            loadSessionProfiles();
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error deleting profile: ' + error.message);
    }
}

async function editProfile(profileId) {
    try {
        // Get profile details first
        const profileResponse = await fetch('/api/session_profiles');
        const profileData = await profileResponse.json();
        const profile = profileData.profiles.find(p => p.id === profileId);
        
        if (!profile) {
            alert('Profile not found');
            return;
        }
        
        // Show edit modal
        showEditProfileModal(profile);
        
    } catch (error) {
        alert('Error loading profile: ' + error.message);
    }
}

function showEditProfileModal(profile) {
    // Create edit modal HTML
    const modalHTML = `
        <div id="editProfileModal" style="
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
        ">
            <div style="
                background: white; 
                padding: 30px; 
                border-radius: 10px; 
                width: 90%; 
                max-width: 500px;
                max-height: 90vh;
                overflow-y: auto;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="margin: 0; color: #333;">Edit Profile: ${escapeHtml(profile.profile_name)}</h3>
                    <button onclick="closeEditProfileModal()" style="
                        border: none; background: #ccc; border-radius: 50%; 
                        width: 30px; height: 30px; cursor: pointer; font-size: 18px;
                    ">×</button>
                </div>
                
                <form id="editProfileForm">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Session Name *</label>
                        <input type="text" id="editProfileName" value="${escapeHtml(profile.profile_name)}" required
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Room Type *</label>
                        <select id="editRoomType" required 
                                style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                            <option value="">Select room type</option>
                            <option value="lecture-hall" ${profile.room_type === 'lecture-hall' ? 'selected' : ''}>Lecture Hall</option>
                            <option value="laboratory" ${profile.room_type === 'laboratory' ? 'selected' : ''}>Laboratory</option>
                            <option value="classroom" ${profile.room_type === 'classroom' ? 'selected' : ''}>Classroom</option>
                            <option value="seminar-room" ${profile.room_type === 'seminar-room' ? 'selected' : ''}>Seminar Room</option>
                            <option value="computer-lab" ${profile.room_type === 'computer-lab' ? 'selected' : ''}>Computer Lab</option>
                            <option value="workshop" ${profile.room_type === 'workshop' ? 'selected' : ''}>Workshop</option>
                            <option value="auditorium" ${profile.room_type === 'auditorium' ? 'selected' : ''}>Auditorium</option>
                            <option value="conference-room" ${profile.room_type === 'conference-room' ? 'selected' : ''}>Conference Room</option>
                        </select>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Building & Room No.</label>
                        <input type="text" id="editBuilding" value="${escapeHtml(profile.building || '')}" 
                               placeholder="e.g., Engineering Building, Science Block"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                    </div>

                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Professor</label>
                        <input type="text" id="editOrganizer" value="${escapeHtml(profile.organizer || '')}" 
                               placeholder="e.g., Dr. Smith, Prof. Lee, Guest Speaker"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                    </div>
                    
                    <div style="margin-bottom: 20px;">
                        <label style="display: block; margin-bottom: 5px; font-weight: bold;">Room Capacity</label>
                        <input type="number" id="editCapacity" value="${profile.capacity || ''}" 
                               placeholder="Maximum number of students" min="1" max="1000"
                               style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                    </div>
                    
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button type="button" onclick="closeEditProfileModal()" style="
                            background: #6c757d; 
                            color: white; 
                            padding: 10px 20px; 
                            border: none; 
                            border-radius: 3px; 
                            cursor: pointer;
                        ">Cancel</button>
                        <button type="submit" style="
                            background: #007bff; 
                            color: white; 
                            padding: 10px 20px; 
                            border: none; 
                            border-radius: 3px; 
                            cursor: pointer;
                        ">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Add form submit event listener
    const form = document.getElementById('editProfileForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        updateProfile(profile.id);
    });
}

function closeEditProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) {
        modal.remove();
    }
}

async function updateProfile(profileId) {
    const profileName = document.getElementById('editProfileName').value.trim();
    const roomType = document.getElementById('editRoomType').value;
    const building = document.getElementById('editBuilding').value.trim();
    const capacity = document.getElementById('editCapacity').value;
    const organizer = document.getElementById('editOrganizer').value.trim();
    
    if (!profileName || !roomType) {
        alert('Profile name and room type are required');
        return;
    }
    
    try {
        const response = await fetch(`/api/session_profiles/${profileId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                profile_name: profileName,
                room_type: roomType,
                building: building || '',
                capacity: parseInt(capacity) || 0,
                organizer: organizer || ''
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Profile updated successfully!');
            closeEditProfileModal();
            loadSessionProfiles(); // Reload the profiles to show updated data
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error updating profile: ' + error.message);
        console.error('Error:', error);
    }
}

function filterProfiles(searchTerm) {
    const cards = document.querySelectorAll('.profile-card');
    searchTerm = searchTerm.toLowerCase();
    
    cards.forEach(card => {
        const profileName = card.querySelector('.profile-name').textContent.toLowerCase();
        const roomType = card.querySelector('.profile-type').textContent.toLowerCase();
        
        if (profileName.includes(searchTerm) || roomType.includes(searchTerm)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    try {
        return new Date(dateString).toLocaleDateString();
    } catch {
        return 'Unknown';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}