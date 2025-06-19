import os

class Config:
    DATABASE_PATH = 'attendance.db'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 5
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Token settings
    TOKEN_LENGTH = 16
    TOKEN_EXPIRY = 3600  # 1 hour

# Default app settings
DEFAULT_SETTINGS = {
    'max_uses_per_device': 1,
    'time_window_minutes': 1440,  # 24 hours
    'enable_fingerprint_blocking': True
}