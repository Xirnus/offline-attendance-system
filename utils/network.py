import socket
import subprocess
import platform

def get_hotspot_ip():
    """Get Windows hotspot IP address"""
    if platform.system() != "Windows":
        return get_default_ip()
    
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        # Look for Microsoft Wi-Fi Direct Virtual Adapter
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in [
                'Microsoft Wi-Fi Direct Virtual Adapter',
                'Local Area Connection* 1'
            ]):
                # Find IPv4 address in next few lines
                for j in range(i, min(i+10, len(lines))):
                    if 'IPv4 Address' in lines[j]:
                        return lines[j].split(':')[1].strip()
        
        # Fallback: look for Windows hotspot range
        for line in lines:
            if 'IPv4 Address' in line and '192.168.137.' in line:
                return line.split(':')[1].strip()
                
    except Exception as e:
        print(f"Error getting hotspot IP: {e}")
    
    return get_default_ip()

def get_default_ip():
    """Get default IP using socket connection"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_all_network_interfaces():
    """Get all possible network interfaces"""
    interfaces = [get_hotspot_ip()]
    
    # Add common hotspot IPs if not already included
    common_ips = ['192.168.137.1', '192.168.173.1', '192.168.43.1']
    for ip in common_ips:
        if ip not in interfaces:
            interfaces.append(ip)
    
    return interfaces