/**
 * Common JavaScript Utilities
 * Shared functions and utilities used across multiple files in the attendance system
 */

// =============================================================================
// NOTIFICATION SYSTEM
// =============================================================================

/**
 * Display notification messages to the user
 * @param {string} message - The message to display
 * @param {string} type - The type of notification ('success', 'error', 'info', 'warning')
 * @param {number} duration - Duration in milliseconds (default: 3000)
 */

// Notification throttling to prevent spam
const notificationHistory = new Map();
const NOTIFICATION_THROTTLE_TIME = 3000; // 3 seconds

function showNotification(message, type = 'info', duration = 3000) {
  // Create a key for this specific message + type combination
  const notificationKey = `${message}_${type}`;
  const now = Date.now();
  
  // Check if this exact notification was shown recently
  if (notificationHistory.has(notificationKey)) {
    const lastShown = notificationHistory.get(notificationKey);
    if (now - lastShown < NOTIFICATION_THROTTLE_TIME) {
      // Skip showing the notification if it was shown too recently
      return;
    }
  }
  
  // Update the notification history
  notificationHistory.set(notificationKey, now);
  
  const notification = document.createElement('div');
  
  // Handle multiline messages
  if (message.includes('\n')) {
    notification.innerHTML = message.replace(/\n/g, '<br>');
  } else {
    notification.textContent = message;
  }
  
  const colors = {
    success: '#28a745',
    error: '#dc3545',
    info: '#17a2b8',
    warning: '#ffc107',
    default: '#6c757d'
  };
  
  notification.style.cssText = `
    position: fixed; top: 20px; right: 20px; padding: 15px 20px;
    border-radius: 8px; color: white; z-index: 1000; font-weight: bold;
    background-color: ${colors[type] || colors.default};
    max-width: 400px; line-height: 1.4; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    border: 2px solid ${colors[type] || colors.default};
    animation: slideIn 0.3s ease-in-out;
  `;
  
  // Add slide-in animation
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `;
  if (!document.querySelector('style[data-notification-styles]')) {
    style.setAttribute('data-notification-styles', 'true');
    document.head.appendChild(style);
  }
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    if (document.body.contains(notification)) {
      notification.style.animation = 'slideOut 0.3s ease-in-out';
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 300);
    }
  }, duration);
}

/**
 * Alternative name for showNotification to maintain compatibility
 */
function showAlert(message, type = 'info', duration = 3000) {
  showNotification(message, type, duration);
}

// =============================================================================
// ALTERNATIVE NOTIFICATION SYSTEM (for compatibility)
// =============================================================================

/**
 * Alternative notification system (used in some files)
 * Compatible with existing showMessage implementations
 * @param {string} message - The message to display
 * @param {string} type - The type of message ('success', 'error', 'info', 'warning', 'danger')
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showMessage(message, type = 'info', duration = 5000) {
  // Remove existing messages first
  const existingMessages = document.querySelectorAll('.error-message, .success-message, .info-message, .warning-message, .danger-message');
  existingMessages.forEach(msg => msg.remove());
  
  // Map types to CSS classes and colors
  const typeMapping = {
    'success': { class: 'success-message', color: '#28a745' },
    'error': { class: 'error-message', color: '#dc3545' },
    'danger': { class: 'error-message', color: '#dc3545' },
    'info': { class: 'info-message', color: '#17a2b8' },
    'warning': { class: 'warning-message', color: '#ffc107' }
  };
  
  const config = typeMapping[type] || typeMapping.info;
  
  // Create new message element
  const messageDiv = document.createElement('div');
  messageDiv.className = config.class;
  messageDiv.textContent = message;
  
  // Style the message
  messageDiv.style.cssText = `
    position: fixed; top: 20px; right: 20px; padding: 15px 20px;
    border-radius: 8px; color: white; z-index: 1000; font-weight: bold;
    background-color: ${config.color}; max-width: 400px; line-height: 1.4;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 2px solid ${config.color};
    animation: slideIn 0.3s ease-in-out;
  `;
  
  // Try to insert at the top of content, fallback to body
  const content = document.querySelector('.content') || document.body;
  if (content === document.body) {
    content.appendChild(messageDiv);
  } else {
    content.insertBefore(messageDiv, content.firstChild);
  }
  
  // Auto-remove after specified duration
  setTimeout(() => {
    if (messageDiv.parentNode) {
      messageDiv.style.animation = 'slideOut 0.3s ease-in-out';
      setTimeout(() => {
        if (messageDiv.parentNode) {
          messageDiv.remove();
        }
      }, 300);
    }
  }, duration);
}

// =============================================================================
// MODAL UTILITIES
// =============================================================================

/**
 * Custom alert modal
 * @param {string} message - The message to display
 * @param {string} title - The title of the modal
 * @returns {Promise} - Resolves when user clicks OK
 */
function customAlert(message, title = 'Alert') {
  return new Promise((resolve) => {
    const modal = document.getElementById('customModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalConfirm = document.getElementById('modalConfirm');
    const modalCancel = document.getElementById('modalCancel');
    
    if (!modal) {
      console.warn('Custom modal not found, falling back to native alert');
      alert(message);
      resolve();
      return;
    }
    
    modalTitle.textContent = title;
    if (message.includes('\n')) {
      modalMessage.innerHTML = message.replace(/\n/g, '<br>');
    } else {
      modalMessage.textContent = message;
    }
    modalCancel.style.display = 'none';
    modalConfirm.textContent = 'OK';
    
    modal.classList.add('show');
    
    const handleConfirm = () => {
      modal.classList.remove('show');
      modalConfirm.removeEventListener('click', handleConfirm);
      modalCancel.style.display = 'inline-block';
      resolve();
    };
    
    modalConfirm.addEventListener('click', handleConfirm);
  });
}

/**
 * Custom confirm modal
 * @param {string} message - The message to display
 * @param {string} title - The title of the modal
 * @returns {Promise<boolean>} - Resolves with true if confirmed, false if cancelled
 */
function customConfirm(message, title = 'Confirmation') {
  return new Promise((resolve) => {
    const modal = document.getElementById('customModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalConfirm = document.getElementById('modalConfirm');
    const modalCancel = document.getElementById('modalCancel');
    
    if (!modal) {
      console.warn('Custom modal not found, falling back to native confirm');
      resolve(confirm(message));
      return;
    }
    
    modalTitle.textContent = title;
    if (message.includes('\n')) {
      modalMessage.innerHTML = message.replace(/\n/g, '<br>');
    } else {
      modalMessage.textContent = message;
    }
    modalCancel.style.display = 'inline-block';
    modalConfirm.textContent = 'Confirm';
    
    modal.classList.add('show');
    
    const handleConfirm = () => {
      modal.classList.remove('show');
      modalConfirm.removeEventListener('click', handleConfirm);
      modalCancel.removeEventListener('click', handleCancel);
      resolve(true);
    };
    
    const handleCancel = () => {
      modal.classList.remove('show');
      modalConfirm.removeEventListener('click', handleConfirm);
      modalCancel.removeEventListener('click', handleCancel);
      resolve(false);
    };
    
    modalConfirm.addEventListener('click', handleConfirm);
    modalCancel.addEventListener('click', handleCancel);
  });
}

/**
 * Generic custom modal
 * @param {string} message - The message to display
 * @param {string} title - The title of the modal
 * @param {boolean} showCancel - Whether to show cancel button
 * @returns {Promise<boolean>} - Resolves with true if confirmed, false if cancelled
 */
function showCustomModal(message, title = 'Notification', showCancel = false) {
  return new Promise((resolve) => {
    const modal = document.getElementById('customModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalConfirm = document.getElementById('modalConfirm');
    const modalCancel = document.getElementById('modalCancel');
    
    if (!modal) {
      console.warn('Custom modal not found, falling back to native confirm/alert');
      if (showCancel) {
        resolve(confirm(message));
      } else {
        alert(message);
        resolve(true);
      }
      return;
    }
    
    modalTitle.textContent = title;
    if (message.includes('\n')) {
      modalMessage.innerHTML = message.replace(/\n/g, '<br>');
    } else {
      modalMessage.textContent = message;
    }
    
    if (showCancel) {
      modalCancel.style.display = 'inline-block';
      modalConfirm.textContent = 'Confirm';
    } else {
      modalCancel.style.display = 'none';
      modalConfirm.textContent = 'OK';
    }
    
    modal.classList.add('show');
    
    const handleConfirm = () => {
      modal.classList.remove('show');
      modalConfirm.removeEventListener('click', handleConfirm);
      modalCancel.removeEventListener('click', handleCancel);
      resolve(true);
    };
    
    const handleCancel = () => {
      modal.classList.remove('show');
      modalConfirm.removeEventListener('click', handleConfirm);
      modalCancel.removeEventListener('click', handleCancel);
      resolve(false);
    };
    
    modalConfirm.addEventListener('click', handleConfirm);
    if (showCancel) {
      modalCancel.addEventListener('click', handleCancel);
    }
  });
}

// =============================================================================
// MODAL CONTROL UTILITIES
// =============================================================================

/**
 * Setup modal controls for all modals on the page
 * Handles close buttons and click-outside-to-close functionality
 */
function setupModalControls() {
  const modals = document.querySelectorAll('.modal');
  const closeButtons = document.querySelectorAll('.close, .modal-close');
  
  // Close modal when clicking X or close button
  closeButtons.forEach(button => {
    button.addEventListener('click', function() {
      const modal = this.closest('.modal');
      if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
      }
    });
  });
  
  // Close modal when clicking outside
  window.addEventListener('click', function(event) {
    modals.forEach(modal => {
      if (event.target === modal) {
        modal.style.display = 'none';
        modal.classList.remove('show');
      }
    });
  });
  
  // Handle ESC key to close modals
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      modals.forEach(modal => {
        if (modal.style.display === 'block' || modal.classList.contains('show')) {
          modal.style.display = 'none';
          modal.classList.remove('show');
        }
      });
    }
  });
}

/**
 * Show a modal by ID
 * @param {string} modalId - The ID of the modal to show
 */
function showModal(modalId) {
  const modal = getElement(modalId);
  if (modal) {
    modal.style.display = 'block';
    modal.classList.add('show');
  }
}

/**
 * Hide a modal by ID
 * @param {string} modalId - The ID of the modal to hide
 */
function hideModal(modalId) {
  const modal = getElement(modalId);
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('show');
  }
}

// =============================================================================
// DOM UTILITIES
// =============================================================================

/**
 * Safely get element by ID with error handling
 * @param {string} id - The element ID
 * @returns {HTMLElement|null} - The element or null if not found
 */
function getElement(id) {
  const element = document.getElementById(id);
  if (!element) {
    console.warn(`Element with ID '${id}' not found`);
  }
  return element;
}

/**
 * Add event listener with error handling
 * @param {string|HTMLElement} elementOrId - Element or element ID
 * @param {string} event - Event type
 * @param {Function} handler - Event handler
 * @param {object} options - Event listener options
 */
function addEventListenerSafe(elementOrId, event, handler, options = {}) {
  const element = typeof elementOrId === 'string' ? getElement(elementOrId) : elementOrId;
  if (element) {
    element.addEventListener(event, handler, options);
  }
}

/**
 * Bulk add event listeners
 * @param {object} handlers - Object with element IDs as keys and handler functions as values
 * @param {string} eventType - Event type (default: 'click')
 */
function addEventListeners(handlers, eventType = 'click') {
  Object.entries(handlers).forEach(([id, handler]) => {
    addEventListenerSafe(id, eventType, handler);
  });
}

/**
 * Toggle element visibility
 * @param {string|HTMLElement} elementOrId - Element or element ID
 * @param {boolean} show - Whether to show the element
 */
function toggleElement(elementOrId, show) {
  const element = typeof elementOrId === 'string' ? getElement(elementOrId) : elementOrId;
  if (element) {
    element.style.display = show ? 'block' : 'none';
  }
}

/**
 * Set loading state for buttons
 * @param {string|HTMLElement} buttonOrId - Button element or ID
 * @param {boolean} loading - Whether button is in loading state
 * @param {string} loadingText - Text to show when loading
 */
function setButtonLoading(buttonOrId, loading, loadingText = 'Loading...') {
  const button = typeof buttonOrId === 'string' ? getElement(buttonOrId) : buttonOrId;
  if (!button) return;
  
  if (loading) {
    button.dataset.originalText = button.textContent;
    button.textContent = loadingText;
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

// =============================================================================
// FETCH UTILITIES
// =============================================================================

/**
 * Enhanced fetch with error handling and loading states
 * @param {string} url - The URL to fetch
 * @param {object} options - Fetch options
 * @param {string|HTMLElement} loadingButton - Button to set loading state
 * @returns {Promise} - Enhanced fetch promise
 */
async function fetchWithLoading(url, options = {}, loadingButton = null) {
  if (loadingButton) {
    setButtonLoading(loadingButton, true);
  }
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Server error (${response.status}): ${errorText}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    } else {
      return response;
    }
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  } finally {
    if (loadingButton) {
      setButtonLoading(loadingButton, false);
    }
  }
}

/**
 * POST request with JSON data
 * @param {string} url - The URL to post to
 * @param {object} data - Data to send
 * @param {string|HTMLElement} loadingButton - Button to set loading state
 * @returns {Promise} - Fetch promise
 */
async function postJSON(url, data, loadingButton = null) {
  return fetchWithLoading(url, {
    method: 'POST',
    body: JSON.stringify(data)
  }, loadingButton);
}

/**
 * GET request with automatic retry
 * @param {string} url - The URL to get
 * @param {number} retries - Number of retries (default: 3)
 * @returns {Promise} - Fetch promise
 */
async function getWithRetry(url, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      return await fetchWithLoading(url);
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
}

// =============================================================================
// DATE AND TIME UTILITIES
// =============================================================================

/**
 * Format a timestamp to locale string
 * @param {number} timestamp - Unix timestamp
 * @returns {string} - Formatted date/time string
 */
function formatTimestamp(timestamp) {
  try {
    return new Date(timestamp * 1000).toLocaleString();
  } catch (error) {
    return 'Invalid date';
  }
}

/**
 * Format a date/time string to locale string
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted date/time string
 */
function formatDateTime(dateString) {
  try {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  } catch (error) {
    return dateString || 'Invalid date';
  }
}

/**
 * Format date for display
 * @param {Date|string} date - Date object or string
 * @returns {string} - Formatted display time
 */
function formatDisplayTime(date) {
  try {
    if (!date) return 'N/A';
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return dateObj.toLocaleString();
  } catch (error) {
    return date?.toString() || 'Invalid date';
  }
}

/**
 * Calculate duration between two timestamps
 * @param {string} startTime - Start time ISO string
 * @param {string} endTime - End time ISO string
 * @returns {string} - Duration in hours and minutes
 */
function calculateDuration(startTime, endTime) {
  try {
    const start = new Date(startTime);
    const end = new Date(endTime);
    const diffMs = end - start;
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  } catch (error) {
    return 'N/A';
  }
}

/**
 * Get current date string for file naming
 * @returns {string} - Date string in YYYYMMDD format
 */
function getDateString() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
}

/**
 * Get default end time (current time + 2 hours)
 * @returns {string} - Time string in HH:MM format
 */
function getDefaultEndTime() {
  const now = new Date();
  now.setHours(now.getHours() + 2);
  return now.toTimeString().slice(0, 5);
}

// =============================================================================
// FILE DOWNLOAD UTILITIES
// =============================================================================

/**
 * Download a blob as a file
 * @param {Blob} blob - The blob to download
 * @param {string} filename - The filename for the download
 */
function downloadFile(blob, filename) {
  try {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error downloading file:', error);
    showNotification('Error downloading file', 'error');
  }
}

/**
 * Convert data to CSV and download
 * @param {Array} data - Array of objects to convert to CSV
 * @param {string} filename - The filename for the download
 */
function downloadCSV(data, filename) {
  try {
    if (!data.length) {
      showNotification('No data to export', 'warning');
      return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(header => `"${(row[header] || '').toString().replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    downloadFile(blob, filename.endsWith('.csv') ? filename : filename + '.csv');
  } catch (error) {
    console.error('Error creating CSV:', error);
    showNotification('Error creating CSV file', 'error');
  }
}

