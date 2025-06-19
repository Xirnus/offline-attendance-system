def extract_device_signature(user_agent):
    """Extract device signature from User-Agent"""
    ua = user_agent.lower()
    
    device_map = {
        'iphone': 'iphone',
        'ipad': 'ipad', 
        'android': 'android',
        'mobile': 'mobile'
    }
    
    for key, value in device_map.items():
        if key in ua:
            return value
    
    return 'desktop'

def generate_device_info(request_data):
    """Generate device information object"""
    return {
        'user_agent': request_data.get('user_agent', ''),
        'screen_resolution': request_data.get('screen_resolution', ''),
        'timezone': request_data.get('timezone', ''),
        'language': request_data.get('language', ''),
        'platform': request_data.get('platform', ''),
        'timestamp': request_data.get('timestamp', '')
    }