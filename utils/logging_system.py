"""
Centralized Logging System for Offline Attendance System

This module provides structured logging, error handling, and monitoring
capabilities to replace debug statements and improve system observability.

Features:
- Structured JSON logging
- Multiple log levels and handlers
- Error tracking and reporting
- Performance monitoring
- User-friendly error messages
- Log rotation and cleanup

Replaces all debug print statements with proper logging.
"""

import logging
import logging.handlers
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from config.config import Config

class StructuredLogger:
    """Centralized logging system with structured output"""
    
    def __init__(self, name: str = "attendance_system"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging with multiple handlers"""
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create logs directory
        log_dir = os.path.join(Config.PROJECT_ROOT, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'attendance_system.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        
        # Custom formatter for structured logging
        formatter = StructuredFormatter()
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        
    def log_event(self, level: str, message: str, **kwargs):
        """Log structured event with additional context"""
        extra_data = {
            'timestamp': datetime.now().isoformat(),
            'component': kwargs.get('component', 'unknown'),
            'action': kwargs.get('action', 'unknown'),
            'user_id': kwargs.get('user_id'),
            'session_id': kwargs.get('session_id'),
            'ip_address': kwargs.get('ip_address'),
            'duration_ms': kwargs.get('duration_ms'),
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra={'structured_data': extra_data})
    
    def log_database_operation(self, operation: str, table: str, 
                             duration_ms: float = None, error: str = None):
        """Log database operations for performance monitoring"""
        self.log_event(
            'info' if not error else 'error',
            f"Database {operation} on {table}",
            component='database',
            action=operation,
            table=table,
            duration_ms=duration_ms,
            error=error
        )
    
    def log_api_request(self, method: str, endpoint: str, status_code: int,
                       duration_ms: float, user_agent: str = None, ip: str = None):
        """Log API requests for monitoring"""
        self.log_event(
            'info',
            f"{method} {endpoint} - {status_code}",
            component='api',
            action='request',
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            user_agent=user_agent,
            ip_address=ip
        )
    
    def log_attendance_event(self, student_id: str, action: str, 
                           session_id: int = None, error: str = None):
        """Log attendance-related events"""
        self.log_event(
            'info' if not error else 'warning',
            f"Attendance {action} for student {student_id}",
            component='attendance',
            action=action,
            student_id=student_id,
            session_id=session_id,
            error=error
        )
    
    def log_security_event(self, event_type: str, details: str, 
                          severity: str = 'warning', **kwargs):
        """Log security-related events"""
        self.log_event(
            severity,
            f"Security event: {event_type} - {details}",
            component='security',
            action=event_type,
            severity=severity,
            **kwargs
        )
    
    def log_error(self, error: Exception, context: str = None, **kwargs):
        """Log errors with full traceback and context"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context,
            **kwargs
        }
        
        self.log_event(
            'error',
            f"Error in {context or 'unknown'}: {str(error)}",
            component='error_handler',
            action='error_occurred',
            **error_data
        )
    
    def log_performance(self, operation: str, duration_ms: float, 
                       threshold_ms: float = 1000, **kwargs):
        """Log performance metrics and slow operations"""
        level = 'warning' if duration_ms > threshold_ms else 'info'
        
        self.log_event(
            level,
            f"Performance: {operation} took {duration_ms:.2f}ms",
            component='performance',
            action='timing',
            operation=operation,
            duration_ms=duration_ms,
            slow_operation=duration_ms > threshold_ms,
            **kwargs
        )

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record):
        # Base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # Add exception info if available
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)

class ErrorHandler:
    """Centralized error handling and user-friendly messages"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.error_messages = {
            'database_connection': "Unable to connect to the database. Please check if the system is properly initialized.",
            'database_locked': "Database is temporarily locked. Please try again in a moment.",
            'invalid_student_id': "Invalid student ID format. Please check the student ID and try again.",
            'session_not_active': "No active attendance session. Please start a session first.",
            'token_expired': "QR code has expired. Please generate a new QR code.",
            'device_blocked': "This device has been blocked. Please contact the administrator.",
            'rate_limit_exceeded': "Too many requests. Please wait before trying again.",
            'file_upload_error': "File upload failed. Please check the file format and try again.",
            'network_error': "Network connection issue. Please check your connection.",
            'permission_denied': "Permission denied. You don't have access to this resource."
        }
    
    def handle_error(self, error: Exception, context: str = None, 
                    user_message: str = None) -> Dict[str, Any]:
        """Handle error and return user-friendly response"""
        
        # Log the error
        self.logger.log_error(error, context)
        
        # Determine error type and user message
        error_type = type(error).__name__
        
        if user_message:
            message = user_message
        else:
            message = self._get_user_friendly_message(error, error_type)
        
        return {
            'error': True,
            'message': message,
            'error_id': self._generate_error_id(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_user_friendly_message(self, error: Exception, error_type: str) -> str:
        """Get user-friendly error message"""
        error_str = str(error).lower()
        
        # Check for known error patterns
        if 'database is locked' in error_str:
            return self.error_messages['database_locked']
        elif 'no such table' in error_str or 'no such column' in error_str:
            return self.error_messages['database_connection']
        elif 'permission denied' in error_str:
            return self.error_messages['permission_denied']
        elif 'connection' in error_str and 'refused' in error_str:
            return self.error_messages['network_error']
        else:
            return f"An unexpected error occurred. Please try again or contact support if the issue persists. (Error ID: {self._generate_error_id()})"
    
    def _generate_error_id(self) -> str:
        """Generate unique error ID for tracking"""
        import uuid
        return str(uuid.uuid4())[:8]

# Global logger instance
_logger_instance = None

def get_logger(name: str = "attendance_system") -> StructuredLogger:
    """Get or create logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name)
    return _logger_instance

def get_error_handler() -> ErrorHandler:
    """Get error handler instance"""
    return ErrorHandler(get_logger())

# Convenience functions for common logging patterns
def log_info(message: str, **kwargs):
    """Log info message"""
    get_logger().log_event('info', message, **kwargs)

def log_warning(message: str, **kwargs):
    """Log warning message"""
    get_logger().log_event('warning', message, **kwargs)

def log_error(message: str, **kwargs):
    """Log error message"""
    get_logger().log_event('error', message, **kwargs)

def log_debug(message: str, **kwargs):
    """Log debug message"""
    get_logger().log_event('debug', message, **kwargs)

# Decorator for performance monitoring
def monitor_performance(operation_name: str = None):
    """Decorator to monitor function performance"""
    def decorator(func):
        import functools
        import time
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                get_logger().log_performance(op_name, duration_ms)
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                op_name = operation_name or f"{func.__module__}.{func.__name__}"
                
                get_logger().log_error(e, context=op_name)
                raise
        
        return wrapper
    return decorator

# Context manager for database operations
class DatabaseOperationLogger:
    """Context manager for logging database operations"""
    
    def __init__(self, operation: str, table: str = None):
        self.operation = operation
        self.table = table or 'unknown'
        self.start_time = None
        self.logger = get_logger()
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration_ms = (time.time() - self.start_time) * 1000 if self.start_time else 0
        
        if exc_type is None:
            self.logger.log_database_operation(self.operation, self.table, duration_ms)
        else:
            self.logger.log_database_operation(
                self.operation, self.table, duration_ms, str(exc_val)
            )
        
        return False  # Don't suppress exceptions