// =============================================================================
// LOADING STATE UTILITIES
// =============================================================================

/**
 * Show or hide loading indicator
 * @param {string} elementId - ID of the loading element
 * @param {boolean} show - Whether to show or hide the loading indicator
 */
function showLoading(elementId, show) {
  const element = getElement(elementId);
  if (element) {
    element.style.display = show ? 'block' : 'none';
  }
}

/**
 * Create a loading spinner element
 * @returns {HTMLElement} - Loading spinner element
 */
function createLoadingSpinner() {
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';
  spinner.style.cssText = `
    display: inline-block; width: 20px; height: 20px;
    border: 3px solid #f3f3f3; border-top: 3px solid #3498db;
    border-radius: 50%; animation: spin 1s linear infinite;
  `;
  
  // Add spin animation if not already present
  if (!document.querySelector('style[data-spinner-styles]')) {
    const style = document.createElement('style');
    style.setAttribute('data-spinner-styles', 'true');
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
  }
  
  return spinner;
}

// =============================================================================
// FORM VALIDATION UTILITIES
// =============================================================================

/**
 * Validate form fields
 * @param {HTMLFormElement|string} formOrId - Form element or form ID
 * @param {Array} requiredFields - Array of required field names
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(formOrId, requiredFields = []) {
  const form = typeof formOrId === 'string' ? getElement(formOrId) : formOrId;
  if (!form) return false;
  
  let isValid = true;
  const errors = [];
  
  requiredFields.forEach(fieldName => {
    const field = form.querySelector(`[name="${fieldName}"]`);
    if (!field || !field.value.trim()) {
      isValid = false;
      errors.push(`${fieldName} is required`);
      if (field) {
        field.style.borderColor = '#dc3545';
      }
    } else if (field) {
      field.style.borderColor = '';
    }
  });
  
  if (!isValid) {
    showNotification(errors.join(', '), 'error');
  }
  
  return isValid;
}

/**
 * Clear form validation errors
 * @param {HTMLFormElement|string} formOrId - Form element or form ID
 */
