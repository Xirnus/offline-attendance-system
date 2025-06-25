// Analytics Dashboard JavaScript

let trendsChart, lateChart, courseChart, weeklyChart;

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadAnalyticsData();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('refresh-trends').addEventListener('click', refreshTrends);
    document.getElementById('refresh-courses').addEventListener('click', refreshCourseData);
    document.getElementById('trend-period').addEventListener('change', refreshTrends);

    // New refresh buttons for each graph
    document.getElementById('refresh-trends-graph').addEventListener('click', refreshTrends);
    document.getElementById('refresh-late-graph').addEventListener('click', loadLateArrivalData);
    document.getElementById('refresh-course-graph').addEventListener('click', loadCourseComparison);
    document.getElementById('refresh-weekly-graph').addEventListener('click', loadWeeklyPatterns);
    document.getElementById('refresh-top-performers').addEventListener('click', loadTopPerformers);
    document.getElementById('refresh-issues').addEventListener('click', loadAttendanceIssues);

    // New refresh buttons for tables
    document.getElementById('refresh-top-performers-table').addEventListener('click', loadTopPerformers);
    document.getElementById('refresh-issues-table').addEventListener('click', loadAttendanceIssues);
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
        // Load overview stats
        await loadOverviewStats();
        
        // Load trend data
        await loadTrendData();
        
        // Load late arrival data
        await loadLateArrivalData();
        
        // Load course comparison
        await loadCourseComparison();
        
        // Load weekly patterns
        await loadWeeklyPatterns();
        
        // Load top performers
        await loadTopPerformers();
        
        // Load attendance issues
        await loadAttendanceIssues();
        
    } catch (error) {
        console.error('Error loading analytics data:', error);
    }
}

async function loadOverviewStats() {
    try {
        const response = await fetch('/api/analytics/overview');
        const data = await response.json();
        
        document.getElementById('total-students').textContent = data.total_students || 0;
        document.getElementById('avg-attendance').textContent = (data.avg_attendance || 0).toFixed(1) + '%';
        document.getElementById('active-courses').textContent = data.active_courses || 0;
        
        // Calculate trend
        const trend = data.weekly_trend || 0;
        const trendElement = document.getElementById('weekly-trend');
        if (trend > 0) {
            trendElement.innerHTML = `<span class="trend-up">↗ +${trend.toFixed(1)}%</span>`;
        } else if (trend < 0) {
            trendElement.innerHTML = `<span class="trend-down">↘ ${trend.toFixed(1)}%</span>`;
        } else {
            trendElement.innerHTML = `<span class="trend-neutral">→ ${trend.toFixed(1)}%</span>`;
        }
        
    } catch (error) {
        console.error('Error loading overview stats:', error);
        // Set default values
        document.getElementById('total-students').textContent = '0';
        document.getElementById('avg-attendance').textContent = '0%';
        document.getElementById('active-courses').textContent = '0';
        document.getElementById('weekly-trend').textContent = '0%';
    }
}

async function loadTrendData() {
    try {
        const period = document.getElementById('trend-period').value;
        const response = await fetch(`/api/analytics/trends?period=${period}`);
        const data = await response.json();
        
        trendsChart.data.labels = data.labels || [];
        trendsChart.data.datasets[0].data = data.values || [];
        trendsChart.update();
        
    } catch (error) {
        console.error('Error loading trend data:', error);
        // Show sample data
        trendsChart.data.labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4'];
        trendsChart.data.datasets[0].data = [75, 80, 78, 85];
        trendsChart.update();
    }
}

async function loadLateArrivalData() {
    try {
        const response = await fetch('/api/analytics/late-arrivals');
        const data = await response.json();
        
        document.getElementById('late-today').textContent = data.late_today || 0;
        document.getElementById('avg-late-time').textContent = (data.avg_late_time || 0) + ' min';
        document.getElementById('chronic-late').textContent = data.chronic_late || 0;
        
        // Update late chart
        lateChart.data.datasets[0].data = data.late_distribution || [0, 0, 0, 0];
        lateChart.update();
        
    } catch (error) {
        console.error('Error loading late arrival data:', error);
        // Set default values
        document.getElementById('late-today').textContent = '0';
        document.getElementById('avg-late-time').textContent = '0 min';
        document.getElementById('chronic-late').textContent = '0';
        
        // Sample data
        lateChart.data.datasets[0].data = [25, 15, 8, 3];
        lateChart.update();
    }
}

