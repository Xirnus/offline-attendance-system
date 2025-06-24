"""
Test Suite for Offline Attendance System

This package contains comprehensive tests for all reports and export functionality.

Available test modules:
- test_reports: Main comprehensive test suite
- test_reports_simple: Simplified tests without database dependencies  
- test_individual_methods: Individual method testing
- test_scheduling: Scheduling and email functionality tests
- demo_reports: Live demonstration of report generation
- test_summary: Comprehensive test results summary

Usage:
    # Run from project root
    python tests/test_reports.py
    
    # Or import and run programmatically
    from tests import test_reports
    test_reports.test_reports_functionality()
"""

__version__ = "1.0.0"
__author__ = "Offline Attendance System"
__description__ = "Comprehensive test suite for reports and export functionality"

# Test modules
__all__ = [
    'test_reports',
    'test_reports_simple', 
    'test_individual_methods',
    'test_scheduling',
    'demo_reports',
    'test_summary'
]
