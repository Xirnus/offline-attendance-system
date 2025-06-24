"""
Network Utilities Module for Offline Attendance System

This module provides network interface detection and IP address management for the
attendance system, with special focus on Windows hotspot detection and mobile hotspot connectivity. It ensures the system can properly detect and display the correct IP addresses for QR code access across different network configurations.

Main Features:
- Windows Hotspot Detection: Automatically detect Microsoft Wi-Fi Direct Virtual Adapter
- IP Address Resolution: Get system's active IP addresses for QR code URLs
- Multi-Interface Support: Handle multiple network interfaces and configurations
- Cross-Platform Compatibility: Fallback methods for different operating systems
- Common Hotspot Recognition: Detect standard mobile hotspot IP ranges

Key Functions:
- get_hotspot_ip(): Detect Windows hotspot IP address specifically
- get_default_ip(): Get primary network interface IP using socket connection
- get_all_network_interfaces(): Retrieve all available network interface IPs

Network Detection Logic:
- Windows: Parse ipconfig output for Wi-Fi Direct Virtual Adapter
- Fallback: Use socket connection to external server for IP detection
- Common Ranges: Recognize standard hotspot IP ranges (192.168.137.x, etc.)
- Error Handling: Graceful fallback to localhost on network errors

Use Cases:
- Mobile Hotspot QR Code Access: Students connecting via phone hotspots
- Classroom Network Setup: Teachers sharing internet via Windows hotspot
- Multi-Network Environments: Systems with multiple active interfaces
- Network Troubleshooting: Display all possible connection IPs

Technical Details:
- Windows ipconfig parsing for adapter detection
- Socket-based IP resolution for reliable connectivity
- Standard hotspot IP range recognition
- Cross-platform fallback mechanisms

Used by: Flask app initialization, QR code URL generation, network display
Dependencies: Standard library (socket, subprocess, platform)
"""

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
    common_ips = ['192.168.137.1', '192.168.173.1', '192.168.43.1', '192.168.1.2']
    for ip in common_ips:
        if ip not in interfaces:
            interfaces.append(ip)
    
    return interfaces