async function loadCourseComparison() {
    try {
        const response = await fetch('/api/analytics/courses');
        const data = await response.json();
        
        courseChart.data.labels = data.labels || [];
        courseChart.data.datasets[0].data = data.values || [];
        courseChart.update();
        
        // Update course details table
        updateCourseDetailsTable(data.details || []);
        
    } catch (error) {
        console.error('Error loading course comparison:', error);
        // Sample data
        courseChart.data.labels = ['Computer Science', 'Mathematics', 'Physics', 'Chemistry'];
        courseChart.data.datasets[0].data = [45, 30, 25, 20];
        courseChart.update();
        
        // Sample course details
        updateCourseDetailsTable([
            { name: 'Computer Science', students: 45, avg_attendance: 85.2 },
            { name: 'Mathematics', students: 30, avg_attendance: 78.5 },
            { name: 'Physics', students: 25, avg_attendance: 82.1 },
            { name: 'Chemistry', students: 20, avg_attendance: 79.8 }
        ]);
    }
}

async function loadWeeklyPatterns() {
    try {
        const response = await fetch('/api/analytics/weekly-patterns');
        const data = await response.json();
        
        weeklyChart.data.datasets[0].data = data.values || [0, 0, 0, 0, 0, 0, 0];
        weeklyChart.update();
        
    } catch (error) {
        console.error('Error loading weekly patterns:', error);
        // Sample data
        weeklyChart.data.datasets[0].data = [85, 88, 82, 90, 78, 45, 30];
        weeklyChart.update();
    }
}

async function loadTopPerformers() {
    try {
        const response = await fetch('/api/analytics/top-performers');
        const data = await response.json();
        
        updateTopPerformersTable(data.performers || []);
        
    } catch (error) {
        console.error('Error loading top performers:', error);
        // Sample data
        updateTopPerformersTable([
            { rank: 1, name: 'John Doe', course: 'Computer Science', attendance_rate: 98.5, trend: 'up' },
            { rank: 2, name: 'Jane Smith', course: 'Mathematics', attendance_rate: 96.2, trend: 'up' },
            { rank: 3, name: 'Bob Johnson', course: 'Physics', attendance_rate: 94.8, trend: 'neutral' }
        ]);
    }
}

async function loadAttendanceIssues() {
    try {
        const response = await fetch('/api/analytics/issues');
        const data = await response.json();
        
        updateIssuesTable(data.issues || []);
        
    } catch (error) {
        console.error('Error loading attendance issues:', error);
        // Sample data
        updateIssuesTable([
            { student: 'Mike Wilson', course: 'Chemistry', issue: 'Low Attendance', severity: 'High', last_seen: '3 days ago' },
            { student: 'Sarah Davis', course: 'Physics', issue: 'Frequent Late', severity: 'Medium', last_seen: '1 day ago' }
        ]);
    }
}

function updateCourseDetailsTable(courses) {
    const container = document.getElementById('course-details');
    
    if (courses.length === 0) {
        container.innerHTML = '<p>No course data available</p>';
        return;
    }
    
    let html = `
        <table>
            <thead>
                <tr>
                    <th>Course</th>
                    <th>Students</th>
                    <th>Avg Attendance</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    courses.forEach(course => {
        const status = course.avg_attendance >= 80 ? 'Good' : course.avg_attendance >= 60 ? 'Fair' : 'Poor';
        const statusClass = course.avg_attendance >= 80 ? 'trend-up' : course.avg_attendance >= 60 ? 'trend-neutral' : 'trend-down';
        
        html += `
            <tr>
                <td>${course.name}</td>
                <td>${course.students}</td>
                <td>${course.avg_attendance.toFixed(1)}%</td>
                <td><span class="${statusClass}">${status}</span></td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function updateTopPerformersTable(performers) {
    const tbody = document.querySelector('#top-performers-table tbody');
    
    if (performers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
        return;
    }
    
    let html = '';
    performers.forEach(performer => {
        const trendIcon = performer.trend === 'up' ? '↗' : performer.trend === 'down' ? '↘' : '→';
        const trendClass = performer.trend === 'up' ? 'trend-up' : performer.trend === 'down' ? 'trend-down' : 'trend-neutral';
        
        html += `
            <tr>
                <td>${performer.rank}</td>
                <td>${performer.name}</td>
                <td>${performer.course}</td>
                <td>${performer.attendance_rate.toFixed(1)}%</td>
                <td><span class="${trendClass}">${trendIcon}</span></td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function updateIssuesTable(issues) {
    const tbody = document.querySelector('#issues-table tbody');
    
    if (issues.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No attendance issues detected</td></tr>';
        return;
    }
    
    let html = '';
    issues.forEach(issue => {
        const severityClass = issue.severity === 'High' ? 'trend-down' : issue.severity === 'Medium' ? 'trend-neutral' : 'trend-up';
        
        html += `
            <tr>
                <td>${issue.student}</td>
                <td>${issue.course}</td>
                <td>${issue.issue}</td>
                <td><span class="${severityClass}">${issue.severity}</span></td>
                <td>${issue.last_seen}</td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

function refreshTrends() {
    loadTrendData();
}

function refreshCourseData() {
    loadCourseComparison();
}

// Utility functions
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 3000);
}

// Auto-refresh data every 5 minutes
setInterval(loadAnalyticsData, 5 * 60 * 1000);