function clearFormErrors(formOrId) {
  const form = typeof formOrId === 'string' ? getElement(formOrId) : formOrId;
  if (!form) return;
  
  const fields = form.querySelectorAll('input, select, textarea');
  fields.forEach(field => {
    field.style.borderColor = '';
  });
}

// =============================================================================
// EVENT LISTENER SETUP UTILITIES
// =============================================================================

/**
 * Setup event listeners with mapping object (more efficient than individual calls)
 * @param {object} eventHandlers - Object mapping element IDs to handler functions
 * @param {string} defaultEventType - Default event type (default: 'click')
 */
function setupEventListeners(eventHandlers, defaultEventType = 'click') {
  Object.entries(eventHandlers).forEach(([id, handler]) => {
    const element = getElement(id);
    if (element) {
      const eventType = element.tagName === 'SELECT' ? 'change' : 
                       element.tagName === 'INPUT' ? 'input' : 
                       defaultEventType;
      element.addEventListener(eventType, handler);
    }
  });
}

// =============================================================================
// DEVICE FINGERPRINTING UTILITIES
// =============================================================================

/**
 * Generate canvas fingerprint for device identification
 * @returns {string} - Canvas fingerprint hash
 */
function getCanvasFingerprint() {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 200;
    canvas.height = 50;
    
    // Draw text with different styles
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Canvas fingerprint 🔒', 2, 2);
    
    ctx.font = '18px serif';
    ctx.fillStyle = 'rgba(255, 0, 102, 0.8)';
    ctx.fillText('Device ID', 4, 20);
    
    // Add some geometric shapes
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = 'rgb(255,0,255)';
    ctx.beginPath();
    ctx.arc(50, 25, 20, 0, Math.PI * 2);
    ctx.fill();
    
    return canvas.toDataURL();
  } catch (e) {
    return 'canvas_error';
  }
}

