// Combined Analytics & Reports JavaScript Module

// Global chart variables for analytics
let trendsChart, lateChart, courseChart, weeklyChart;

// Initialize the combined page
document.addEventListener('DOMContentLoaded', function() {
    initializeAnalytics();
    initializeReports();
    setupTabSwitching();
    loadInitialData();
});

// Tab switching functionality
function setupTabSwitching() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabName = this.textContent.includes('Analytics') ? 'analytics' : 'reports';
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to appropriate button
    const activeButton = document.querySelector(`.tab-button[onclick*="${tabName}"]`) ||
                        (tabName === 'analytics' ? document.querySelector('.tab-button:first-child') : 
                         document.querySelector('.tab-button:last-child'));
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Load tab-specific content
    if (tabName === 'analytics') {
        loadAnalyticsData();
    } else if (tabName === 'reports') {
        initializeReportsTab();
    }
}

// ===============================
// ANALYTICS FUNCTIONALITY
// ===============================

function initializeAnalytics() {
    initializeCharts();
    setupAnalyticsEventListeners();
    loadAnalyticsData();
}

function setupAnalyticsEventListeners() {
    const eventHandlers = {
        'refresh-trends': refreshTrends,
        'refresh-courses': loadCourseComparison,
        'trend-period': refreshTrends,
        'refresh-trends-graph': refreshTrends,
        'refresh-late-graph': loadLateArrivalData,
        'refresh-course-graph': loadCourseComparison,
        'refresh-weekly-graph': loadWeeklyPatterns,
        'refresh-top-performers-table': loadTopPerformers,
        'refresh-issues-table': loadAttendanceIssues
    };

    addEventListeners(eventHandlers);
}

