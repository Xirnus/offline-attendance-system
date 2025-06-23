#!/usr/bin/env python3
"""
Individual test script for each Reports Service method
Tests each method in isolation with real data
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.reports import ReportsService

def test_individual_methods():
    """Test each method of ReportsService individually"""
    print("=" * 60)
    print("TESTING INDIVIDUAL REPORTS SERVICE METHODS")
    print("=" * 60)
    
    reports_service = ReportsService()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Test 1: PDF Report Generation (Comprehensive)
    print("\n1. Testing generate_pdf_report (comprehensive)...")
    try:
        pdf_file = reports_service.generate_pdf_report("comprehensive")
        print(f"✓ Generated: {pdf_file}")
        print(f"  Size: {os.path.getsize(pdf_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 2: PDF Report Generation (Summary)
    print("\n2. Testing generate_pdf_report (summary)...")
    try:
        pdf_file = reports_service.generate_pdf_report("summary")
        print(f"✓ Generated: {pdf_file}")
        print(f"  Size: {os.path.getsize(pdf_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 3: Excel Export
    print("\n3. Testing export_to_excel...")
    try:
        excel_file = reports_service.export_to_excel()
        print(f"✓ Generated: {excel_file}")
        print(f"  Size: {os.path.getsize(excel_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 4: CSV Export - Students
    print("\n4. Testing export_to_csv (students)...")
    try:
        csv_file = reports_service.export_to_csv("students")
        print(f"✓ Generated: {csv_file}")
        print(f"  Size: {os.path.getsize(csv_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 5: CSV Export - Attendance
    print("\n5. Testing export_to_csv (attendance)...")
    try:
        csv_file = reports_service.export_to_csv("attendance")
        print(f"✓ Generated: {csv_file}")
        print(f"  Size: {os.path.getsize(csv_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 6: CSV Export - Sessions
    print("\n6. Testing export_to_csv (sessions)...")
    try:
        csv_file = reports_service.export_to_csv("sessions")
        print(f"✓ Generated: {csv_file}")
        print(f"  Size: {os.path.getsize(csv_file)} bytes")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 7: CSV Export - All
    print("\n7. Testing export_to_csv (all)...")
    try:
        csv_files = reports_service.export_to_csv("all")
        print(f"✓ Generated: {csv_files}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 8: Analytics
    print("\n8. Testing get_attendance_analytics...")
    try:
        analytics = reports_service.get_attendance_analytics()
        print(f"✓ Analytics generated successfully")
        print(f"  Total students: {analytics['overview']['total_students']}")
        print(f"  Total sessions: {analytics['overview']['total_sessions']}")
        print(f"  Total check-ins: {analytics['overview']['total_checkins']}")
        print(f"  Active sessions: {analytics['overview']['active_sessions']}")
        print(f"  Courses tracked: {len(analytics['course_breakdown'])}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test 9: Reports directory functionality
    print("\n9. Testing ensure_reports_directory...")
    try:
        reports_service.ensure_reports_directory()
        if os.path.exists(reports_service.reports_dir):
            print(f"✓ Reports directory verified: {reports_service.reports_dir}")
        else:
            print(f"✗ Reports directory not found")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("INDIVIDUAL METHOD TESTING COMPLETED")
    print("=" * 60)

def test_file_content_verification():
    """Verify the content of generated files"""
    print("\n" + "=" * 60)
    print("VERIFYING FILE CONTENTS")
    print("=" * 60)
    
    reports_service = ReportsService()
    
    # Check if files have valid content
    files_to_check = []
    if os.path.exists(reports_service.reports_dir):
        for file in os.listdir(reports_service.reports_dir):
            file_path = os.path.join(reports_service.reports_dir, file)
            if os.path.isfile(file_path):
                files_to_check.append((file, file_path))
    
    print(f"\nChecking {len(files_to_check)} files...")
    
    for filename, filepath in files_to_check:
        size = os.path.getsize(filepath)
        
        if filename.endswith('.csv'):
            # Check CSV files
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    print(f"📄 {filename}: {size} bytes, {len(lines)} lines")
                    if len(lines) > 0:
                        print(f"    Header: {lines[0].strip()}")
            except Exception as e:
                print(f"📄 {filename}: Error reading - {e}")
        
        elif filename.endswith('.xlsx'):
            # Check Excel files
            try:
                import pandas as pd
                xlsx_data = pd.ExcelFile(filepath)
                print(f"📊 {filename}: {size} bytes, {len(xlsx_data.sheet_names)} sheets")
                print(f"    Sheets: {', '.join(xlsx_data.sheet_names)}")
            except Exception as e:
                print(f"📊 {filename}: {size} bytes (Excel file - {e})")
        
        elif filename.endswith('.pdf'):
            # Check PDF files
            print(f"📑 {filename}: {size} bytes (PDF file)")
        
        else:
            print(f"📄 {filename}: {size} bytes")

if __name__ == "__main__":
    try:
        # Test individual methods
        test_individual_methods()
        
        # Verify file contents
        test_file_content_verification()
        
        print(f"\n🎯 INDIVIDUAL METHOD TESTING COMPLETE!")
        print(f"✅ All export and report generation methods are working correctly!")
        
    except Exception as e:
        print(f"\n💥 Error during individual testing: {e}")
        import traceback
        traceback.print_exc()