/**
 * Get WebGL fingerprint for enhanced device identification
 * @returns {string} - WebGL fingerprint
 */
function getWebGLFingerprint() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) return 'webgl_not_supported';
    
    const renderer = gl.getParameter(gl.RENDERER);
    const vendor = gl.getParameter(gl.VENDOR);
    const version = gl.getParameter(gl.VERSION);
    const shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
    
    return `${renderer}|${vendor}|${version}|${shadingLanguageVersion}`;
  } catch (e) {
    return 'webgl_error';
  }
}

// =============================================================================
// BROWSER COMPATIBILITY UTILITIES
// =============================================================================

/**
 * Check if browser supports required features
 * @returns {object} - Object with feature support flags
 */
function checkBrowserCompatibility() {
  return {
    canvas: !!document.createElement('canvas').getContext,
    localStorage: typeof(Storage) !== 'undefined',
    fetch: typeof fetch !== 'undefined',
    webgl: !!(document.createElement('canvas').getContext('webgl') || 
              document.createElement('canvas').getContext('experimental-webgl')),
    geolocation: 'geolocation' in navigator,
    deviceOrientation: 'DeviceOrientationEvent' in window,
    touchSupport: 'ontouchstart' in window || navigator.maxTouchPoints > 0
  };
}

// =============================================================================
// ANALYTICS AND DATA UTILITIES
// =============================================================================

