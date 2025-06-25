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
            const refreshInterval = (data.active_session && data.active_session.is_active) ? 10000 : 30000;
            setInterval(loadStudents, refreshInterval);
        })
        .catch(() => {
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
    importBtn.addEventListener('click', () => csvInput.click());

    // File upload
    csvInput.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
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
            alert(data.error ? 'Error: ' + data.error : data.message);
            if (!data.error) loadStudents();
        })
        .catch(error => {
            console.error('Upload failed:', error);
            alert('Upload failed: ' + error.message);
        })
        .finally(() => {
            csvInput.value = '';
        });
    });

    function formatYear(yearNumber) {
        const yearMap = {
            1: '1st Year',
            2: '2nd Year', 
            3: '3rd Year',
            4: '4th Year',
            5: '5th Year'
        };
        
        return yearMap[yearNumber] || `${yearNumber}th Year`;
    }

    function loadStudents() {
        fetch('/api/students_with_attendance?' + Date.now(), {
            headers: {
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading students:', data.error);
                return;
            }
            
            tableBody.innerHTML = '';
            data.students.forEach(student => {
                const tr = document.createElement('tr');
                
                tr.innerHTML = `
                    <td>${escapeHtml(student.student_id)}</td>
                    <td>${escapeHtml(student.name)}</td>
                    <td>${formatYear(student.year)}</td>
                    <td><span class="status-badge ${getStatusClass(student.status)}">${formatStatus(student.status)}</span></td>
                    <td>${formatLastCheckIn(student.last_check_in)}</td>
                    <td style="color: #28a745; font-weight: bold;">${student.present_count || 0}</td>
                    <td style="color: #dc3545; font-weight: bold;">${student.absent_count || 0}</td>
                    <td style="font-weight: bold;">${calculateAttendanceRatio(student.present_count, student.absent_count)}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="editStudent('${escapeHtml(student.student_id)}')">Edit</button>
                    </td>
                `;
                tableBody.appendChild(tr);
            });
            
            updateSummaryStats(data.students);
        })
        .catch(error => {
            console.error('Error loading students:', error);
            tableBody.innerHTML = '<tr><td colspan="9">Error loading student data</td></tr>';
        });
    }

    // Make editStudent function global
    window.editStudent = function(studentId) {
        fetch(`/api/students/${studentId}`)
            .then(response => response.json())
            .then(student => {
                if (student.error) {
                    alert('Error: ' + student.error);
                    return;
                }
                showEditStudentModal(student);
            })
            .catch(error => {
                console.error('Error fetching student:', error);
                alert('Error loading student data');
            });
    };

    function showEditStudentModal(student) {
        const modalHTML = `
            <div id="editStudentModal" style="
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.5); display: flex; justify-content: center; 
                align-items: center; z-index: 1000;">
                <div style="
                    background: white; padding: 30px; border-radius: 10px; 
                    width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3 style="margin: 0; color: #333;">Edit Student: ${escapeHtml(student.name)}</h3>
                        <button onclick="closeEditStudentModal()" style="
                            border: none; background: #ccc; border-radius: 50%; 
                            width: 30px; height: 30px; cursor: pointer; font-size: 18px;">×</button>
                    </div>
                    
                    <form id="editStudentForm">
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Student ID *</label>
                            <input type="text" id="editStudentId" value="${escapeHtml(student.student_id)}" required readonly
                                style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; background: #f5f5f5;">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Name *</label>
                            <input type="text" id="editStudentName" value="${escapeHtml(student.name)}" required
                                style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Course *</label>
                            <input type="text" id="editStudentCourse" value="${escapeHtml(student.course || '')}" required
                                style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                        </div>
                        
                        <div style="margin-bottom: 15px;">
                            <label style="display: block; margin-bottom: 5px; font-weight: bold;">Year *</label>
                            <select id="editStudentYear" required 
                                    style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                                <option value="">Select year</option>
                                ${[1,2,3,4,5].map(year => 
                                    `<option value="${year}" ${student.year === year.toString() ? 'selected' : ''}>${year}${getOrdinalSuffix(year)} Year</option>`
                                ).join('')}
                            </select>
                        </div>
                        
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <h4 style="margin-bottom: 15px; color: #555;">📊 Attendance Statistics:</h4>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #28a745;">Present Count:</label>
                                    <input type="number" id="editPresentCount" value="${student.present_count || 0}" min="0" max="999"
                                        style="width: 100%; padding: 8px; border: 1px solid #28a745; border-radius: 3px;">
                                </div>
                                
                                <div>
                                    <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #dc3545;">Absent Count:</label>
                                    <input type="number" id="editAbsentCount" value="${student.absent_count || 0}" min="0" max="999"
                                        style="width: 100%; padding: 8px; border: 1px solid #dc3545; border-radius: 3px;">
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; margin-bottom: 5px; font-weight: bold;">Current Status:</label>
                                <select id="editStudentStatus" 
                                        style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px;">
                                    <option value="">No Status</option>
                                    <option value="present" ${student.status === 'present' ? 'selected' : ''}>Present</option>
                                    <option value="absent" ${student.status === 'absent' ? 'selected' : ''}>Absent</option>
                                </select>
                            </div>
                            
                            <div id="attendanceRate" style="
                                padding: 10px; background: #e9ecef; border-radius: 3px; 
                                text-align: center; font-weight: bold;">
                                Attendance Rate: <span id="currentRate">${calculateAttendanceRatio(student.present_count, student.absent_count)}</span>
                            </div>
                        </div>
                        
                        <div style="display: flex; gap: 10px; justify-content: flex-end;">
                            <button type="button" onclick="closeEditStudentModal()" style="background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer;">Cancel</button>
                            <button type="button" onclick="deleteStudent('${student.student_id.replace(/'/g, "\\'")}')" style="background: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer;">Delete</button>
                            <button type="submit" style="background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer;">Save Changes</button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add real-time attendance rate calculation
        const presentInput = document.getElementById('editPresentCount');
        const absentInput = document.getElementById('editAbsentCount');
        const rateDisplay = document.getElementById('currentRate');
        
        function updateAttendanceRate() {
            const present = parseInt(presentInput.value) || 0;
            const absent = parseInt(absentInput.value) || 0;
            const rate = calculateAttendanceRatio(present, absent);
            const percentage = parseFloat(rate);
            const rateContainer = document.getElementById('attendanceRate');
            
            rateDisplay.textContent = rate;
            
            // Update color based on rate
            if (percentage >= 80) {
                rateContainer.style.background = '#d4edda';
                rateContainer.style.color = '#155724';
            } else if (percentage >= 60) {
                rateContainer.style.background = '#fff3cd';
                rateContainer.style.color = '#856404';
            } else {
                rateContainer.style.background = '#f8d7da';
                rateContainer.style.color = '#721c24';
            }
        }
        
        presentInput.addEventListener('input', updateAttendanceRate);
        absentInput.addEventListener('input', updateAttendanceRate);
        
        // Add form submit event listener
        document.getElementById('editStudentForm').addEventListener('submit', function(e) {
            e.preventDefault();
            updateStudent(student.student_id);
        });
    }

    window.closeEditStudentModal = function() {
        const modal = document.getElementById('editStudentModal');
        if (modal) modal.remove();
    };

    function updateStudent(originalStudentId) {
        const name = document.getElementById('editStudentName').value.trim();
        const course = document.getElementById('editStudentCourse').value.trim();
        const year = document.getElementById('editStudentYear').value;
        const presentCount = parseInt(document.getElementById('editPresentCount').value) || 0;
        const absentCount = parseInt(document.getElementById('editAbsentCount').value) || 0;
        const status = document.getElementById('editStudentStatus').value || null;
        
        if (!name || !course || !year) {
            alert('Name, Course, and Year are required');
            return;
        }
        
        if (presentCount < 0 || absentCount < 0) {
            alert('Attendance counts cannot be negative');
            return;
        }
        
        fetch(`/api/students/${originalStudentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
            },
            body: JSON.stringify({
                name, course, year,
                present_count: presentCount,
                absent_count: absentCount,
                status
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Student updated successfully!');
                closeEditStudentModal();
                loadStudents();
                // Additional refreshes for data consistency
                setTimeout(loadStudents, 500);
                setTimeout(loadStudents, 1000);
            }
        })
        .catch(error => {
            console.error('Error updating student:', error);
            alert('Error updating student: ' + error.message);
        });
    }

    window.deleteStudent = function(studentId) {
        showDeleteConfirmationModal(studentId);
    };

    function showDeleteConfirmationModal(studentId) {
        const confirmHTML = `
            <div id="deleteConfirmModal" style="
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.7); display: flex; justify-content: center; 
                align-items: center; z-index: 2000;">
                <div style="
                    background: white; padding: 30px; border-radius: 10px; 
                    width: 90%; max-width: 400px; text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
                    <h3 style="margin-bottom: 20px; color: #dc3545;">⚠️ Confirm Deletion</h3>
                    <p style="margin-bottom: 25px; color: #333;">
                        Are you sure you want to delete this student?<br>
                        <strong>This will also delete all their attendance records.</strong><br><br>
                        <strong>Student ID:</strong> ${escapeHtml(studentId)}
                    </p>
                    
                    <div style="display: flex; gap: 15px; justify-content: center;">
                        <button id="cancelDelete" style="background: #6c757d; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px;">Cancel</button>
                        <button id="confirmDelete" style="background: #dc3545; color: white; padding: 12px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold;">Yes, Delete Student</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', confirmHTML);
        
        document.getElementById('cancelDelete').addEventListener('click', closeDeleteConfirmModal);
        document.getElementById('confirmDelete').addEventListener('click', function() {
            closeDeleteConfirmModal();
            proceedWithDelete(studentId);
        });
    }

    function closeDeleteConfirmModal() {
        const modal = document.getElementById('deleteConfirmModal');
        if (modal) modal.remove();
    }

    function proceedWithDelete(studentId) {
        fetch(`/api/students/${studentId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                alert('Student deleted successfully!');
                closeEditStudentModal();
                loadStudents();
            }
        })
        .catch(error => {
            console.error('Error deleting student:', error);
            alert('Error deleting student: ' + error.message);
        });
    }

    // Utility functions
    function getStatusClass(status) {
        return status === 'present' ? 'status-present' : 
               status === 'absent' ? 'status-absent' : 'status-na';
    }
    
    function formatStatus(status) {
        return status === 'present' ? 'Present' : 
               status === 'absent' ? 'Absent' : 'N/A';
    }
    
    function formatLastCheckIn(lastCheckIn) {
        if (!lastCheckIn) return '-';
        const date = new Date(lastCheckIn);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
    
    function calculateAttendanceRatio(presentCount, absentCount) {
        const totalSessions = (presentCount || 0) + (absentCount || 0);
        return totalSessions === 0 ? 'N/A' : `${((presentCount || 0) / totalSessions * 100).toFixed(1)}%`;
    }

    function getOrdinalSuffix(num) {
        const suffixes = ['th', 'st', 'nd', 'rd'];
        const v = num % 100;
        return suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0];
    }
    
    function updateSummaryStats(students) {
        const totalStudents = students.length;
        const presentStudents = students.filter(s => s.status === 'present').length;
        const absentStudents = students.filter(s => s.status === 'absent').length;
        const naStudents = totalStudents - presentStudents - absentStudents;
        
        const totalPresentCount = students.reduce((sum, s) => sum + (s.present_count || 0), 0);
        const totalAbsentCount = students.reduce((sum, s) => sum + (s.absent_count || 0), 0);
        const overallRate = totalPresentCount + totalAbsentCount > 0 
            ? ((totalPresentCount / (totalPresentCount + totalAbsentCount)) * 100).toFixed(1) + '%'
            : 'N/A';
        
        const summaryElement = document.getElementById('attendance-summary');
        if (summaryElement) {
            summaryElement.innerHTML = `
                <div class="summary-stats">
                    <span class="stat-item">Total Students: ${totalStudents}</span>
                    <span class="stat-item present">Currently Present: ${presentStudents}</span>
                    <span class="stat-item absent">Currently Absent: ${absentStudents}</span>
                    <span class="stat-item na">No Status: ${naStudents}</span>
                    <br>
                    <span class="stat-item" style="color: #28a745; font-weight: bold;">Total Present Records: ${totalPresentCount}</span>
                    <span class="stat-item" style="color: #dc3545; font-weight: bold;">Total Absent Records: ${totalAbsentCount}</span>
                    <span class="stat-item" style="font-weight: bold;">Overall Rate: ${overallRate}</span>
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