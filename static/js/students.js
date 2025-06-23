document.addEventListener('DOMContentLoaded', function() {
    const importBtn = document.getElementById('import-csv');
    const clearBtn = document.getElementById('clear-table');
    const csvInput = document.getElementById('csv-input');
    const tableBody = document.getElementById('table-body');

    // Load students on page load
    loadStudents();

    // Check for active session and adjust refresh rate accordingly
    checkSessionAndSetRefresh();

    function checkSessionAndSetRefresh() {
        fetch('/api/session_status')
        .then(response => response.json())
        .then(data => {
            if (data.active_session && data.active_session.is_active) {
                // During active session, refresh every 10 seconds
                setInterval(loadStudents, 10000);
            } else {
                // No active session, refresh every 30 seconds
                setInterval(loadStudents, 30000);
            }
        })
        .catch(() => {
            // Default to 30 seconds if can't determine session status
            setInterval(loadStudents, 30000);
        });
    }

    // Clear button
    clearBtn.addEventListener('click', function() {
        if (confirm('Clear all students?')) {
            fetch('/clear_students', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    alert(`Deleted ${data.deleted} students`);
                    loadStudents();
                });
        }
    });

    // Import button
    importBtn.addEventListener('click', function() {
        csvInput.click();
    });

    // File upload
    csvInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload_students', {
                method: 'POST',
                body: formData
            })
            .then(async response => {
                const contentType = response.headers.get('content-type');
                
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Server error (${response.status}): ${errorText}`);
                }
                
                if (!contentType || !contentType.includes('application/json')) {
                    const responseText = await response.text();
                    throw new Error(`Expected JSON response, got: ${responseText.substring(0, 100)}`);
                }
                
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert(data.message);
                    loadStudents();
                }
            })
            .catch(error => {
                console.error('Upload failed:', error);
                alert('Upload failed: ' + error.message);
            });

            csvInput.value = '';
        }
    });

    function loadStudents() {
        fetch('/api/students_with_attendance')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error loading students:', data.error);
                    return;
                }
                
                tableBody.innerHTML = '';
                data.students.forEach(student => {
                    const tr = document.createElement('tr');
                    
                    const statusClass = getStatusClass(student.status);
                    const statusDisplay = formatStatus(student.status);
                    const lastCheckIn = formatLastCheckIn(student.last_check_in);
                    const attendanceRatio = calculateAttendanceRatio(student.present_count, student.absent_count);
                    
                    tr.innerHTML = `
                        <td>${escapeHtml(student.student_id)}</td>
                        <td>${escapeHtml(student.name)}</td>
                        <td>${escapeHtml(student.year)}</td>
                        <td><span class="status-badge ${statusClass}">${statusDisplay}</span></td>
                        <td>${lastCheckIn}</td>
                        <td>${student.absent_count || 0}</td>
                        <td>${attendanceRatio}</td>
                    `;
                    tableBody.appendChild(tr);
                });
                
                updateSummaryStats(data.students);
            })
            .catch(error => {
                console.error('Error loading students:', error);
                tableBody.innerHTML = '<tr><td colspan="7">Error loading student data</td></tr>';
            });
    }
    
    function getStatusClass(status) {
        switch(status) {
            case 'present': return 'status-present';
            case 'absent': return 'status-absent';
            default: return 'status-na';
        }
    }
    
    function formatStatus(status) {
        switch(status) {
            case 'present': return 'Present';
            case 'absent': return 'Absent';
            default: return 'N/A';
        }
    }
    
    function formatLastCheckIn(lastCheckIn) {
        if (!lastCheckIn) return '-';
        
        const date = new Date(lastCheckIn);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    function calculateAttendanceRatio(presentCount, absentCount) {
        const totalSessions = (presentCount || 0) + (absentCount || 0);
        
        if (totalSessions === 0) return 'N/A';
        
        const ratio = ((presentCount || 0) / totalSessions * 100).toFixed(1);
        return `${ratio}%`;
    }
    
    function updateSummaryStats(students) {
        const totalStudents = students.length;
        const presentStudents = students.filter(s => s.status === 'present').length;
        const absentStudents = students.filter(s => s.status === 'absent').length;
        const naStudents = students.filter(s => !s.status || s.status === 'na').length;
        
        const summaryElement = document.getElementById('attendance-summary');
        if (summaryElement) {
            summaryElement.innerHTML = `
                <div class="summary-stats">
                    <span class="stat-item">Total: ${totalStudents}</span>
                    <span class="stat-item present">Present: ${presentStudents}</span>
                    <span class="stat-item absent">Absent: ${absentStudents}</span>
                    <span class="stat-item na">N/A: ${naStudents}</span>
                </div>
            `;
        }
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});