/**
 * Escape HTML special characters to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
  if (text == null) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Calculate percentage with safe division
 * @param {number} part - The part value
 * @param {number} total - The total value
 * @param {number} decimals - Number of decimal places (default: 1)
 * @returns {number} - Percentage value
 */
function calculatePercentage(part, total, decimals = 1) {
  if (total === 0) return 0;
  return Math.round((part / total) * 100 * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

/**
 * Sort array of objects by a property
 * @param {Array} array - Array to sort
 * @param {string} property - Property to sort by
 * @param {boolean} ascending - Whether to sort in ascending order (default: true)
 * @returns {Array} - Sorted array
 */
function sortByProperty(array, property, ascending = true) {
  return [...array].sort((a, b) => {
    const aVal = a[property];
    const bVal = b[property];
    
    if (aVal < bVal) return ascending ? -1 : 1;
    if (aVal > bVal) return ascending ? 1 : -1;
    return 0;
  });
}

// =============================================================================
// MISSING COMMON UTILITIES
// =============================================================================

/**
 * Debounce function: returns a function, that, as long as it continues to be invoked, will not
 * be triggered. The function will be called after it stops being called for N milliseconds.
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @returns {Function}
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Throttle function: returns a function, that, as long as it continues to be invoked, will only
 * trigger at most once every N milliseconds.
 * @param {Function} func - Function to throttle
 * @param {number} limit - Milliseconds to wait
 * @returns {Function}
 */
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Generate a random ID string
 * @returns {string}
 */
function generateId() {
  return 'id-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Deep clone an object or array
 * @param {any} obj
 * @returns {any}
 */
function deepClone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if a value is empty (null, undefined, empty string, array, or object)
 * @param {any} value
 * @returns {boolean}
 */
function isEmpty(value) {
  if (value == null) return true;
  if (Array.isArray(value) || typeof value === 'string') return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

/**
 * Simple localStorage wrapper
 */
const storage = {
  set(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
  },
  get(key) {
    try {
      return JSON.parse(localStorage.getItem(key));
    } catch {
      return null;
    }
  },
  remove(key) {
    localStorage.removeItem(key);
  },
  clear() {
    localStorage.clear();
  }
};

/**
 * Validate email address format
 * @param {string} email
 * @returns {boolean}
 */
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Close modal when clicking outside (global event listener)
document.addEventListener('click', (e) => {
  if (e.target.id === 'customModal') {
    const modal = document.getElementById('customModal');
    if (modal) modal.classList.remove('show');
  }
});

// Add global error handler for unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  showNotification('An unexpected error occurred. Please try again.', 'error');
});

// Prevent default form submission for forms with 'prevent-default' class
document.addEventListener('submit', (e) => {
  if (e.target.classList.contains('prevent-default')) {
    e.preventDefault();
  }
});

// Auto-setup modal controls when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  setupModalControls();
  
  // Add global error handler for modal operations
  window.addEventListener('error', function(event) {
    if (event.error && event.error.message.includes('modal')) {
      console.warn('Modal operation failed:', event.error);
    }
  });
});

