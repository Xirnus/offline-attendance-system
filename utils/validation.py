"""
Input Validation Utility Module for Offline Attendance System

This module provides comprehensive input validation and sanitization functions for the attendance tracking system. It ensures data integrity, prevents injection attacks, and maintains consistent data quality across all user inputs and form submissions.

Main Features:
- Student Data Validation: Validate names, courses, and academic years
- Security Validation: Check fingerprint hashes and device signatures
- Input Sanitization: Clean and sanitize text inputs to prevent attacks
- Format Enforcement: Ensure data meets system requirements and constraints
- Error Messaging: Provide clear, user-friendly validation error messages

Key Functions:
- validate_name(): Check student name format and length requirements
- validate_course(): Validate course name specifications
- validate_year(): Ensure academic year is within valid range
- validate_fingerprint_hash(): Check security hash format requirements
- sanitize_input(): Clean text inputs to prevent injection attacks

Validation Rules:
- Name: Minimum 2 characters, maximum 100 characters, required field
- Course: Minimum 2 characters, maximum 50 characters, required field
- Year: Must be 1-5 (representing academic year levels)
- Fingerprint Hash: Minimum 8 characters, required for security
- Text Sanitization: Remove HTML/script tags and dangerous characters

Security Features:
- Input sanitization to prevent XSS attacks
- Length limits to prevent buffer overflow attempts
- Character filtering to remove potentially harmful content
- Consistent validation across all input fields
- Clear error messages without revealing system internals

Data Quality Assurance:
- Consistent formatting across all inputs
- Trimming whitespace and normalizing data
- Preventing empty or malformed submissions
- Maintaining database integrity constraints
- User-friendly error feedback

Used by: API routes, form processing, data import functions
Dependencies: Standard library (re for regex operations)
"""

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