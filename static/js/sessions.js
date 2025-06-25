document.addEventListener('DOMContentLoaded', function() {
    // Form submit
    document.getElementById('profileForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const profile_name = document.getElementById('profileName').value.trim();
        const organizer = document.getElementById('professorName').value.trim();
        const building = document.getElementById('buildingRoom').value.trim();
        const room_type = document.getElementById('roomType').value.trim();
        const capacity = document.getElementById('roomCapacity').value.trim();
        if (!profile_name || !organizer || !building || !room_type || !capacity) {
            alert('Please fill in all fields.');
            return;
        }
        try {
            const res = await fetch('/api/session_profiles', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ profile_name, organizer, building, room_type, capacity })
            });
            if (res.ok) {
                this.reset();
                fetchProfiles(document.getElementById('searchProfiles').value);
            } else {
                const err = await res.json();
                alert('Error: ' + (err.error || 'Could not create profile.'));
            }
        } catch (err) {
            alert('Error: ' + err.message);
        }
    });
    // Search
    document.getElementById('searchProfiles').addEventListener('input', function(e) {
        fetchProfiles(e.target.value);
    });
    fetchProfiles();
});

// Fetch and display session profiles from backend
async function fetchProfiles(filter = '') {
    try {
        const res = await fetch('/api/session_profiles');
        const data = await res.json();
        let profiles = Array.isArray(data.profiles) ? data.profiles : [];
        if (filter) {
            const f = filter.toLowerCase();
            profiles = profiles.filter(p =>
                (p.profile_name || '').toLowerCase().includes(f) ||
                (p.organizer || '').toLowerCase().includes(f) ||
                (p.building || '').toLowerCase().includes(f) ||
                (p.room_type || '').toLowerCase().includes(f) ||
                (p.capacity + '').includes(f)
            );
        }
        renderProfiles(profiles);
    } catch (err) {
        renderProfiles([]);
    }
}

function renderProfiles(profiles) {
    const messageDiv = document.querySelector('.no-profiles-message');
    if (!profiles || profiles.length === 0) {
        messageDiv.innerHTML = '<p>No session profiles created yet.</p>';
        return;
    }
    messageDiv.innerHTML =
        '<div style="margin: 30px 0;">' +
        profiles.map(profile => `
            <div style="border:1.5px solid #28156E; border-radius:12px; margin-bottom:18px; padding:18px 24px; background:#fff; max-width:800px; margin-left:auto; margin-right:auto;">
                <div style="font-weight:600; font-size:16px; color:#28156E; margin-bottom:8px;">${profile.profile_name || ''}</div>
                <div style="font-size:14px; color:#333; margin-bottom:4px;">${profile.organizer || ''} | ${profile.building || ''} | ${profile.room_type || ''} | Capacity: ${profile.capacity || ''}</div>
            </div>
        `).join('') + '</div>';
}