"""
QR Code Generator Utility Module for Offline Attendance System

This module provides QR code generation functionality for the attendance tracking system.
It creates scannable QR codes containing URLs that point to attendance check-in forms,
enabling students to quickly access the attendance system via mobile devices.

Main Features:
- QR Code Image Generation: Create PNG images from text data
- URL Construction: Build proper scan URLs with tokens
- Mobile-Optimized: Generate QR codes optimized for phone cameras
- Memory-Efficient: Use BytesIO for in-memory image handling
- Format Support: PNG output format for web compatibility

Key Functions:
- generate_qr_code(): Creates QR code images from data strings
- build_qr_url(): Constructs proper URLs for QR code embedding

QR Code Workflow:
1. Token Generation: System creates unique attendance token
2. URL Building: Token is embedded into scannable URL
3. QR Creation: URL is encoded into QR code image
4. Display: QR code is shown to students for scanning
5. Scanning: Students scan QR code to access check-in form

Technical Details:
- Uses qrcode library for image generation
- BytesIO for memory-efficient image handling
- PNG format for web browser compatibility
- Dynamic URL construction based on request headers
- Automatic HTTPS/HTTP protocol detection

URL Structure:
- Format: {scheme}://{host}/scan/{token}
- Example: http://192.168.1.100:5000/scan/abc123token
- Supports both local and network access

Used by: API routes for QR code generation endpoint
Dependencies: qrcode library, BytesIO from standard library
"""

import qrcode
from io import BytesIO

def generate_qr_code(data):
    """Generate QR code image for given data"""
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def build_qr_url(request, token):
    """Build QR code URL from request and token"""
    host = request.headers.get('Host', 'localhost:5000')
    scheme = 'https' if request.is_secure else 'http'
    return f"{scheme}://{host}/scan/{token}"