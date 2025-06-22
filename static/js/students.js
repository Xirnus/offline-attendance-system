document.addEventListener('DOMContentLoaded', function() {
    const importBtn = document.getElementById('import-csv');
    const clearBtn = document.getElementById('clear-table');
    const csvInput = document.getElementById('csv-input');
    const tableBody = document.getElementById('table-body');

    // Load students on page load
    loadStudents();

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
        fetch('/get_students')
            .then(response => response.json())
            .then(data => {
                tableBody.innerHTML = '';
                data.students.forEach(student => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${student.student_id}</td>
                        <td>${student.name}</td>
                        <td>${student.year}</td>
                        <td>Present</td>
                        <td>-</td>
                        <td>0</td>
                        <td>100%</td>
                    `;
                    tableBody.appendChild(tr);
                });
            });
    }
});