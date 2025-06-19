import time
import threading
from collections import defaultdict
from config import Config

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