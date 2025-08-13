document.addEventListener('DOMContentLoaded', function() {
    const importBtn = getElement('import-csv');
    const clearBtn = getElement('clear-table');
    const csvInput = getElement('csv-input');
    const tableBody = getElement('table-body');

    // Load students and classes on page load
    loadStudents();
    loadClasses();

    // Check for active session and adjust refresh rate accordingly
    checkSessionAndSetRefresh();

    function checkSessionAndSetRefresh() {
        fetchWithLoading('/api/session_status')
        .then(data => {
            const refreshInterval = (data.active_session && data.active_session.is_active) ? 10000 : 30000;
            setInterval(loadStudents, refreshInterval);
        })
        .catch(() => {
            setInterval(loadStudents, 30000);
        });
    }

    // Clear button
    addEventListenerSafe(clearBtn, 'click', async function() {
        const confirmed = await customConfirm('Clear all students?', 'Confirm Action');
        if (confirmed) {
            try {
                const data = await postJSON('/clear_students');
                showNotification(`Deleted ${data.deleted} students`, 'success');
                loadStudents();
            } catch (error) {
                showNotification('Error deleting students', 'error');
            }
        }
    });

    // Import button
    addEventListenerSafe(importBtn, 'click', () => csvInput?.click());

    // File upload
    addEventListenerSafe(csvInput, 'change', async function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            setButtonLoading(importBtn, true, 'Uploading...');
            
            const response = await fetch('/upload_students', {
                method: 'POST',
                body: formData
            });
            
            const contentType = response.headers.get('content-type');
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Server error (${response.status}): ${errorText}`);
            }
            
            if (!contentType || !contentType.includes('application/json')) {
                const responseText = await response.text();
                throw new Error(`Expected JSON response, got: ${responseText.substring(0, 100)}`);
            }
            
            const data = await response.json();
            showNotification(data.error ? 'Error: ' + data.error : data.message, data.error ? 'error' : 'success');
            if (!data.error) loadStudents();
        } catch (error) {
            console.error('Upload failed:', error);
            showNotification('Upload failed: ' + error.message, 'error');
        } finally {
            setButtonLoading(importBtn, false);
            if (csvInput) csvInput.value = '';
        }
    });

    // Class filter change - use direct DOM query
    const classFilterElement = document.getElementById('class-filter');
    if (classFilterElement) {
        classFilterElement.addEventListener('change', function() {
            loadStudents();
        });
    }

    // Add to DOMContentLoaded function
    const addStudentBtn = document.getElementById('add-student');
    const addStudentModal = document.getElementById('addStudentModal');

    // Add Student Button Event
    addStudentBtn.addEventListener('click', () => {
        addStudentModal.style.display = 'flex';
        populateClassDropdownForModal();
    });

    // Close Modal Events
    document.getElementById('closeAddModal').addEventListener('click', closeAddModal);
    document.getElementById('cancelAddStudent').addEventListener('click', closeAddModal);

    function closeAddModal() {
        addStudentModal.style.display = 'none';
        document.getElementById('addStudentForm').reset();
    }

    // Form Submission
    document.getElementById('addStudentForm').addEventListener('submit', function(e) {
        e.preventDefault();
        addNewStudent();
    });

    function addNewStudent() {
        const studentId = document.getElementById('newStudentId').value.trim();
        const name = document.getElementById('newStudentName').value.trim();
        const course = document.getElementById('newStudentCourse').value.trim();
        const year = document.getElementById('newStudentYear').value;
        const classId = document.getElementById('newStudentClass').value;
    
        if (!studentId || !name || !course || !year) {
            alert('Please fill all required fields');
            return;
        }
    
        // First, add the student
        fetch('/api/add_student', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                name: name,
                course: course,
                year: parseInt(year)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Error: ' + data.error);
            } else {
                // If student was added successfully and a class was selected, enroll them
                if (classId && classId !== '') {
                    enrollStudentInClass(studentId, classId);
                } else {
                    alert('Student added successfully!');
                    closeAddModal();
                    loadStudents();
                }
            }
        })
        .catch(error => {
            console.error('Error adding student:', error);
            alert('Error adding student: ' + error.message);
        });
    }

    // Function to enroll a student in a class
    function enrollStudentInClass(studentId, classId) {
        fetch(`/api/optimized/classes/${classId}/enroll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_ids: [studentId]
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('Student added but failed to enroll in class: ' + data.error);
            } else {
                alert('Student added and enrolled in class successfully!');
            }
            closeAddModal();
            loadStudents();
        })
        .catch(error => {
            console.error('Error enrolling student in class:', error);
            alert('Student added but failed to enroll in class: ' + error.message);
            closeAddModal();
            loadStudents();
        });
    }

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

    // Load available classes for the filter
    function loadClasses() {
        fetch('/api/optimized/classes')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.classes) {
                const classFilter = document.getElementById('class-filter');
                
                if (!classFilter) {
                    console.error('Class filter element not found');
                    return;
                }
                
                // Clear existing options except "All Classes"
                classFilter.innerHTML = '<option value="">All Classes</option>';
                
                // Add class options
                data.classes.forEach(classItem => {
                    const option = document.createElement('option');
                    // Use class_id instead of id
                    if (classItem.class_id !== undefined && classItem.class_id !== null) {
                        option.value = classItem.class_id;
                        option.textContent = classItem.class_name || `Class ${classItem.class_id}`;
                        classFilter.appendChild(option);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading classes:', error);
        });
    }

    // Populate class dropdown for Add Student modal
    function populateClassDropdownForModal() {
        fetch('/api/optimized/classes')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.classes) {
                const classSelect = document.getElementById('newStudentClass');
                
                if (!classSelect) return;
                
                // Clear existing options except default
                classSelect.innerHTML = '<option value="">No class assignment</option>';
                
                // Add class options
                data.classes.forEach(classItem => {
                    if (classItem.class_id !== undefined && classItem.class_id !== null) {
                        const option = document.createElement('option');
                        option.value = classItem.class_id;
                        option.textContent = classItem.class_name || `Class ${classItem.class_id}`;
                        classSelect.appendChild(option);
                    }
                });
            }
        })
        .catch(error => {
            console.error('Error loading classes for modal:', error);
        });
    }

    function loadStudents() {
        // Show loading state
        tableBody.innerHTML = '<tr><td colspan="9" class="table-loading">Loading students...</td></tr>';
        
        // Get selected class filter
        const classFilterElement = document.getElementById('class-filter');
        const selectedClassId = classFilterElement ? classFilterElement.value : '';
        
        // Choose endpoint based on filter
        let endpoint;
        if (selectedClassId && selectedClassId !== '' && selectedClassId !== 'undefined' && selectedClassId !== undefined) {
            endpoint = `/api/optimized/classes/${selectedClassId}/students`;
        } else {
            endpoint = '/api/students_with_attendance?' + Date.now();
        }
        
        fetch(endpoint, {
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
            
            // Handle different response formats
            let students;
            if (selectedClassId && selectedClassId !== '' && selectedClassId !== 'undefined' && selectedClassId !== undefined) {
                // Response from class students endpoint
                students = data.status === 'success' ? data.students : [];
            } else {
                // Response from all students endpoint
                students = data.students || [];
            }
            
            students.forEach(student => {
                const tr = document.createElement('tr');
                
                tr.innerHTML = `
                    <td>${escapeHtml(student.student_id)}</td>
                    <td>${escapeHtml(student.name)}</td>
                    <td>${formatYear(student.year)}</td>
                    <td><span class="status-badge ${getStatusClass(student.status)}">${formatStatus(student.status)}</span></td>
                    <td>${formatLastCheckIn(student.last_check_in)}</td>
                    <td class="count-present">${student.present_count || 0}</td>
                    <td class="count-absent">${student.absent_count || 0}</td>
                    <td>
                        <button class="btn btn-sm btn-primary" onclick="editStudent('${escapeHtml(student.student_id)}')">Edit</button>
                    </td>
                    <td class="attendance-ratio">${calculateAttendanceRatio(student.present_count, student.absent_count)}</td>
                `;
                tableBody.appendChild(tr);
            });
            
            updateSummaryStats(students);
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
            <div id="editStudentModal" class="modern-modal-overlay">
                <div class="modern-modal">
                    <div class="modern-modal-header">
                        <h3>Edit Student: ${escapeHtml(student.name)}</h3>
                        <button type="button" class="modern-modal-close" onclick="closeEditStudentModal()">×</button>
                    </div>
                    <form id="editStudentForm">
                        <div class="modern-modal-group">
                            <label>Student ID *</label>
                            <input type="text" id="editStudentId" value="${escapeHtml(student.student_id)}" required readonly>
                        </div>
                        <div class="modern-modal-group">
                            <label>Name *</label>
                            <input type="text" id="editStudentName" value="${escapeHtml(student.name)}" required>
                        </div>
                        <div class="modern-modal-group">
                            <label>Course *</label>
                            <input type="text" id="editStudentCourse" value="${escapeHtml(student.course || '')}" required>
                        </div>
                        <div class="modern-modal-group">
                            <label>Year *</label>
                            <select id="editStudentYear" required>
                                <option value="">Select year</option>
                                ${[1,2,3,4,5].map(year => 
                                    `<option value="${year}" ${student.year === year.toString() ? 'selected' : ''}>${year}${getOrdinalSuffix(year)} Year</option>`
                                ).join('')}
                            </select>
                        </div>
                        <div class="modern-modal-stats">
                            <h4>📊 Attendance Statistics:</h4>
                            <div class="modern-modal-stats-row">
                                <div>
                                    <label>Present Count:</label>
                                    <input type="number" id="editPresentCount" value="${student.present_count || 0}" min="0" max="999">
                                </div>
                                <div>
                                    <label>Absent Count:</label>
                                    <input type="number" id="editAbsentCount" value="${student.absent_count || 0}" min="0" max="999">
                                </div>
                            </div>
                            <div class="modern-modal-group">
                                <label>Current Status:</label>
                                <select id="editStudentStatus">
                                    <option value="">No Status</option>
                                    <option value="present" ${student.status === 'present' ? 'selected' : ''}>Present</option>
                                    <option value="absent" ${student.status === 'absent' ? 'selected' : ''}>Absent</option>
                                    <option value="late" ${student.status === 'late' ? 'selected' : ''}>Late</option>
                                </select>
                            </div>
                            <div id="attendanceRate" class="modern-modal-rate">
                                Attendance Rate: <span id="currentRate">${calculateAttendanceRatio(student.present_count, student.absent_count)}</span>
                            </div>
                        </div>
                        <div class="modern-modal-actions">
                            <button type="button" class="modern-btn modern-btn-secondary" onclick="closeEditStudentModal()">Cancel</button>
                            <button type="button" class="modern-btn modern-btn-danger" data-student-id="${escapeHtml(student.student_id)}" id="deleteStudentBtn">Delete</button>
                            <button type="submit" class="modern-btn modern-btn-primary">Save Changes</button>
                        </div>
                        <div id="editStudentSuccessMsg" class="modern-modal-success" style="display:none;">Student updated successfully!</div>
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
        
        // Add delete button event listener
        document.getElementById('deleteStudentBtn').addEventListener('click', function() {
            const studentId = this.getAttribute('data-student-id');
            deleteStudent(studentId);
        });
    }

    window.closeEditStudentModal = function() {
        const modal = document.getElementById('editStudentModal');
        if (modal) modal.remove();
    };

    function updateStudent(originalStudentId) {
        const name = document.getElementById('editStudentName').value.trim();
        const course = document.getElementById('editStudentCourse').value.trim();
        const year = parseInt(document.getElementById('editStudentYear').value, 10);
        const presentCount = parseInt(document.getElementById('editPresentCount').value) || 0;
        const absentCount = parseInt(document.getElementById('editAbsentCount').value) || 0;
        const status = document.getElementById('editStudentStatus').value || null;

        if (!name || !course || !year) {
            showModernModalError('Name, Course, and Year are required');
            return;
        }
        if (presentCount < 0 || absentCount < 0) {
            showModernModalError('Attendance counts cannot be negative');
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
                showModernModalError('Error: ' + data.error);
            } else {
                // Show success message in modal, then close after a short delay
                const msg = document.getElementById('editStudentSuccessMsg');
                if (msg) {
                    msg.style.display = 'block';
                    setTimeout(() => {
                        closeEditStudentModal();
                        loadStudents();
                    }, 1200);
                } else {
                    closeEditStudentModal();
                    loadStudents();
                }
            }
        })
        .catch(error => {
            showModernModalError('Error updating student: ' + error.message);
        });
    }

    // Show error in modal (modern look)
    function showModernModalError(msg) {
        let errorDiv = document.getElementById('editStudentErrorMsg');
        if (!errorDiv) {
            const form = document.getElementById('editStudentForm');
            errorDiv = document.createElement('div');
            errorDiv.id = 'editStudentErrorMsg';
            errorDiv.className = 'modern-modal-error';
            form.insertBefore(errorDiv, form.firstChild);
        }
        errorDiv.textContent = msg;
        errorDiv.style.display = 'block';
        setTimeout(() => { if (errorDiv) errorDiv.style.display = 'none'; }, 2000);
    }

    window.deleteStudent = function(studentId) {
        showDeleteConfirmationModal(studentId);
    };

    function showDeleteConfirmationModal(studentId) {
        const confirmHTML = `
            <div id="deleteConfirmModal" style="
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.8); display: flex; justify-content: center; 
                align-items: center; z-index: 9999;">
                <div style="
                    background: white; padding: 30px; border-radius: 10px; 
                    width: 90%; max-width: 400px; text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 10000;">
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
               status === 'absent' ? 'status-absent' :
               status === 'late' ? 'status-late' : 'status-na';
    }
    
    function formatStatus(status) {
        return status === 'present' ? 'Present' : 
               status === 'absent' ? 'Absent' :
               status === 'late' ? 'Late' : 'N/A';
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
    
    // Remove duplicate escapeHtml function - now using common.js version
});