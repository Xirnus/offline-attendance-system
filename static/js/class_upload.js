document.addEventListener('DOMContentLoaded', function() {
    const classInfoContainer = document.getElementById('classInfoContainer');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');

    // Initialize the page
    initPage();

    function initPage() {
        // Load CSS
        loadCSS();
        
        // Set up event listeners
        uploadBtn.addEventListener('click', handleFileUpload);
        
        // Load existing class data
        loadClassTables();
        
        // Add manual input section
        addManualInputSection();
    }

    function loadCSS() {
        const cssLink = document.createElement('link');
        cssLink.href = "{{ url_for('static', filename='css/class_upload.css') }}";
        cssLink.rel = "stylesheet";
        cssLink.type = "text/css";
        document.head.appendChild(cssLink);
    }

    function handleFileUpload() {
        const file = fileInput.files[0];
        if (!file) {
            showAlert('Please select an Excel file first', 'error');
            return;
        }

        showLoading(true);
        uploadBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload_class_record', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            console.log('Upload successful:', data);
            showAlert(
                `${data.message}<br>Professor: ${data.professor || 'N/A'}<br>Room: ${data.room || 'N/A'}`,
                'success'
            );
            loadClassTables();
        })
        .catch(error => {
            console.error('Upload error:', error);
            showAlert(`Upload failed: ${error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
            uploadBtn.disabled = false;
            fileInput.value = '';
        });
    }

    function loadClassTables() {
        showLoading(true);

        fetch('/api/class_tables')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load data: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderClassTables(data);
            // Also update the dropdown for manual input
            updateClassDropdown(data);
        })
        .catch(error => {
            console.error('Error loading class tables:', error);
            classInfoContainer.innerHTML = `
                <div class="error-message">
                    Failed to load class data: ${error.message}
                </div>
            `;
        })
        .finally(() => {
            showLoading(false);
        });
    }

function renderClassTables(tables) {
    if (!tables || tables.length === 0) {
        classInfoContainer.innerHTML = `
            <div class="no-data">
                No class records found. Upload an Excel file to get started.
            </div>
        `;
        return;
    }

    classInfoContainer.innerHTML = tables.map(table => `
        <div class="class-card">
            <div class="class-card-header">
                <h3>${table.display_name || table.table_name.replace(/_/g, ' ')}</h3>
                <div class="card-header-right">
                    <span class="student-count">${table.students.length} students</span>
                    <button class="delete-table-btn" data-table="${table.table_name}" title="Delete this class">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                            <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                        </svg>
                    </button>
                    <span class="toggle-icon">▼</span>
                </div>
            </div>
            <div class="class-card-body">
                <div class="table-controls">
                    <input type="text" class="search-input" placeholder="Search students...">
                </div>
                <div class="student-table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Student ID</th>
                                <th>Student Name</th>
                                <th>Year Level</th>
                                <th>Course</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${table.students.map(student => `
                                <tr>
                                    <td>${student.student_id || ''}</td>
                                    <td>${student.student_name || ''}</td>
                                    <td>${student.year_level || ''}</td>
                                    <td>${student.course || ''}</td>
                                    <td>
                                        <button class="delete-student-btn" 
                                                data-table="${table.table_name}" 
                                                data-student-id="${student.student_id || ''}"
                                                data-student-name="${student.student_name || ''}"
                                                title="Remove student from class">
                                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                                                <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                                <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                                            </svg>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `).join('');

    // Add toggle functionality
    document.querySelectorAll('.class-card-header').forEach(header => {
        header.addEventListener('click', function(e) {
            // Don't toggle if clicking on delete button
            if (e.target.closest('.delete-table-btn')) {
                return;
            }
            
            const body = this.nextElementSibling;
            const icon = this.querySelector('.toggle-icon');
            body.style.display = body.style.display === 'none' ? 'block' : 'none';
            icon.textContent = body.style.display === 'none' ? '▼' : '▲';
        });
    });

    // Add search functionality
    document.querySelectorAll('.search-input').forEach(input => {
        input.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const tableBody = this.closest('.table-controls').nextElementSibling.querySelector('tbody');
            
            tableBody.querySelectorAll('tr').forEach(row => {
                const rowText = row.textContent.toLowerCase();
                row.style.display = rowText.includes(searchTerm) ? '' : 'none';
            });
        });
    });


    // Add delete functionality
    document.querySelectorAll('.delete-table-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering the card header click
            const tableName = this.dataset.table;
            const displayName = this.closest('.class-card').querySelector('h3').textContent;
            
            if (confirm(`Are you sure you want to delete "${displayName}"?\nThis will permanently remove all student records in this class.`)) {
                deleteClassTable(tableName);
            }
        });
    });

    // Add delete student functionality
    document.querySelectorAll('.delete-student-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering other events
            const tableName = this.dataset.table;
            const studentId = this.dataset.studentId;
            const studentName = this.dataset.studentName;
            
            if (confirm(`Are you sure you want to remove "${studentName}" (${studentId}) from this class?`)) {
                deleteStudentFromClass(tableName, studentId);
            }
        });
    });
}

