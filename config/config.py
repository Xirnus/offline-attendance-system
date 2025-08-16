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
import secrets
import sys

class Config:
    """Main application configuration"""
    # Handle PyInstaller bundled environment
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle - use directory beside the exe
        PROJECT_ROOT = os.path.dirname(sys.executable)
        DATABASE_DIR = os.path.join(PROJECT_ROOT, 'data')
    else:
        # Running as script - use project directory
        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        DATABASE_DIR = os.path.join(PROJECT_ROOT, 'database', 'db')
    
    # Ensure database directory exists
    os.makedirs(DATABASE_DIR, exist_ok=True)
    
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'attendance.db')
    CLASSES_DATABASE_PATH = os.path.join(DATABASE_DIR, 'classes.db')
    
    # Generate secure secret key if not provided via environment
    _DEFAULT_SECRET = 'dev-key-change-in-production'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    if not SECRET_KEY:
        # Check if we're in development (presence of .git directory)
        git_dir = os.path.join(PROJECT_ROOT, '.git')
        if os.path.exists(git_dir):
            # Development environment - use deterministic but secure key
            import hashlib
            project_hash = hashlib.sha256(PROJECT_ROOT.encode()).hexdigest()[:32]
            SECRET_KEY = f"dev_{project_hash}"
        else:
            # Production environment - generate random key
            SECRET_KEY = secrets.token_urlsafe(32)
            print("⚠️  WARNING: Generated new SECRET_KEY for production.")
            print("   Please set SECRET_KEY environment variable to persist this key.")
            print(f"   Current key: {SECRET_KEY}")
    
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