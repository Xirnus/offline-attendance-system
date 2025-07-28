"""
Configuration Module for Offline Attendance System

This module defines all configuration settings, constants, and default values for the
attendance tracking system. It centralizes system parameters, security settings,
and operational constraints to ensure consistent behavior across all components.

Main Features:
- Application Configuration: Core Flask and system settings
- Security Parameters: Token settings, rate limits, and encryption keys
- Database Configuration: File paths and connection settings
- Default System Settings: Attendance policies and device restrictions
- Environment Support: Development and production configuration handling

Configuration Categories:
- Database: SQLite file paths and connection parameters
- Security: Secret keys, token lengths, and expiration times
- Rate Limiting: Request limits and time windows for abuse prevention
- Device Policy: Fingerprinting settings and usage restrictions
- Time Management: Session durations and validation windows

Key Configuration Classes:
- Config: Main application configuration with security and database settings
- DEFAULT_SETTINGS: System-wide attendance policies and device restrictions

Security Settings:
- SECRET_KEY: Flask session encryption (environment variable supported)
- TOKEN_LENGTH: QR code token character length for security
- TOKEN_EXPIRY: Token validity duration in seconds
- RATE_LIMIT_*: Request throttling to prevent abuse

Device Policy Settings:
- max_uses_per_device: [DEPRECATED] Previously used for time-window limits, now unused
- time_window_minutes: [DEPRECATED] Previously used for time-window limits, now unused  
- enable_fingerprint_blocking: Toggle device fingerprint validation per session

Development vs Production:
- Environment variable support for sensitive settings
- Default development values with production override capability
- Configurable paths for different deployment scenarios

Used by: All system components requiring configuration values
Dependencies: Standard library (os for environment variables)
"""

import os

class Config:
    """Main application configuration"""
    # Get the project root directory (parent of config folder)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_PATH = os.path.join(PROJECT_ROOT, 'database', 'db', 'attendance.db')
    CLASSES_DATABASE_PATH = os.path.join(PROJECT_ROOT, 'database', 'db', 'classes.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Token settings
    TOKEN_LENGTH = 16
    TOKEN_EXPIRY = 3600  # 1 hour
    
    @classmethod
    def ensure_database_directory(cls):
        """Ensure the database directory exists"""
        db_dir = os.path.join(cls.PROJECT_ROOT, 'database', 'db')
        os.makedirs(db_dir, exist_ok=True)
        return db_dir

# Default app settings
DEFAULT_SETTINGS = {
    'max_uses_per_device': 1,
    'time_window_minutes': 1440,  # 24 hours
    'enable_fingerprint_blocking': True
}