function deleteClassTable(tableName) {
    showLoading(true);
    
    fetch('/api/delete_class_table', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ table_name: tableName })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete table');
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            showAlert(`Successfully deleted table: ${tableName}`, 'success');
            loadClassTables(); // Refresh the list
        } else {
            throw new Error(data.error || 'Failed to delete table');
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        showAlert(`Delete failed: ${error.message}`, 'error');
    })
    .finally(() => {
        showLoading(false);
    });
}

    function exportTableToExcel(tableName) {
        showLoading(true);
        
        fetch(`/api/export_class_table?table_name=${encodeURIComponent(tableName)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to export table');
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${tableName}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        })
        .catch(error => {
            console.error('Export error:', error);
            showAlert(`Export failed: ${error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
        });
    }

    function showLoading(show) {
        if (show) {
            const loader = document.createElement('div');
            loader.className = 'loader';
            loader.id = 'loadingIndicator';
            document.body.appendChild(loader);
        } else {
            const loader = document.getElementById('loadingIndicator');
            if (loader) loader.remove();
        }
    }

    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = message;
        
        // Position the alert
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.padding = '15px';
        alertDiv.style.borderRadius = '5px';
        alertDiv.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
        alertDiv.style.zIndex = '1000';
        
        // Style based on type
        if (type === 'error') {
            alertDiv.style.backgroundColor = '#ffebee';
            alertDiv.style.color = '#c62828';
            alertDiv.style.border = '1px solid #ef9a9a';
        } else if (type === 'success') {
            alertDiv.style.backgroundColor = '#e8f5e9';
            alertDiv.style.color = '#2e7d32';
            alertDiv.style.border = '1px solid #a5d6a7';
        } else {
            alertDiv.style.backgroundColor = '#e3f2fd';
            alertDiv.style.color = '#1565c0';
            alertDiv.style.border = '1px solid #90caf9';
        }
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function addManualInputSection() {
        const container = document.querySelector('.container');
        const uploadContainer = document.querySelector('.upload-container');
        
        // Create manual input section
        const manualInputHTML = `
            <div class="manual-input-container">
                <h2>Manual Student Entry</h2>
                <div class="manual-input-form">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="manualClassSelect">Select Class:</label>
                            <select id="manualClassSelect">
                                <option value="">-- Select a Class --</option>
                            </select>
                        </div>
                        <button id="createNewClassBtn" class="btn-secondary">Create New Class</button>
                    </div>
                    
                    <div id="newClassForm" class="new-class-form" style="display: none;">
                        <h3>Create New Class</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="newClassName">Class Name:</label>
                                <input type="text" id="newClassName" placeholder="e.g., Computer Science 101">
                            </div>
                            <div class="form-group">
                                <label for="newClassProfessor">Professor:</label>
                                <input type="text" id="newClassProfessor" placeholder="Professor Name">
                            </div>
                        </div>
                        <div class="form-row">
                            <button id="saveNewClassBtn" class="btn-primary">Create Class</button>
                            <button id="cancelNewClassBtn" class="btn-secondary">Cancel</button>
                        </div>
                    </div>
                    
                    <div id="studentInputForm" class="student-input-form" style="display: none;">
                        <h3>Add Student from Database</h3>
                        <div class="form-row">
                            <div class="form-group" style="flex: 1;">
                                <label for="studentSelect">Select Student:</label>
                                <select id="studentSelect" required>
                                    <option value="">-- Select a Student --</option>
                                </select>
                            </div>
                        </div>
                        <div id="selectedStudentInfo" class="selected-student-info" style="display: none;">
                            <div class="student-info-card">
                                <h4>Selected Student Information</h4>
                                <div class="info-row">
                                    <span class="info-label">Student ID:</span>
                                    <span id="selectedStudentId"></span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Name:</span>
                                    <span id="selectedStudentName"></span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Course:</span>
                                    <span id="selectedStudentCourse"></span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Year Level:</span>
                                    <span id="selectedStudentYear"></span>
                                </div>
                            </div>
                        </div>
                        <div class="form-row">
                            <button id="addStudentBtn" class="btn-primary" disabled>Add Student to Class</button>
                            <button id="clearSelectionBtn" class="btn-secondary">Clear Selection</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Insert after upload container
        uploadContainer.insertAdjacentHTML('afterend', manualInputHTML);
        
        // Set up event listeners for manual input
        setupManualInputListeners();
        
        // Load classes for dropdown
        loadClassesForDropdown();
    }

    function setupManualInputListeners() {
        const classSelect = document.getElementById('manualClassSelect');
        const createNewClassBtn = document.getElementById('createNewClassBtn');
        const newClassForm = document.getElementById('newClassForm');
        const studentInputForm = document.getElementById('studentInputForm');
        const saveNewClassBtn = document.getElementById('saveNewClassBtn');
        const cancelNewClassBtn = document.getElementById('cancelNewClassBtn');
        const addStudentBtn = document.getElementById('addStudentBtn');
        const clearSelectionBtn = document.getElementById('clearSelectionBtn');
        const studentSelect = document.getElementById('studentSelect');

        // Class selection change
        classSelect.addEventListener('change', function() {
            if (this.value) {
                studentInputForm.style.display = 'block';
                newClassForm.style.display = 'none';
                // Load students when a class is selected
                loadStudentsForDropdown();
            } else {
                studentInputForm.style.display = 'none';
                clearStudentSelection();
            }
        });

        // Student selection change
        studentSelect.addEventListener('change', function() {
            if (this.value) {
                showSelectedStudentInfo(this.value);
                addStudentBtn.disabled = false;
            } else {
                hideSelectedStudentInfo();
                addStudentBtn.disabled = true;
            }
        });

        // Create new class button
        createNewClassBtn.addEventListener('click', function() {
            newClassForm.style.display = newClassForm.style.display === 'none' ? 'block' : 'none';
            studentInputForm.style.display = 'none';
            classSelect.value = '';
        });

        // Save new class
        saveNewClassBtn.addEventListener('click', handleCreateNewClass);

        // Cancel new class
        cancelNewClassBtn.addEventListener('click', function() {
            newClassForm.style.display = 'none';
            document.getElementById('newClassName').value = '';
            document.getElementById('newClassProfessor').value = '';
        });

        // Add student
        addStudentBtn.addEventListener('click', handleAddStudentFromDropdown);

        // Clear selection
        clearSelectionBtn.addEventListener('click', clearStudentSelection);
    }

    function loadClassesForDropdown() {
        fetch('/api/classes')
        .then(response => response.json())
        .then(data => {
            const classSelect = document.getElementById('manualClassSelect');
            
            // Clear existing options except the first one
            while (classSelect.children.length > 1) {
                classSelect.removeChild(classSelect.lastChild);
            }
            
            // Add classes to dropdown
            if (data.classes && data.classes.length > 0) {
                data.classes.forEach(classInfo => {
                    const option = document.createElement('option');
                    option.value = classInfo.table_name;
                    option.textContent = classInfo.display_name;
                    classSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading classes:', error);
        });
    }

    function updateClassDropdown(tables) {
        const classSelect = document.getElementById('manualClassSelect');
        if (!classSelect) return;
        
        // Preserve the currently selected value
        const currentSelection = classSelect.value;
        
        // Clear existing options except the first one
        while (classSelect.children.length > 1) {
            classSelect.removeChild(classSelect.lastChild);
        }
        
        // Add classes to dropdown
        if (tables && tables.length > 0) {
            tables.forEach(table => {
                const option = document.createElement('option');
                option.value = table.table_name;
                option.textContent = table.display_name || table.table_name.replace(/_/g, ' ');
                classSelect.appendChild(option);
            });
        }
        
        // Restore the previous selection if it still exists
        if (currentSelection) {
            classSelect.value = currentSelection;
        }
    }

    function handleCreateNewClass() {
        const className = document.getElementById('newClassName').value.trim();
        const professorName = document.getElementById('newClassProfessor').value.trim();
        
        if (!className || !professorName) {
            showAlert('Please fill in both Class Name and Professor fields', 'error');
            return;
        }
        
        // Create a basic class structure by creating a temporary CSV-like data
        const tableName = `${className.replace(/\s+/g, '_')}___${professorName.replace(/\s+/g, '_')}`;
        const sanitizedTableName = tableName.replace(/[^a-zA-Z0-9_]/g, '');
        
        // Create empty class table
        const classData = {
            table_name: sanitizedTableName,
            display_name: `${className} - ${professorName}`,
            students: []
        };
        
        // For now, we'll create it by adding it to our local state and refreshing
        // In a real implementation, you might want a dedicated API endpoint for creating empty classes
        
        showAlert(`Class "${className} - ${professorName}" will be created when you add the first student`, 'success');
        
        // Add to dropdown
        const classSelect = document.getElementById('manualClassSelect');
        const option = document.createElement('option');
        option.value = sanitizedTableName;
        option.textContent = `${className} - ${professorName}`;
        classSelect.appendChild(option);
        classSelect.value = sanitizedTableName;
        
        // Show student input form
        document.getElementById('studentInputForm').style.display = 'block';
        document.getElementById('newClassForm').style.display = 'none';
        
        // Clear form
        document.getElementById('newClassName').value = '';
        document.getElementById('newClassProfessor').value = '';
    }

    function handleAddStudent() {
        const classSelect = document.getElementById('manualClassSelect');
        const selectedClass = classSelect.value;
        
        if (!selectedClass) {
            showAlert('Please select a class first', 'error');
            return;
        }
        
        const studentData = {
            student_id: document.getElementById('studentId').value.trim(),
            student_name: document.getElementById('studentName').value.trim(),
            year_level: document.getElementById('yearLevel').value,
            course: document.getElementById('course').value.trim()
        };
        
        // Validate required fields
        if (!studentData.student_id || !studentData.student_name || !studentData.year_level || !studentData.course) {
            showAlert('Please fill in all required fields', 'error');
            return;
        }
        
        // Show loading
        showLoading(true);
        document.getElementById('addStudentBtn').disabled = true;
        
        // Send request to add student
        fetch(`/api/classes/${selectedClass}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(studentData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert(`Student ${studentData.student_name} added successfully!`, 'success');
            clearStudentForm();
            loadClassTables(); // Refresh the display
        })
        .catch(error => {
            console.error('Error adding student:', error);
            showAlert(`Failed to add student: ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
            document.getElementById('addStudentBtn').disabled = false;
        });
    }

    function clearStudentForm() {
        document.getElementById('studentId').value = '';
        document.getElementById('studentName').value = '';
        document.getElementById('yearLevel').value = '';
        document.getElementById('course').value = '';
    }

    function deleteStudentFromClass(tableName, studentId) {
        showLoading(true);
        
        fetch(`/api/classes/${tableName}/students/${studentId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert(data.message, 'success');
            loadClassTables(); // Refresh the list
        })
        .catch(error => {
            console.error('Delete student error:', error);
            showAlert(`Failed to remove student: ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
        });
    }

    // New functions for student dropdown functionality
    function loadStudentsForDropdown() {
        fetch('/api/students_status')
        .then(response => response.json())
        .then(students => {
            const studentSelect = document.getElementById('studentSelect');
            
            // Clear existing options except the first one
            while (studentSelect.children.length > 1) {
                studentSelect.removeChild(studentSelect.lastChild);
            }
            
            // Add students to dropdown
            if (students && students.length > 0) {
                students.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.student_id;
                    option.textContent = student.name;
                    option.dataset.course = student.course;
                    option.dataset.year = student.year;
                    studentSelect.appendChild(option);
                });
            }
        })
        .catch(error => {
            console.error('Error loading students:', error);
            showAlert('Failed to load students from database', 'error');
        });
    }

    function showSelectedStudentInfo(studentId) {
        const studentSelect = document.getElementById('studentSelect');
        const selectedOption = studentSelect.querySelector(`option[value="${studentId}"]`);
        
        if (selectedOption) {
            // Update the student info display
            document.getElementById('selectedStudentId').textContent = studentId;
            document.getElementById('selectedStudentName').textContent = selectedOption.textContent;
            document.getElementById('selectedStudentCourse').textContent = selectedOption.dataset.course || 'N/A';
            document.getElementById('selectedStudentYear').textContent = selectedOption.dataset.year || 'N/A';
            
            // Show the info section
            document.getElementById('selectedStudentInfo').style.display = 'block';
        }
    }

    function hideSelectedStudentInfo() {
        document.getElementById('selectedStudentInfo').style.display = 'none';
    }

    function clearStudentSelection() {
        document.getElementById('studentSelect').value = '';
        hideSelectedStudentInfo();
        document.getElementById('addStudentBtn').disabled = true;
    }

    function handleAddStudentFromDropdown() {
        const classSelect = document.getElementById('manualClassSelect');
        const studentSelect = document.getElementById('studentSelect');
        const selectedClass = classSelect.value;
        const selectedStudentId = studentSelect.value;
        
        if (!selectedClass) {
            showAlert('Please select a class first', 'error');
            return;
        }
        
        if (!selectedStudentId) {
            showAlert('Please select a student', 'error');
            return;
        }
        
        const selectedOption = studentSelect.querySelector(`option[value="${selectedStudentId}"]`);
        const studentData = {
            student_id: selectedStudentId,
            student_name: selectedOption.textContent,
            year_level: selectedOption.dataset.year,
            course: selectedOption.dataset.course
        };
        
        // Show loading
        showLoading(true);
        document.getElementById('addStudentBtn').disabled = true;
        
        // Send request to add student
        fetch(`/api/classes/${selectedClass}/students`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(studentData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert(`Student ${studentData.student_name} added to class successfully!`, 'success');
            clearStudentSelection();
            // Preserve the selected class when refreshing
            const selectedClass = document.getElementById('manualClassSelect').value;
            loadClassTables(); // Refresh the display
            // Restore the selected class after refresh
            setTimeout(() => {
                if (selectedClass) {
                    document.getElementById('manualClassSelect').value = selectedClass;
                    // Also reload students for the dropdown
                    loadStudentsForDropdown();
                }
            }, 100);
        })
        .catch(error => {
            console.error('Error adding student:', error);
            showAlert(`Failed to add student: ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
            document.getElementById('addStudentBtn').disabled = false;
        });
    }
});