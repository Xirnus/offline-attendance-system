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