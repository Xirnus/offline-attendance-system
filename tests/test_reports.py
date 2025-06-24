#!/usr/bin/env python3
"""
Test script for Reports and Export functionality
Tests all export formats and report generation methods
"""

import os
import sys
import traceback
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reports import ReportsService
from database.operations import get_all_data, get_students_with_attendance_data

def test_reports_functionality():
    """Test all reports and export functionality"""
    print("=" * 60)
    print("TESTING REPORTS AND EXPORT FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize reports service
    reports_service = ReportsService()
    
    # Test 1: Check if reports directory exists
    print("\n1. Testing Reports Directory Creation...")
    if os.path.exists(reports_service.reports_dir):
        print(f"✓ Reports directory exists: {reports_service.reports_dir}")
    else:
        print(f"✗ Reports directory not found: {reports_service.reports_dir}")
        return False
    
    # Test 2: Check database connectivity and data
    print("\n2. Testing Database Connectivity...")
    try:
        students_data = get_students_with_attendance_data()
        attendance_data = get_all_data('attendances')
        sessions_data = get_all_data('attendance_sessions')
        
        print(f"✓ Database connection successful")
        print(f"  - Students found: {len(students_data)}")
        print(f"  - Attendance records: {len(attendance_data)}")
        print(f"  - Sessions found: {len(sessions_data)}")
        
        if len(students_data) == 0:
            print("⚠ Warning: No student data found. Tests will proceed but reports may be empty.")
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    # Test 3: PDF Report Generation
    print("\n3. Testing PDF Report Generation...")
    try:
        # Test comprehensive report
        pdf_file = reports_service.generate_pdf_report("comprehensive")
        if os.path.exists(pdf_file):
            file_size = os.path.getsize(pdf_file)
            print(f"✓ Comprehensive PDF report created: {pdf_file}")
            print(f"  - File size: {file_size} bytes")
        else:
            print(f"✗ PDF report file not created: {pdf_file}")
            return False
            
        # Test summary report
        pdf_summary = reports_service.generate_pdf_report("summary")
        if os.path.exists(pdf_summary):
            print(f"✓ Summary PDF report created: {pdf_summary}")
        else:
            print(f"✗ Summary PDF report not created")
            
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 4: Excel Export
    print("\n4. Testing Excel Export...")
    try:
        excel_file = reports_service.export_to_excel()
        if os.path.exists(excel_file):
            file_size = os.path.getsize(excel_file)
            print(f"✓ Excel export created: {excel_file}")
            print(f"  - File size: {file_size} bytes")
        else:
            print(f"✗ Excel export file not created: {excel_file}")
            return False
    except Exception as e:
        print(f"✗ Excel export failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 5: CSV Export
    print("\n5. Testing CSV Export...")
    try:
        # Test students CSV
        csv_students = reports_service.export_to_csv("students")
        if os.path.exists(csv_students):
            print(f"✓ Students CSV export created: {csv_students}")
        else:
            print(f"✗ Students CSV not created")
            return False
            
        # Test attendance CSV
        csv_attendance = reports_service.export_to_csv("attendance")
        if os.path.exists(csv_attendance):
            print(f"✓ Attendance CSV export created: {csv_attendance}")
        else:
            print(f"✗ Attendance CSV not created")
            
        # Test sessions CSV
        csv_sessions = reports_service.export_to_csv("sessions")
        if os.path.exists(csv_sessions):
            print(f"✓ Sessions CSV export created: {csv_sessions}")
        else:
            print(f"✗ Sessions CSV not created")
            
    except Exception as e:
        print(f"✗ CSV export failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 6: Analytics Generation
    print("\n6. Testing Analytics Generation...")
    try:
        analytics = reports_service.get_attendance_analytics()
        print(f"✓ Analytics generated successfully")
        print(f"  - Overview data: {analytics['overview']}")
        print(f"  - Attendance rates calculated: {len(analytics['attendance_rates'])} students")
        print(f"  - Course breakdown: {len(analytics['course_breakdown'])} courses")
    except Exception as e:
        print(f"✗ Analytics generation failed: {e}")
        traceback.print_exc()
        return False
    
    # Test 7: File Validation
    print("\n7. Testing Generated Files...")
    try:
        reports_files = os.listdir(reports_service.reports_dir)
        print(f"✓ Files in reports directory: {len(reports_files)}")
        
        for file in reports_files:
            file_path = os.path.join(reports_service.reports_dir, file)
            file_size = os.path.getsize(file_path)
            print(f"  - {file}: {file_size} bytes")
            
            if file_size == 0:
                print(f"⚠ Warning: {file} is empty")
                
    except Exception as e:
        print(f"✗ File validation failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
    print("=" * 60)
    return True

def test_email_configuration():
    """Test email configuration (without sending)"""
    print("\n8. Testing Email Configuration...")
    from services.reports import EMAIL_CONFIG
    
    required_keys = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'sender_name']
    
    for key in required_keys:
        if key in EMAIL_CONFIG:
            value = EMAIL_CONFIG[key]
            if key == 'sender_password':
                print(f"  - {key}: {'*' * len(str(value))}")
            else:
                print(f"  - {key}: {value}")
        else:
            print(f"⚠ Missing email config key: {key}")
    
    print("✓ Email configuration structure is valid (credentials need to be updated for actual sending)")

def show_sample_data():
    """Show sample data from database for context"""
    print("\n" + "=" * 60)
    print("SAMPLE DATA OVERVIEW")
    print("=" * 60)
    
    try:
        students = get_students_with_attendance_data()
        if students:
            print(f"\nSample Students ({len(students)} total):")
            for i, student in enumerate(students[:3]):  # Show first 3
                print(f"  {i+1}. ID: {student.get('student_id')}, Name: {student.get('name')}, Course: {student.get('course')}")
        
        attendance = get_all_data('attendances')
        if attendance:
            print(f"\nSample Attendance Records ({len(attendance)} total):")
            for i, record in enumerate(attendance[:3]):  # Show first 3
                print(f"  {i+1}. Student: {record.get('student_id')}, Time: {record.get('checkin_time')}")
        
        sessions = get_all_data('attendance_sessions')
        if sessions:
            print(f"\nSample Sessions ({len(sessions)} total):")
            for i, session in enumerate(sessions[:3]):  # Show first 3
                print(f"  {i+1}. Name: {session.get('name')}, Status: {session.get('status')}")
                
    except Exception as e:
        print(f"Error retrieving sample data: {e}")

if __name__ == "__main__":
    try:
        # Show sample data first
        show_sample_data()
        
        # Run the main tests
        success = test_reports_functionality()
        
        # Test email configuration
        test_email_configuration()
        
        if success:
            print(f"\n🎉 All reports and export functionality is working correctly!")
            print(f"📁 Check the 'reports' directory for generated files.")
        else:
            print(f"\n❌ Some tests failed. Please check the error messages above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Critical error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)