console.log('Common utilities loaded successfully');

// =============================================================================
// GLOBAL EXPORTS (for modules/compatibility)
// =============================================================================

// Make functions available globally
if (typeof window !== 'undefined') {
  // Export all functions to global scope for backward compatibility
  window.CommonUtils = {
    showNotification,
    showAlert,
    showMessage,
    customAlert,
    customConfirm,
    showCustomModal,
    getElement,
    addEventListenerSafe,
    addEventListeners,
    toggleElement,
    setButtonLoading,
    setupModalControls,
    showModal,
    hideModal,
    fetchWithLoading,
    postJSON,
    getWithRetry,
    escapeHtml,
    formatTimestamp,
    formatDateTime,
    formatDisplayTime,
    calculateDuration,
    getDateString,
    getDefaultEndTime,
    downloadFile,
    downloadCSV,
    showLoading,
    createLoadingSpinner,
    validateForm,
    clearFormErrors,
    setupEventListeners,
    getCanvasFingerprint,
    getWebGLFingerprint,
    checkBrowserCompatibility,
    calculatePercentage,
    sortByProperty,
    debounce,
    throttle,
    generateId,
    deepClone,
    isEmpty,
    storage,
    isValidEmail
  };

  // Also make functions available directly on window for easy access
  window.showNotification = showNotification;
  window.showAlert = showAlert;
  window.showMessage = showMessage;
  window.customAlert = customAlert;
  window.customConfirm = customConfirm;
  window.showCustomModal = showCustomModal;
  window.getElement = getElement;
  window.addEventListenerSafe = addEventListenerSafe;
  window.addEventListeners = addEventListeners;
  window.toggleElement = toggleElement;
  window.setButtonLoading = setButtonLoading;
  window.setupModalControls = setupModalControls;
  window.showModal = showModal;
  window.hideModal = hideModal;
  window.fetchWithLoading = fetchWithLoading;
  window.postJSON = postJSON;
  window.getWithRetry = getWithRetry;
  window.escapeHtml = escapeHtml;
  window.formatTimestamp = formatTimestamp;
  window.formatDateTime = formatDateTime;
  window.formatDisplayTime = formatDisplayTime;
  window.calculateDuration = calculateDuration;
  window.getDateString = getDateString;
  window.getDefaultEndTime = getDefaultEndTime;
  window.downloadFile = downloadFile;
  window.downloadCSV = downloadCSV;
  window.showLoading = showLoading;
  window.createLoadingSpinner = createLoadingSpinner;
  window.validateForm = validateForm;
  window.clearFormErrors = clearFormErrors;
  window.setupEventListeners = setupEventListeners;
  window.getCanvasFingerprint = getCanvasFingerprint;
  window.getWebGLFingerprint = getWebGLFingerprint;
  window.checkBrowserCompatibility = checkBrowserCompatibility;
  window.calculatePercentage = calculatePercentage;
  window.sortByProperty = sortByProperty;
  window.debounce = debounce;
  window.throttle = throttle;
  window.generateId = generateId;
  window.deepClone = deepClone;
  window.isEmpty = isEmpty;
  window.storage = storage;
  window.isValidEmail = isValidEmail;
}
