"""
Rate Limiting Service Module for Offline Attendance System

This module provides IP-based rate limiting functionality to protect the attendance system from abuse, spam, and denial-of-service attacks. It implements a sliding window algorithm to track and limit requests per IP address within configurable time periods.

Main Features:
- IP-based Rate Limiting: Track requests per IP address
- Sliding Window Algorithm: Time-based request counting with automatic cleanup
- Thread-safe Operations: Concurrent request handling with thread locks
- Configurable Limits: Customizable request limits and time windows
- Automatic Cleanup: Old request records are automatically purged
- Real IP Detection: Handles proxy headers and forwarded IPs

Key Functions:
- is_rate_limited(): Check if IP address has exceeded rate limits
- get_client_ip(): Extract real client IP from request headers

Rate Limiting Logic:
- Tracks timestamps of requests per IP address
- Automatically removes expired request records
- Configurable maximum requests per time window
- Thread-safe operations for concurrent access
- Memory-efficient with automatic cleanup

Security Features:
- Protection against brute force attacks
- QR code generation spam prevention
- API endpoint abuse mitigation
- Configurable rate limits per endpoint
- Real IP detection through proxy headers

Configuration:
- RATE_LIMIT_REQUESTS: Maximum requests per time window
- RATE_LIMIT_WINDOW: Time window in seconds for rate limiting
- Default values can be overridden per function call

Used by: API routes, QR code generation, authentication endpoints
Dependencies: Standard library (time, threading, collections), config settings
"""

import time
import threading
from collections import defaultdict
from config.config import Config

# Rate limiting storage
request_counts = defaultdict(list)
rate_limit_lock = threading.Lock()

def is_rate_limited(ip_address, max_requests=None, time_window=None):
    """Check if IP is rate limited"""
    max_requests = max_requests or Config.RATE_LIMIT_REQUESTS
    time_window = time_window or Config.RATE_LIMIT_WINDOW
    current_time = time.time()
    
    with rate_limit_lock:
        # Clean old requests
        request_counts[ip_address] = [
            req_time for req_time in request_counts[ip_address] 
            if current_time - req_time < time_window
        ]
        
        # Check if over limit
        if len(request_counts[ip_address]) >= max_requests:
            return True
        
        # Add current request
        request_counts[ip_address].append(current_time)
        return False

def get_client_ip(request):
    """Extract client IP from request"""
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)