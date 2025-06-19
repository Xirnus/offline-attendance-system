import re

def validate_name(name):
    """Validate student name"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters"
    if len(name) > 100:
        return False, "Name too long"
    return True, "Valid"

def validate_course(course):
    """Validate course name"""
    if not course or len(course.strip()) < 2:
        return False, "Course must be specified"
    if len(course) > 50:
        return False, "Course name too long"
    return True, "Valid"

def validate_year(year):
    """Validate academic year"""
    if not year:
        return False, "Year must be specified"
    if year not in ['1', '2', '3', '4', '5']:
        return False, "Invalid year level"
    return True, "Valid"

def validate_fingerprint_hash(hash_value):
    """Validate fingerprint hash format"""
    if not hash_value:
        return False, "Fingerprint hash required"
    if len(hash_value) < 8:
        return False, "Invalid fingerprint hash"
    return True, "Valid"

def sanitize_input(text):
    """Sanitize text input"""
    if not text:
        return ""
    # Remove potentially harmful characters
    return re.sub(r'[<>"\']', '', str(text).strip())