function initializeCharts() {
    // Attendance Trends Chart
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx) {
        trendsChart = new Chart(trendsCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Attendance Rate',
                    data: [],
                    borderColor: '#28156E',
                    backgroundColor: 'rgba(40, 21, 110, 0.1)',
                    tension: 0.1,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Late Arrival Chart
    const lateCtx = document.getElementById('lateChart');
    if (lateCtx) {
        lateChart = new Chart(lateCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['On Time', 'Late (< 5 min)', 'Late (5-15 min)', 'Very Late (> 15 min)'],
                datasets: [{
                    data: [70, 15, 10, 5],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#fd7e14',
                        '#dc3545'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    }

    // Course Comparison Chart
    const courseCtx = document.getElementById('courseChart');
    if (courseCtx) {
        courseChart = new Chart(courseCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Attendance Rate',
                    data: [],
                    backgroundColor: '#28156E',
                    borderColor: '#28156E',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    // Weekly Patterns Chart
    const weeklyCtx = document.getElementById('weeklyChart');
    if (weeklyCtx) {
        weeklyChart = new Chart(weeklyCtx.getContext('2d'), {
            type: 'radar',
            data: {
                labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                datasets: [{
                    label: 'Attendance Rate',
                    data: [85, 92, 88, 90, 78, 65, 45],
                    fill: true,
                    backgroundColor: 'rgba(40, 21, 110, 0.2)',
                    borderColor: '#28156E',
                    pointBackgroundColor: '#28156E',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#28156E'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
}

async function loadAnalyticsData() {
    try {
        loadOverviewStats();
        refreshTrends();
        loadLateArrivalData();
        loadCourseComparison();
        loadWeeklyPatterns();
        loadTopPerformers();
        loadAttendanceIssues();
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

async function loadOverviewStats() {
    try {
        const response = await fetch('/api/analytics/overview');
        const data = await response.json();
        
        if (data.success) {
            updateElement('total-students', data.stats.total_students || '0');
            updateElement('avg-attendance', (data.stats.avg_attendance || 0) + '%');
            updateElement('active-courses', data.stats.active_courses || '0');
            updateElement('weekly-trend', data.stats.weekly_trend || 'N/A');
        }
    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

async function refreshTrends() {
    try {
        const period = getElementValue('trend-period') || 'weekly';
        const response = await fetch(`/api/analytics/trends?period=${period}`);
        const data = await response.json();
        
        if (data.success && trendsChart) {
            trendsChart.data.labels = data.trends.labels || [];
            trendsChart.data.datasets[0].data = data.trends.data || [];
            trendsChart.update();
        }
    } catch (error) {
        console.error('Error loading trends data:', error);
    }
}

async function loadLateArrivalData() {
    try {
        const response = await fetch('/api/analytics/late-arrivals');
        const data = await response.json();
        
        if (data.success) {
            updateElement('late-today', data.stats.late_today || '0');
            updateElement('avg-late-time', data.stats.avg_late_time || 'N/A');
            
            if (lateChart && data.chart_data) {
                lateChart.data.datasets[0].data = data.chart_data;
                lateChart.update();
            }
        }
    } catch (error) {
        console.error('Error loading late arrival data:', error);
    }
}

async function loadCourseComparison() {
    try {
        const response = await fetch('/api/analytics/courses');
        const data = await response.json();
        
        if (data.success && courseChart) {
            courseChart.data.labels = data.courses.map(c => c.name) || [];
            courseChart.data.datasets[0].data = data.courses.map(c => c.attendance_rate) || [];
            courseChart.update();
        }
    } catch (error) {
        console.error('Error loading course comparison data:', error);
    }
}

async function loadWeeklyPatterns() {
    try {
        const response = await fetch('/api/analytics/weekly-patterns');
        const data = await response.json();
        
        if (data.success && weeklyChart) {
            weeklyChart.data.datasets[0].data = data.patterns || [];
            weeklyChart.update();
        }
    } catch (error) {
        console.error('Error loading weekly patterns data:', error);
    }
}

async function loadTopPerformers() {
    try {
        const response = await fetch('/api/analytics/top-performers');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.querySelector('#top-performers-table tbody');
            if (tbody) {
                tbody.innerHTML = data.performers.map((performer, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${performer.name}</td>
                        <td>${performer.course}</td>
                        <td>${performer.attendance_rate}%</td>
                        <td>${performer.trend}</td>
                    </tr>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error loading top performers data:', error);
    }
}

async function loadAttendanceIssues() {
    try {
        const response = await fetch('/api/analytics/issues');
        const data = await response.json();
        
        if (data.success) {
            const tbody = document.querySelector('#issues-table tbody');
            if (tbody) {
                if (data.issues.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="loading">No attendance issues found</td></tr>';
                } else {
                    tbody.innerHTML = data.issues.map(issue => `
                        <tr>
                            <td>${issue.student}</td>
                            <td>${issue.course}</td>
                            <td>${issue.type}</td>
                            <td>${issue.severity}</td>
                            <td>${issue.last_seen}</td>
                        </tr>
                    `).join('');
                }
            }
        }
    } catch (error) {
        console.error('Error loading attendance issues data:', error);
    }
}

// ===============================
// REPORTS FUNCTIONALITY
// ===============================

function initializeReports() {
    setupReportsEventListeners();
    setDefaultDateRange();
}

function setupReportsEventListeners() {
    const eventHandlers = {
        'export-pdf': exportPDF,
        'export-excel': exportExcel,
        'export-csv': exportCSV,
        'send-email-report': sendEmailReport,
        'setup-schedule': setupScheduledReports,
        'view-schedules': viewActiveSchedules,
        'export-custom': exportCustomData,
        'export-json': exportJSON,
        'backup-data': backupAllData,
        'clear-old-data': clearOldData,
        'verify-data': verifyDataIntegrity
    };

    addEventListeners(eventHandlers);
}

function initializeReportsTab() {
    console.log('Initializing reports tab...');
    // Additional reports-specific initialization if needed
}

function setDefaultDateRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - 30);
    
    const endInput = getElement('date-range-end');
    const startInput = getElement('date-range-start');
    
    if (endInput) endInput.value = endDate.toISOString().split('T')[0];
    if (startInput) startInput.value = startDate.toISOString().split('T')[0];
}

// Export Functions
async function exportPDF() {
    try {
        showNotification('Generating PDF report...', 'info');
        const reportType = getElementValue('report-type') || 'comprehensive';
        const response = await fetch(`/api/export/pdf?type=${reportType}`);
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `attendance_report_${new Date().toISOString().split('T')[0]}.pdf`);
            showNotification('PDF report downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate PDF report');
        }
    } catch (error) {
        console.error('Error exporting PDF:', error);
        showNotification('Failed to export PDF report', 'error');
    }
}

async function exportExcel() {
    try {
        showNotification('Generating Excel report...', 'info');
        const reportType = getElementValue('report-type') || 'comprehensive';
        const response = await fetch(`/api/export/excel?type=${reportType}`);
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `attendance_report_${new Date().toISOString().split('T')[0]}.xlsx`);
            showNotification('Excel report downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate Excel report');
        }
    } catch (error) {
        console.error('Error exporting Excel:', error);
        showNotification('Failed to export Excel report', 'error');
    }
}

async function exportCSV() {
    try {
        showNotification('Generating CSV export...', 'info');
        const reportType = getElementValue('report-type') || 'comprehensive';
        const response = await fetch(`/api/export/csv?type=${reportType}`);
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `attendance_data_${new Date().toISOString().split('T')[0]}.csv`);
            showNotification('CSV data downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate CSV export');
        }
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showNotification('Failed to export CSV data', 'error');
    }
}

async function sendEmailReport() {
    try {
        const email = getElementValue('recipient-email');
        const reportType = getElementValue('email-report-type') || 'pdf';
        
        if (!email || !isValidEmail(email)) {
            showNotification('Please enter a valid email address', 'error');
            return;
        }
        
        showNotification('Sending email report...', 'info');
        
        const response = await fetch('/api/reports/email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                report_type: reportType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Email report sent successfully!', 'success');
            setElementValue('recipient-email', '');
        } else {
            throw new Error(data.message || 'Failed to send email report');
        }
    } catch (error) {
        console.error('Error sending email report:', error);
        showNotification('Failed to send email report', 'error');
    }
}

async function setupScheduledReports() {
    try {
        const email = getElementValue('schedule-email');
        const frequency = getElementValue('schedule-frequency') || 'weekly';
        const time = getElementValue('schedule-time') || '09:00';
        const reportType = getElementValue('schedule-report-type') || 'pdf';
        
        if (!email || !isValidEmail(email)) {
            showNotification('Please enter a valid email address', 'error');
            return;
        }
        
        showNotification('Setting up scheduled reports...', 'info');
        
        const response = await fetch('/api/reports/schedule', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                frequency: frequency,
                time: time,
                report_type: reportType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Scheduled reports set up successfully!', 'success');
        } else {
            throw new Error(data.message || 'Failed to schedule reports');
        }
    } catch (error) {
        console.error('Error setting up scheduled reports:', error);
        showNotification('Failed to set up scheduled reports', 'error');
    }
}

async function viewActiveSchedules() {
    try {
        const response = await fetch('/api/reports/schedules');
        const data = await response.json();
        
        if (data.success) {
            // Display schedules in a modal or alert for now
            const schedules = data.schedules;
            if (schedules.length === 0) {
                alert('No active schedules found.');
            } else {
                const scheduleList = schedules.map(s => 
                    `${s.email} - ${s.frequency} at ${s.time} (${s.report_type})`
                ).join('\n');
                alert('Active Schedules:\n\n' + scheduleList);
            }
        }
    } catch (error) {
        console.error('Error loading schedules:', error);
        showNotification('Failed to load schedules', 'error');
    }
}

async function exportCustomData() {
    try {
        const startDate = getElementValue('date-range-start');
        const endDate = getElementValue('date-range-end');
        const format = getElementValue('export-format') || 'all';
        
        if (!startDate || !endDate) {
            showNotification('Please select date range', 'error');
            return;
        }
        
        showNotification('Generating custom export...', 'info');
        
        const params = new URLSearchParams({
            start_date: startDate,
            end_date: endDate,
            format: format
        });
        
        const response = await fetch(`/api/export/custom?${params}`);
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `custom_export_${startDate}_${endDate}.xlsx`);
            showNotification('Custom export downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate custom export');
        }
    } catch (error) {
        console.error('Error exporting custom data:', error);
        showNotification('Failed to export custom data', 'error');
    }
}

async function exportJSON() {
    try {
        showNotification('Generating JSON export...', 'info');
        const response = await fetch('/api/export/json');
        
        if (response.ok) {
            const blob = await response.blob();
            downloadBlob(blob, `attendance_data_${new Date().toISOString().split('T')[0]}.json`);
            showNotification('JSON export downloaded successfully!', 'success');
        } else {
            throw new Error('Failed to generate JSON export');
        }
    } catch (error) {
        console.error('Error exporting JSON:', error);
        showNotification('Failed to export JSON data', 'error');
    }
}

async function backupAllData() {
    try {
        showNotification('Creating backup...', 'info');
        const response = await fetch('/api/data/backup', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showNotification('Backup created successfully!', 'success');
        } else {
            throw new Error(data.message || 'Failed to create backup');
        }
    } catch (error) {
        console.error('Error creating backup:', error);
        showNotification('Failed to create backup', 'error');
    }
}

async function clearOldData() {
    try {
        const days = getElementValue('cleanup-days') || 90;
        
        if (!confirm(`Are you sure you want to clear data older than ${days} days? This action cannot be undone.`)) {
            return;
        }
        
        showNotification('Clearing old data...', 'info');
        
        const response = await fetch('/api/data/cleanup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ days: parseInt(days) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`Cleared ${data.records_deleted || 0} old records`, 'success');
        } else {
            throw new Error(data.message || 'Failed to clear old data');
        }
    } catch (error) {
        console.error('Error clearing old data:', error);
        showNotification('Failed to clear old data', 'error');
    }
}

async function verifyDataIntegrity() {
    try {
        showNotification('Verifying data integrity...', 'info');
        const response = await fetch('/api/data/verify');
        const data = await response.json();
        
        if (data.success) {
            const message = `Data integrity check complete:\n` +
                          `Total records: ${data.total_records}\n` +
                          `Issues found: ${data.issues_found}\n` +
                          `Status: ${data.status}`;
            alert(message);
            showNotification('Data integrity check completed', 'success');
        } else {
            throw new Error(data.message || 'Failed to verify data integrity');
        }
    } catch (error) {
        console.error('Error verifying data integrity:', error);
        showNotification('Failed to verify data integrity', 'error');
    }
}

// ===============================
// UTILITY FUNCTIONS
// ===============================

function loadInitialData() {
    // Load analytics data by default
    loadAnalyticsData();
}

function addEventListeners(eventHandlers) {
    Object.keys(eventHandlers).forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('click', eventHandlers[id]);
        }
    });
}

function getElement(id) {
    return document.getElementById(id);
}

function getElementValue(id) {
    const element = getElement(id);
    return element ? element.value : null;
}

function setElementValue(id, value) {
    const element = getElement(id);
    if (element) {
        element.value = value;
    }
}

function updateElement(id, value) {
    const element = getElement(id);
    if (element) {
        element.textContent = value;
    }
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function showNotification(message, type = 'info') {
    // Use existing notification system if available
    if (typeof window.showNotification === 'function') {
        window.showNotification(message, type);
    } else {
        // Fallback to alert
        alert(message);
    }
}
