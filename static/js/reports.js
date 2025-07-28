// Reports & Exports JavaScript Module

// Initialize reports page
document.addEventListener('DOMContentLoaded', function() {
  setupEventListeners();
  loadInitialData();
});

// Set up all event listeners
function setupEventListeners() {
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

  // Use common utility to set up event listeners
  addEventListeners(eventHandlers);
}

// Load initial data for the page
function loadInitialData() {
  // Set default date range (last 30 days)
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
    const reportType = getElement('report-type')?.value || 'basic';
    const response = await fetch(`/api/export/pdf?type=${reportType}`, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const blob = await response.blob();
      downloadFile(blob, `attendance_report_${reportType}_${getDateString()}.pdf`);
      showNotification('PDF report downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate PDF report');
    }
  } catch (error) {
    console.error('Error exporting PDF:', error);
    showNotification('Error generating PDF report', 'error');
  }
}

async function exportExcel() {
  try {
    showNotification('Generating Excel report...', 'info');
    const response = await fetch('/api/export/excel', {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.ok) {
      const blob = await response.blob();
      downloadFile(blob, `attendance_data_${getDateString()}.xlsx`);
      showNotification('Excel report downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate Excel report');
    }
  } catch (error) {
    console.error('Error exporting Excel:', error);
    showNotification('Error generating Excel report', 'error');
  }
}

async function exportCSV() {
  try {
    showNotification('Generating CSV export...', 'info');
    const dataType = 'all';
    
    if (dataType === 'all') {
      // For 'all' type, API returns JSON with file information
      const result = await fetchWithLoading('/api/export/csv?type=all');
      if (result.files) {
        showNotification(`CSV files generated: ${result.files.length} files`, 'success');
        console.log('Generated CSV files:', result.files);
      } else {
        showNotification('CSV export completed', 'success');
      }
    } else {
      // For specific types, API returns the file directly
      const response = await fetch(`/api/export/csv?type=${dataType}`, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        downloadFile(blob, `attendance_data_${dataType}_${getDateString()}.csv`);
        showNotification('CSV export downloaded successfully', 'success');
      } else {
        throw new Error('Failed to generate CSV export');
      }
    }
  } catch (error) {
    console.error('Error exporting CSV:', error);
    showNotification('Error generating CSV export', 'error');
  }
}

async function exportCustomData() {
  try {
    const startDate = getElement('date-range-start')?.value;
    const endDate = getElement('date-range-end')?.value;
    const format = getElement('export-format')?.value || 'csv';
    
    if (!startDate || !endDate) {
      showNotification('Please select both start and end dates', 'warning');
      return;
    }
    
    showNotification('Generating custom export...', 'info');
    
    const params = new URLSearchParams({
      type: format,
      start_date: startDate,
      end_date: endDate
    });
    
    const response = await fetchWithLoading(`/api/export/custom?${params}`);
    
    if (response.ok) {
      const blob = await response.blob();
      const filename = `custom_export_${format}_${startDate}_to_${endDate}.csv`;
      downloadFile(blob, filename);
      showNotification('Custom export downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate custom export');
    }
  } catch (error) {
    console.error('Error generating custom export:', error);
    showNotification('Error generating custom export', 'error');
  }
}

async function exportJSON() {
  try {
    showNotification('Generating JSON export...', 'info');
    const response = await fetchWithLoading('/api/export_data');
    
    if (response.ok) {
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      downloadFile(blob, `attendance_data_${getDateString()}.json`);
      showNotification('JSON export downloaded successfully', 'success');
    } else {
      throw new Error('Failed to generate JSON export');
    }
  } catch (error) {
    console.error('Error exporting JSON:', error);
    showNotification('Error generating JSON export', 'error');
  }
}

// Email Reports
async function sendEmailReport() {
  try {
    const recipientEmail = getElement('recipient-email')?.value;
    const reportType = getElement('email-report-type')?.value || 'basic';
    
    if (!recipientEmail) {
      showNotification('Please enter recipient email address', 'warning');
      return;
    }
    
    if (!isValidEmail(recipientEmail)) {
      showNotification('Please enter a valid email address', 'warning');
      return;
    }
    
    showNotification('Sending email report...', 'info');
    
    const result = await postJSON('/api/reports/email', {
      recipient_email: recipientEmail,
      report_type: reportType
    });
    
    // Check if the response has a message field (success) or error field (failure)
    if (result.message) {
      showNotification('Email report sent successfully', 'success');
      const emailInput = getElement('recipient-email');
      if (emailInput) emailInput.value = '';
    } else {
      throw new Error(result.error || 'Failed to send email report');
    }
  } catch (error) {
    console.error('Error sending email report:', error);
    showNotification('Error sending email report', 'error');
  }
}

// Scheduled Reports
async function setupScheduledReports() {
  try {
    const email = document.getElementById('schedule-email').value;
    const frequency = document.getElementById('schedule-frequency').value;
    const time = document.getElementById('schedule-time').value;
    const reportType = document.getElementById('schedule-report-type').value;
    
    if (!email) {
      showNotification('Please enter recipient email address', 'warning');
      return;
    }
    
    if (!isValidEmail(email)) {
      showNotification('Please enter a valid email address', 'warning');
      return;
    }
    
    if (!time) {
      showNotification('Please select a time for scheduled reports', 'warning');
      return;
    }
    
    showNotification('Setting up scheduled reports...', 'info');
    
    const response = await fetch('/api/reports/schedule', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        recipient_email: email,
        frequency: frequency,
        time: time,
        report_type: reportType
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(`Scheduled ${frequency} reports set up successfully`, 'success');
      // Clear form
      document.getElementById('schedule-email').value = '';
      document.getElementById('schedule-time').value = '09:00';
    } else {
      throw new Error(result.error || 'Failed to setup scheduled reports');
    }
  } catch (error) {
    console.error('Error setting up scheduled reports:', error);
    showNotification('Error setting up scheduled reports', 'error');
  }
}

async function viewActiveSchedules() {
  try {
    showNotification('Loading active schedules...', 'info');
    
    const response = await fetch('/api/reports/schedules');
    
    if (response.ok) {
      const schedules = await response.json();
      displayActiveSchedules(schedules);
    } else {
      showNotification('No active schedules found or error loading schedules', 'info');
    }
  } catch (error) {
    console.error('Error loading schedules:', error);
    showNotification('Error loading active schedules', 'error');
  }
}

function displayActiveSchedules(schedules) {
  if (!schedules || schedules.length === 0) {
    showNotification('No active schedules found', 'info');
    return;
  }
  
  let html = '<h4>📅 Active Scheduled Reports</h4>';
  html += '<ul>';
  
  schedules.forEach(schedule => {
    html += `<li>${schedule.frequency} reports to ${schedule.email} at ${schedule.time}</li>`;
  });
  
  html += '</ul>';
  
  // Create a modal or update the page content to show schedules
  showNotification(`Found ${schedules.length} active schedule(s)`, 'success');
  console.log('Active schedules:', schedules);
}

// Data Management Functions
async function backupAllData() {
  try {
    showNotification('Creating backup...', 'info');
    
    const response = await fetch('/api/backup/create', {
      method: 'POST'
    });
    
    if (response.ok) {
      const blob = await response.blob();
      downloadFile(blob, `attendance_backup_${getDateString()}.sql`);
      showNotification('Backup created and downloaded successfully', 'success');
    } else {
      throw new Error('Failed to create backup');
    }
  } catch (error) {
    console.error('Error creating backup:', error);
    showNotification('Error creating backup', 'error');
  }
}

async function clearOldData() {
  try {
    const days = document.getElementById('cleanup-days').value;
    
    if (!days || days < 1) {
      showNotification('Please enter a valid number of days', 'warning');
      return;
    }
    
    if (!confirm(`Are you sure you want to clear data older than ${days} days? This action cannot be undone.`)) {
      return;
    }
    
    showNotification('Clearing old data...', 'info');
    
    const response = await fetch('/api/cleanup/old_data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        days: parseInt(days)
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      showNotification(`Successfully cleared old data. Removed ${result.removed_count || 'some'} records.`, 'success');
    } else {
      throw new Error(result.error || 'Failed to clear old data');
    }
  } catch (error) {
    console.error('Error clearing old data:', error);
    showNotification('Error clearing old data', 'error');
  }
}

async function verifyDataIntegrity() {
  try {
    showNotification('Verifying data integrity...', 'info');
    
    const response = await fetch('/api/verify/data_integrity');
    
    if (response.ok) {
      const result = await response.json();
      
      if (result.issues && result.issues.length > 0) {
        showNotification(`Data verification complete. Found ${result.issues.length} issues.`, 'warning');
        console.log('Data integrity issues:', result.issues);
      } else {
        showNotification('Data integrity verification passed. No issues found.', 'success');
      }
    } else {
      throw new Error('Failed to verify data integrity');
    }
  } catch (error) {
    console.error('Error verifying data integrity:', error);
    showNotification('Error verifying data integrity', 'error');
  }
}

// Utility Functions
function downloadFile(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

// Remove duplicate utility functions - now using common.js versions
// isValidEmail, getDateString, showNotification, showLoading, and downloadFile are all in common.js
