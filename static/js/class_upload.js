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
                            </tr>
                        </thead>
                        <tbody>
                            ${table.students.map(student => `
                                <tr>
                                    <td>${student.student_id || ''}</td>
                                    <td>${student.student_name || ''}</td>
                                    <td>${student.year_level || ''}</td>
                                    <td>${student.course || ''}</td>
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
});