// Analytics Dashboard JavaScript

let trendsChart, lateChart, courseChart, weeklyChart;

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadAnalyticsData();
    setupEventListeners();
});

function setupEventListeners() {
    // Remove redundant event listeners and use a more efficient approach
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

    // Add event listeners efficiently
    Object.entries(eventHandlers).forEach(([id, handler]) => {
        const element = document.getElementById(id);
        if (element) {
            const eventType = element.tagName === 'SELECT' ? 'change' : 'click';
            element.addEventListener(eventType, handler);
        }
    });
}

function initializeCharts() {
    // Attendance Trends Chart
    const trendsCtx = document.getElementById('trendsChart').getContext('2d');
    trendsChart = new Chart(trendsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Attendance Rate',
                data: [],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
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
            },
            plugins: {
                legend: {
                    display: true
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + '%';
                        }
                    }
                }
            }
        }
    });

    // Late Arrival Chart
    const lateCtx = document.getElementById('lateChart').getContext('2d');
    lateChart = new Chart(lateCtx, {
        type: 'bar',
        data: {
            labels: ['0-5 min', '5-15 min', '15-30 min', '30+ min'],
            datasets: [{
                label: 'Number of Students',
                data: [0, 0, 0, 0],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(255, 152, 0, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Course Comparison Chart
    const courseCtx = document.getElementById('courseChart').getContext('2d');
    courseChart = new Chart(courseCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF',
                    '#FF9F40'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + ' students';
                        }
                    }
                }
            }
        }
    });

    // Weekly Patterns Chart
    const weeklyCtx = document.getElementById('weeklyChart').getContext('2d');
    weeklyChart = new Chart(weeklyCtx, {
        type: 'radar',
        data: {
            labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
            datasets: [{
                label: 'Average Attendance Rate',
                data: [0, 0, 0, 0, 0, 0, 0],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.2)',
                pointBackgroundColor: '#007bff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
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

async function loadAnalyticsData() {
    try {
        // Load all analytics data in parallel for better performance
        await Promise.all([
            loadOverviewStats(),
            loadTrendData(),
            loadLateArrivalData(),
            loadCourseComparison(),
            loadWeeklyPatterns(),
            loadTopPerformers(),
            loadAttendanceIssues()
        ]);
    } catch (error) {
        console.error('Error loading analytics data:', error);
        showError('Failed to load analytics data. Please refresh the page.');
    }
}

async function loadOverviewStats() {
    try {
        const response = await fetch('/api/analytics/overview');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Update overview statistics with error checking
        updateElementContent('total-students', data.total_students || 0);
        updateElementContent('avg-attendance', (data.avg_attendance || 0).toFixed(1) + '%');
        updateElementContent('active-courses', data.active_courses || 0);
        updateElementContent('weekly-trend', (data.weekly_trend || 0).toFixed(1) + '%');
        
    } catch (error) {
        console.error('Error loading overview stats:', error);
        showError('Failed to load overview statistics');
    }
}

async function loadTrendData() {
    try {
        const period = document.getElementById('trend-period').value;
        const response = await fetch(`/api/analytics/trends?period=${period}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Update trends chart
        trendsChart.data.labels = data.labels || [];
        trendsChart.data.datasets[0].data = data.values || [];
        trendsChart.update();
        
    } catch (error) {
        console.error('Error loading trend data:', error);
        showError('Failed to load trend data');
    }
}

async function refreshTrends() {
    await loadTrendData();
}

async function loadLateArrivalData() {
    try {
        const response = await fetch('/api/analytics/late-arrivals');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Update late arrival stats
        updateElementContent('late-today', data.late_today || 0);
        updateElementContent('avg-late-time', (data.avg_late_time || 0) + ' min');
        
        // Update late arrival chart
        lateChart.data.datasets[0].data = data.late_distribution || [0, 0, 0, 0];
        lateChart.update();
        
    } catch (error) {
        console.error('Error loading late arrival data:', error);
        showError('Failed to load late arrival data');
    }
}

async function loadCourseComparison() {
    try {
        const response = await fetch('/api/analytics/courses');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Update course chart
        courseChart.data.labels = data.labels || [];
        courseChart.data.datasets[0].data = data.values || [];
        courseChart.update();
        
        // Update course details table
        updateCourseDetails(data.details || []);
        
    } catch (error) {
        console.error('Error loading course comparison:', error);
        showError('Failed to load course comparison');
    }
}

function updateCourseDetails(details) {
    const container = document.getElementById('course-details');
    if (!container) return;
    
    if (details.length === 0) {
        container.innerHTML = '<p class="loading">No course data available</p>';
        return;
    }
    
    let html = '<table><thead><tr><th>Course</th><th>Students</th><th>Avg Attendance</th></tr></thead><tbody>';
    details.forEach(course => {
        html += `<tr>
            <td>${course.name}</td>
            <td>${course.students}</td>
            <td>${course.avg_attendance.toFixed(1)}%</td>
        </tr>`;
    });
    html += '</tbody></table>';
    container.innerHTML = html;
}

async function loadWeeklyPatterns() {
    try {
        const response = await fetch('/api/analytics/weekly-patterns');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        // Update weekly patterns chart
        weeklyChart.data.datasets[0].data = data.values || [0, 0, 0, 0, 0, 0, 0];
        weeklyChart.update();
        
    } catch (error) {
        console.error('Error loading weekly patterns:', error);
        showError('Failed to load weekly patterns');
    }
}

async function loadTopPerformers() {
    try {
        const response = await fetch('/api/analytics/top-performers');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        updateTopPerformersTable(data.performers || []);
        
    } catch (error) {
        console.error('Error loading top performers:', error);
        showError('Failed to load top performers');
    }
}

function updateTopPerformersTable(performers) {
    const tbody = document.querySelector('#top-performers-table tbody');
    if (!tbody) return;
    
    if (performers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No performance data available</td></tr>';
        return;
    }
    
    let html = '';
    performers.forEach(performer => {
        const trendIcon = performer.trend === 'up' ? '📈' : performer.trend === 'down' ? '📉' : '➡️';
        const trendClass = `trend-${performer.trend}`;
        
        html += `<tr>
            <td>${performer.rank}</td>
            <td>${performer.name}</td>
            <td>${performer.course}</td>
            <td>${performer.attendance_rate}%</td>
            <td class="${trendClass}">${trendIcon} ${performer.trend}</td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

async function loadAttendanceIssues() {
    try {
        const response = await fetch('/api/analytics/issues');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        updateIssuesTable(data.issues || []);
        
    } catch (error) {
        console.error('Error loading attendance issues:', error);
        showError('Failed to load attendance issues');
    }
}

function updateIssuesTable(issues) {
    const tbody = document.querySelector('#issues-table tbody');
    if (!tbody) return;
    
    if (issues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No issues found</td></tr>';
        return;
    }
    
    let html = '';
    issues.forEach(issue => {
        const severityClass = issue.severity.toLowerCase();
        html += `<tr>
            <td>${issue.student}</td>
            <td>${issue.course}</td>
            <td>${issue.issue}</td>
            <td><span class="severity-${severityClass}">${issue.severity}</span></td>
            <td>${issue.last_seen}</td>
        </tr>`;
    });
    tbody.innerHTML = html;
}

// Utility functions
function updateElementContent(id, content) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = content;
    }
}

function showError(message) {
    console.error(message);
    // You could implement a toast notification system here
    // For now, we'll just log the error
}

// Remove the unused refreshCourseData function since we use loadCourseComparison
