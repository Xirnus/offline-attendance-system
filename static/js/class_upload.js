document.addEventListener('DOMContentLoaded', function() {
    const classInfoContainer = document.getElementById('classInfoContainer');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');

    // Bulk selection state - declare at the top
    let currentSelectionMode = 'single'; // 'single' or 'bulk'
    let allStudents = [];
    let selectedStudents = new Set();
    let filteredStudents = [];

    // Initialize the page
    initPage();

    function initPage() {
        console.log('Initializing class upload page...');
        
        // Load CSS
        loadCSS();
        
        // Set up event listeners
        uploadBtn.addEventListener('click', handleFileUpload);
        
        // Load existing class data
        loadClassTables();
        
        // Set up modal functionality
        setupModalListeners();
        console.log('Modal listeners set up.');
    }

    function loadCSS() {
        // CSS is already loaded in the HTML file, so this function is not needed
        // but we'll keep it for compatibility
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
        formData.append('use_optimized', 'true'); // Use optimized schema

        fetch('/upload_class_record', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            console.log('Upload successful:', data);
            showAlert(
                `${data.message}<br>Professor: ${data.professor || 'N/A'}`,
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

        fetch('/api/optimized/classes')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load data: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            renderClassTables(data.classes || []);
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

    function renderClassTables(classes) {
        const classInfoContainer = document.getElementById('classInfoContainer');
        
        if (!classes || classes.length === 0) {
            classInfoContainer.innerHTML = `
                <div style="
                    text-align: center; 
                    padding: 40px 20px; 
                    color: #666; 
                    background: #f8f9fa; 
                    border-radius: 8px;
                    border: 1px dashed #dee2e6;
                ">
                    No class records found. Upload an Excel file to get started.
                </div>
            `;
            return;
        }

        // Convert classes to have students loaded
        const classPromises = classes.map(async (classInfo) => {
            try {
                const response = await fetch(`/api/optimized/classes/${classInfo.class_id}/students`);
                const studentData = await response.json();
                return {
                    ...classInfo,
                    students: studentData.students || [],
                    display_name: `${classInfo.class_name} - ${classInfo.professor_name}`,
                    class_id: classInfo.class_id
                };
            } catch (error) {
                console.error(`Error loading students for class ${classInfo.class_id}:`, error);
                return {
                    ...classInfo,
                    students: [],
                    display_name: `${classInfo.class_name} - ${classInfo.professor_name}`,
                    class_id: classInfo.class_id
                };
            }
        });

        Promise.all(classPromises).then(classesWithStudents => {
            classInfoContainer.innerHTML = classesWithStudents.map(classInfo => `
                <div class="class-card" style="
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    overflow: hidden;
                ">
                    <div class="class-card-header" style="
                        background: #28156E;
                        color: white;
                        padding: 12px 15px;
                        cursor: pointer;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <h3 style="margin: 0; font-size: 16px; font-weight: 600;">${classInfo.display_name}</h3>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 12px; background: #ffc107; color: #333; padding: 2px 8px; border-radius: 12px; font-weight: 600;">${classInfo.students.length} students</span>
                            <button class="delete-class-btn" data-class-id="${classInfo.class_id}" title="Delete this class" style="
                                background: transparent;
                                border: none;
                                color: #dc3545;
                                cursor: pointer;
                                padding: 4px;
                                border-radius: 4px;
                                display: flex;
                                align-items: center;
                            ">
                                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                                </svg>
                            </button>
                            <span class="toggle-icon" style="font-size: 14px;">▼</span>
                        </div>
                    </div>
                    <div class="class-card-body" style="display: none;">
                        <div class="table-controls" style="padding: 10px 15px; background: white;">
                            <input type="text" class="search-input" placeholder="Search students..." style="
                                width: 100%;
                                padding: 6px 10px;
                                border: 1px solid #dee2e6;
                                border-radius: 4px;
                                font-size: 13px;
                            ">
                        </div>
                        <div class="student-table-container" style="max-height: 300px; overflow-y: auto;">
                            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                                <thead>
                                    <tr style="background: #f8f9fa;">
                                        <th style="padding: 8px 10px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 600;">Student ID</th>
                                        <th style="padding: 8px 10px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 600;">Name</th>
                                        <th style="padding: 8px 10px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 600;">Year</th>
                                        <th style="padding: 8px 10px; text-align: left; border-bottom: 1px solid #dee2e6; font-weight: 600;">Course</th>
                                        <th style="padding: 8px 10px; text-align: center; border-bottom: 1px solid #dee2e6; font-weight: 600; width: 60px;">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${classInfo.students.map(student => `
                                        <tr style="border-bottom: 1px solid #f1f3f4;">
                                            <td style="padding: 6px 10px;">${student.student_id || ''}</td>
                                            <td style="padding: 6px 10px;">${student.name || student.student_name || ''}</td>
                                            <td style="padding: 6px 10px;">${student.year || student.year_level || ''}</td>
                                            <td style="padding: 6px 10px;">${student.course || ''}</td>
                                            <td style="padding: 6px 10px; text-align: center;">
                                                <button class="delete-student-btn" 
                                                        data-class-id="${classInfo.class_id}" 
                                                        data-student-id="${student.student_id || ''}"
                                                        data-student-name="${student.name || student.student_name || ''}"
                                                        title="Remove student from class"
                                                        style="
                                                            background: transparent;
                                                            border: none;
                                                            color: #dc3545;
                                                            cursor: pointer;
                                                            padding: 2px;
                                                            border-radius: 2px;
                                                        ">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
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
                    if (e.target.closest('.delete-class-btn')) {
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

            // Add delete functionality for classes
            document.querySelectorAll('.delete-class-btn').forEach(button => {
                button.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent triggering the card header click
                    const classId = this.dataset.classId;
                    const displayName = this.closest('.class-card').querySelector('h3').textContent;
                    
                    if (confirm(`Are you sure you want to delete "${displayName}"?\nThis will permanently remove the class and all student enrollments.`)) {
                        deleteClass(classId);
                    }
                });
            });

            // Add delete student functionality
            document.querySelectorAll('.delete-student-btn').forEach(button => {
                button.addEventListener('click', function(e) {
                    e.stopPropagation(); // Prevent triggering other events
                    const classId = this.dataset.classId;
                    const studentId = this.dataset.studentId;
                    const studentName = this.dataset.studentName;
                    
                    if (confirm(`Are you sure you want to remove "${studentName}" (${studentId}) from this class?`)) {
                        deleteStudentFromClass(classId, studentId);
                    }
                });
            });
        });
    }

    function deleteClass(classId) {
        showLoading(true);
        
        fetch(`/api/optimized/classes/${classId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert('Class deleted successfully!', 'success');
            loadClassTables(); // Refresh the display
        })
        .catch(error => {
            console.error('Error deleting class:', error);
            showAlert(`Failed to delete class: ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
        });
    }

    function deleteStudentFromClass(classId, studentId) {
        showLoading(true);
        
        fetch(`/api/optimized/classes/${classId}/unenroll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_ids: [studentId]
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert('Student removed from class successfully!', 'success');
            loadClassTables(); // Refresh the display
        })
        .catch(error => {
            console.error('Error removing student from class:', error);
            showAlert(`Failed to remove student: ${error.error || error.message}`, 'error');
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
        } else if (type === 'warning') {
            alertDiv.style.backgroundColor = '#fff3e0';
            alertDiv.style.color = '#ef6c00';
            alertDiv.style.border = '1px solid #ffcc02';
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

    // Modal functionality - define setupModalFormHandlers first
    function setupModalFormHandlers() {
        const classSelect = document.getElementById('modalClassSelect');
        const createNewClassBtn = document.getElementById('modalCreateNewClassBtn');
        const saveNewClassBtn = document.getElementById('modalSaveNewClassBtn');
        const cancelNewClassBtn = document.getElementById('modalCancelNewClassBtn');
        const studentSelect = document.getElementById('modalStudentSelect');
        const addStudentBtn = document.getElementById('modalAddStudentBtn');
        const clearSelectionBtn = document.getElementById('modalClearSelectionBtn');
        
        // Tab switching
        const singleSelectTab = document.getElementById('singleSelectTab');
        const bulkSelectTab = document.getElementById('bulkSelectTab');
        
        // Bulk selection controls
        const selectAllBtn = document.getElementById('selectAllStudentsBtn');
        const clearAllBtn = document.getElementById('clearAllStudentsBtn');
        const searchInput = document.getElementById('studentSearchInput');
        
        // Tab switching functionality
        if (singleSelectTab && bulkSelectTab) {
            singleSelectTab.addEventListener('click', function() {
                switchToSingleSelection();
            });
            
            bulkSelectTab.addEventListener('click', function() {
                switchToBulkSelection();
            });
        }
        
        // Bulk selection controls
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', function() {
                selectAllVisibleStudents();
            });
        }
        
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', function() {
                clearAllSelectedStudents();
            });
        }
        
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                filterStudentList(this.value);
            });
        }
        
        // Class selection handler
        if (classSelect) {
            classSelect.addEventListener('change', function() {
                const selectedClass = this.value;
                if (selectedClass) {
                    showModalStudentForm();
                } else {
                    hideModalStudentForm();
                }
            });
        }
        
        // Create new class button
        if (createNewClassBtn) {
            createNewClassBtn.addEventListener('click', function() {
                showModalNewClassForm();
            });
        }
        
        // Save new class button
        if (saveNewClassBtn) {
            saveNewClassBtn.addEventListener('click', function() {
                handleModalCreateClass();
            });
        }
        
        // Cancel new class button
        if (cancelNewClassBtn) {
            cancelNewClassBtn.addEventListener('click', function() {
                hideModalNewClassForm();
            });
        }
        
        // Student selection handler (single mode)
        if (studentSelect) {
            studentSelect.addEventListener('change', function() {
                const selectedStudent = this.value;
                if (selectedStudent) {
                    showModalSelectedStudentInfo(selectedStudent);
                    updateAddButtonState();
                } else {
                    hideModalSelectedStudentInfo();
                    updateAddButtonState();
                }
            });
        }
        
        // Add student button
        if (addStudentBtn) {
            addStudentBtn.addEventListener('click', function() {
                handleModalAddStudent();
            });
        }
        
        // Clear selection button
        if (clearSelectionBtn) {
            clearSelectionBtn.addEventListener('click', function() {
                clearModalStudentSelection();
            });
        }
    }

    function setupModalListeners() {
        const modal = document.getElementById('manualStudentEntryModal');
        const openModalBtn = document.getElementById('openManualEntryBtn');
        const closeButton = modal.querySelector('.close');
        
        // Open modal
        if (openModalBtn) {
            openModalBtn.addEventListener('click', function() {
                openManualEntryModal();
            });
        }
        
        // Close modal when clicking X
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                closeModal();
            });
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal();
            }
        });
        
        // Set up modal form handlers
        setupModalFormHandlers();
    }
    
    function openManualEntryModal() {
        const modal = document.getElementById('manualStudentEntryModal');
        modal.style.display = 'block';
        
        // Reset modal state
        resetModalState();
        
        // Load data for dropdowns
        loadClassesForModal();
        loadStudentsForModal();
    }
    
    function closeModal() {
        const modal = document.getElementById('manualStudentEntryModal');
        modal.style.display = 'none';
        resetModalState();
    }

    function resetModalState() {
        // Hide forms initially
        document.getElementById('modalNewClassForm').style.display = 'none';
        document.getElementById('modalStudentForm').style.display = 'none';
        document.getElementById('modalSelectedStudentInfo').style.display = 'none';
        document.getElementById('selectedStudentsSummary').style.display = 'none';
        
        // Clear form inputs
        document.getElementById('modalClassSelect').value = '';
        document.getElementById('modalStudentSelect').value = '';
        document.getElementById('modalNewClassName').value = '';
        document.getElementById('modalNewClassProfessor').value = '';
        document.getElementById('studentSearchInput').value = '';
        
        // Reset selection mode to single
        currentSelectionMode = 'single';
        switchToSingleSelection();
        
        // Clear selections
        selectedStudents.clear();
        
        // Reset button states
        document.getElementById('modalAddStudentBtn').disabled = true;
        
        // Clear student info display
        clearModalStudentInfo();
    }
    
    // Tab switching functions
    function switchToSingleSelection() {
        currentSelectionMode = 'single';
        
        // Update tab appearance
        document.getElementById('singleSelectTab').classList.add('active');
        document.getElementById('bulkSelectTab').classList.remove('active');
        
        // Show/hide appropriate sections
        document.getElementById('singleStudentSelection').style.display = 'block';
        document.getElementById('bulkStudentSelection').style.display = 'none';
        
        // Update add button
        updateAddButtonState();
    }
    
    function switchToBulkSelection() {
        currentSelectionMode = 'bulk';
        
        // Update tab appearance
        document.getElementById('singleSelectTab').classList.remove('active');
        document.getElementById('bulkSelectTab').classList.add('active');
        
        // Show/hide appropriate sections
        document.getElementById('singleStudentSelection').style.display = 'none';
        document.getElementById('bulkStudentSelection').style.display = 'block';
        
        // Render bulk student list if not already done
        if (allStudents.length > 0 && document.getElementById('bulkStudentList').children.length === 0) {
            renderBulkStudentList(allStudents);
        }
        
        // Update add button
        updateAddButtonState();
    }
    
    function renderBulkStudentList(students) {
        const bulkStudentList = document.getElementById('bulkStudentList');
        filteredStudents = [...students];
        
        bulkStudentList.innerHTML = '';
        
        if (students.length === 0) {
            bulkStudentList.innerHTML = '<div class="no-students">No students available</div>';
            return;
        }
        
        students.forEach(student => {
            const studentItem = document.createElement('div');
            studentItem.className = 'bulk-student-item';
            studentItem.dataset.studentId = student.student_id;
            
            const isSelected = selectedStudents.has(student.student_id);
            
            studentItem.innerHTML = `
                <div class="student-checkbox-wrapper">
                    <input type="checkbox" 
                           id="student_${student.student_id}" 
                           class="student-checkbox" 
                           value="${student.student_id}"
                           ${isSelected ? 'checked' : ''}>
                    <label for="student_${student.student_id}" class="student-label">
                        <div class="student-info">
                            <div class="student-id-name">
                                <strong>${student.student_id}</strong> - ${student.name}
                            </div>
                            <div class="student-details">
                                ${student.course || 'N/A'} • Year ${student.year || student.year_level || 'N/A'}
                            </div>
                        </div>
                    </label>
                </div>
            `;
            
            // Add event listener to checkbox
            const checkbox = studentItem.querySelector('.student-checkbox');
            checkbox.addEventListener('change', function() {
                handleStudentCheckboxChange(student.student_id, this.checked);
            });
            
            bulkStudentList.appendChild(studentItem);
        });
    }
    
    function handleStudentCheckboxChange(studentId, isChecked) {
        if (isChecked) {
            selectedStudents.add(studentId);
        } else {
            selectedStudents.delete(studentId);
        }
        
        updateSelectedStudentsSummary();
        updateAddButtonState();
    }
    
    function selectAllVisibleStudents() {
        const visibleCheckboxes = document.querySelectorAll('#bulkStudentList .student-checkbox:not([style*="display: none"])');
        
        visibleCheckboxes.forEach(checkbox => {
            const studentId = checkbox.value;
            if (!checkbox.checked) {
                checkbox.checked = true;
                selectedStudents.add(studentId);
            }
        });
        
        updateSelectedStudentsSummary();
        updateAddButtonState();
    }
    
    function clearAllSelectedStudents() {
        selectedStudents.clear();
        
        const allCheckboxes = document.querySelectorAll('#bulkStudentList .student-checkbox');
        allCheckboxes.forEach(checkbox => {
            checkbox.checked = false;
        });
        
        updateSelectedStudentsSummary();
        updateAddButtonState();
    }
    
    function filterStudentList(searchTerm) {
        const searchLower = searchTerm.toLowerCase();
        const studentItems = document.querySelectorAll('#bulkStudentList .bulk-student-item');
        
        studentItems.forEach(item => {
            const studentLabel = item.querySelector('.student-label').textContent.toLowerCase();
            const matches = studentLabel.includes(searchLower);
            item.style.display = matches ? 'block' : 'none';
        });
    }
    
    function updateSelectedStudentsSummary() {
        const summaryDiv = document.getElementById('selectedStudentsSummary');
        const countSpan = document.getElementById('selectedCount');
        const listDiv = document.getElementById('selectedStudentsList');
        
        const selectedCount = selectedStudents.size;
        countSpan.textContent = selectedCount;
        
        if (selectedCount === 0) {
            summaryDiv.style.display = 'none';
            return;
        }
        
        summaryDiv.style.display = 'block';
        
        // Show selected students
        listDiv.innerHTML = '';
        const selectedArray = Array.from(selectedStudents);
        
        selectedArray.forEach(studentId => {
            const student = allStudents.find(s => s.student_id === studentId);
            if (student) {
                const studentTag = document.createElement('div');
                studentTag.className = 'selected-student-tag';
                studentTag.innerHTML = `
                    <span>${student.student_id} - ${student.name}</span>
                    <button type="button" class="remove-student-btn" onclick="removeSelectedStudent('${studentId}')">×</button>
                `;
                listDiv.appendChild(studentTag);
            }
        });
    }
    
    function removeSelectedStudent(studentId) {
        selectedStudents.delete(studentId);
        
        // Uncheck the checkbox
        const checkbox = document.querySelector(`#student_${studentId}`);
        if (checkbox) {
            checkbox.checked = false;
        }
        
        updateSelectedStudentsSummary();
        updateAddButtonState();
    }
    
    function updateAddButtonState() {
        const addButton = document.getElementById('modalAddStudentBtn');
        const addButtonText = document.getElementById('addButtonText');
        const classSelected = document.getElementById('modalClassSelect').value;
        
        if (!classSelected) {
            addButton.disabled = true;
            addButtonText.textContent = 'Add Student';
            return;
        }
        
        if (currentSelectionMode === 'single') {
            const studentSelected = document.getElementById('modalStudentSelect').value;
            addButton.disabled = !studentSelected;
            addButtonText.textContent = 'Add Student';
        } else {
            const selectedCount = selectedStudents.size;
            addButton.disabled = selectedCount === 0;
            addButtonText.textContent = selectedCount === 0 ? 'Add Students' : 
                                      selectedCount === 1 ? 'Add 1 Student' : 
                                      `Add ${selectedCount} Students`;
        }
    }

    function loadClassesForModal() {
        fetch('/api/optimized/classes')
        .then(response => response.json())
        .then(data => {
            const classSelect = document.getElementById('modalClassSelect');
            const classes = data.classes || [];
            
            // Clear existing options (except first)
            classSelect.innerHTML = '<option value="">-- Select a Class --</option>';
            
            // Add class options
            classes.forEach(classInfo => {
                const option = document.createElement('option');
                option.value = classInfo.class_id;
                option.textContent = `${classInfo.class_name} - ${classInfo.professor_name}`;
                classSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading classes for modal:', error);
            showAlert('Failed to load classes', 'error');
        });
    }
    
    function loadStudentsForModal() {
        fetch('/get_students')
        .then(response => response.json())
        .then(data => {
            const studentSelect = document.getElementById('modalStudentSelect');
            const students = data.students || [];
            
            // Store all students for bulk selection
            allStudents = students;
            
            // Clear existing options (except first)
            studentSelect.innerHTML = '<option value="">-- Select a Student --</option>';
            
            // Add student options for single selection
            students.forEach(student => {
                const option = document.createElement('option');
                option.value = student.student_id;
                option.textContent = `${student.student_id} - ${student.name}`;
                option.dataset.name = student.name;
                option.dataset.course = student.course || '';
                option.dataset.year = student.year || student.year_level || '';
                studentSelect.appendChild(option);
            });
            
            // If in bulk mode, render the bulk list
            if (currentSelectionMode === 'bulk') {
                renderBulkStudentList(students);
            }
        })
        .catch(error => {
            console.error('Error loading students for modal:', error);
            showAlert('Failed to load students', 'error');
        });
    }
    
    function showModalNewClassForm() {
        document.getElementById('modalNewClassForm').style.display = 'block';
        document.getElementById('modalStudentForm').style.display = 'none';
    }
    
    function hideModalNewClassForm() {
        document.getElementById('modalNewClassForm').style.display = 'none';
        document.getElementById('modalNewClassName').value = '';
        document.getElementById('modalNewClassProfessor').value = '';
    }
    
    function showModalStudentForm() {
        document.getElementById('modalStudentForm').style.display = 'block';
        document.getElementById('modalNewClassForm').style.display = 'none';
    }
    
    function hideModalStudentForm() {
        document.getElementById('modalStudentForm').style.display = 'none';
        hideModalSelectedStudentInfo();
    }
    
    function showModalSelectedStudentInfo(studentId) {
        const studentSelect = document.getElementById('modalStudentSelect');
        const selectedOption = studentSelect.querySelector(`option[value="${studentId}"]`);
        
        if (selectedOption) {
            document.getElementById('modalSelectedStudentId').textContent = studentId;
            document.getElementById('modalSelectedStudentName').textContent = selectedOption.dataset.name;
            document.getElementById('modalSelectedStudentCourse').textContent = selectedOption.dataset.course || 'N/A';
            document.getElementById('modalSelectedStudentYear').textContent = selectedOption.dataset.year || 'N/A';
            
            document.getElementById('modalSelectedStudentInfo').style.display = 'block';
        }
    }
    
    function hideModalSelectedStudentInfo() {
        document.getElementById('modalSelectedStudentInfo').style.display = 'none';
        clearModalStudentInfo();
    }
    
    function clearModalStudentInfo() {
        document.getElementById('modalSelectedStudentId').textContent = '';
        document.getElementById('modalSelectedStudentName').textContent = '';
        document.getElementById('modalSelectedStudentCourse').textContent = '';
        document.getElementById('modalSelectedStudentYear').textContent = '';
    }
    
    function clearModalStudentSelection() {
        document.getElementById('modalStudentSelect').value = '';
        hideModalSelectedStudentInfo();
        document.getElementById('modalAddStudentBtn').disabled = true;
    }
    
    function handleModalCreateClass() {
        const className = document.getElementById('modalNewClassName').value.trim();
        const professorName = document.getElementById('modalNewClassProfessor').value.trim();
        
        if (!className || !professorName) {
            showAlert('Please fill in both class name and professor name', 'error');
            return;
        }
        
        showLoading(true);
        document.getElementById('modalSaveNewClassBtn').disabled = true;
        
        fetch('/api/optimized/classes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                class_name: className,
                professor_name: professorName
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            showAlert(`Class "${className}" created successfully!`, 'success');
            hideModalNewClassForm();
            
            // Reload classes for modal and main view
            loadClassesForModal();
            loadClassTables();
            
            // Select the newly created class
            setTimeout(() => {
                document.getElementById('modalClassSelect').value = data.class_id;
                showModalStudentForm();
            }, 100);
        })
        .catch(error => {
            console.error('Error creating class:', error);
            showAlert(`Failed to create class: ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
            document.getElementById('modalSaveNewClassBtn').disabled = false;
        });
    }
    
    function handleModalAddStudent() {
        const classId = document.getElementById('modalClassSelect').value;
        
        if (!classId) {
            showAlert('Please select a class', 'error');
            return;
        }
        
        let studentIds = [];
        
        if (currentSelectionMode === 'single') {
            const studentId = document.getElementById('modalStudentSelect').value;
            if (!studentId) {
                showAlert('Please select a student', 'error');
                return;
            }
            studentIds = [studentId];
        } else {
            if (selectedStudents.size === 0) {
                showAlert('Please select at least one student', 'error');
                return;
            }
            studentIds = Array.from(selectedStudents);
        }
        
        showLoading(true);
        document.getElementById('modalAddStudentBtn').disabled = true;
        
        fetch(`/api/optimized/classes/${classId}/enroll`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_ids: studentIds
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err));
            }
            return response.json();
        })
        .then(data => {
            const totalRequested = data.total_requested || studentIds.length;
            const enrolledCount = data.enrolled_count || 0;
            const alreadyEnrolled = totalRequested - enrolledCount;
            
            let message = '';
            let alertType = 'success';
            
            if (enrolledCount === 0 && alreadyEnrolled > 0) {
                // All students were already enrolled
                if (totalRequested === 1) {
                    message = 'Student is already enrolled in this class.';
                } else {
                    message = `All ${totalRequested} students are already enrolled in this class.`;
                }
                alertType = 'warning';
            } else if (enrolledCount > 0 && alreadyEnrolled > 0) {
                // Some students enrolled, some already enrolled
                if (totalRequested === 1) {
                    message = 'Student enrolled successfully!';
                } else {
                    message = `${enrolledCount} students enrolled successfully. ${alreadyEnrolled} student(s) were already enrolled in this class.`;
                }
                alertType = 'success';
            } else if (enrolledCount > 0) {
                // All students enrolled successfully
                if (enrolledCount === 1) {
                    message = 'Student enrolled in class successfully!';
                } else {
                    message = `${enrolledCount} students enrolled in class successfully!`;
                }
                alertType = 'success';
            } else {
                // No students enrolled (shouldn't happen, but just in case)
                message = 'No students were enrolled.';
                alertType = 'error';
            }
            
            showAlert(message, alertType);
            
            // Clear selections
            if (currentSelectionMode === 'single') {
                clearModalStudentSelection();
            } else {
                clearAllSelectedStudents();
            }
            
            // Reload class data
            loadClassTables();
        })
        .catch(error => {
            console.error('Error enrolling student(s):', error);
            showAlert(`Failed to enroll student(s): ${error.error || error.message}`, 'error');
        })
        .finally(() => {
            showLoading(false);
            document.getElementById('modalAddStudentBtn').disabled = false;
        });
    }

    // Make removeSelectedStudent available globally for onclick handlers
    window.removeSelectedStudent = removeSelectedStudent;
});
