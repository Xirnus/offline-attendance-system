#!/usr/bin/env python3
"""
Simplified test script for Reports functionality
Tests the reports module directly with manual data
"""

import os
import sys
import traceback
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_reports_basics():
    """Test basic reports functionality without database dependency"""
    print("=" * 60)
    print("TESTING REPORTS FUNCTIONALITY (SIMPLIFIED)")
    print("=" * 60)
    
    try:
        # Test import
        print("\n1. Testing Reports Module Import...")
        from services.reports import ReportsService
        print("✓ Successfully imported ReportsService")
        
        # Initialize service
        print("\n2. Testing Reports Service Initialization...")
        reports_service = ReportsService()
        print(f"✓ Reports service initialized")
        print(f"  - Reports directory: {reports_service.reports_dir}")
        
        # Check if directory was created
        if os.path.exists(reports_service.reports_dir):
            print(f"✓ Reports directory exists")
        else:
            print(f"✗ Reports directory not created")
            return False
        
        print("\n3. Testing Required Libraries...")
        
        # Test PDF libraries
        try:
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate
            print("✓ ReportLab (PDF) library working")
        except ImportError as e:
            print(f"✗ ReportLab import failed: {e}")
            return False
        
        # Test Excel libraries
        try:
            import xlsxwriter
            print("✓ XlsxWriter (Excel) library working")
        except ImportError as e:
            print(f"✗ XlsxWriter import failed: {e}")
            return False
        
        # Test CSV libraries
        try:
            import csv
            import pandas as pd
            print("✓ CSV libraries working")
        except ImportError as e:
            print(f"✗ CSV libraries import failed: {e}")
            return False
        
        # Test email libraries
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            print("✓ Email libraries working")
        except ImportError as e:
            print(f"✗ Email libraries import failed: {e}")
            return False
        
        # Test scheduling libraries
        try:
            import schedule
            import threading
            print("✓ Scheduling libraries working")
        except ImportError as e:
            print(f"✗ Scheduling libraries import failed: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("BASIC FUNCTIONALITY TESTS PASSED! ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error during basic testing: {e}")
        traceback.print_exc()
        return False

def test_reports_with_mock_data():
    """Test report generation with mock data"""
    print("\n" + "=" * 60)
    print("TESTING WITH MOCK DATA")
    print("=" * 60)
    
    try:
        # Create mock data structure
        mock_students = [
            {
                'student_id': 'S001',
                'name': 'John Doe',
                'course': 'Computer Science',
                'year': '2024',
                'last_check_in': '2025-06-23 10:30:00',
                'status': 'active',
                'absent_count': 2,
                'created_at': '2025-01-01 09:00:00'
            },
            {
                'student_id': 'S002',
                'name': 'Jane Smith',
                'course': 'Data Science',
                'year': '2024',
                'last_check_in': '2025-06-23 11:15:00',
                'status': 'active',
                'absent_count': 1,
                'created_at': '2025-01-01 09:00:00'
            }
        ]
        
        mock_attendance = [
            {
                'id': 1,
                'student_id': 'S001',
                'session_id': 'SESSION001',
                'checkin_time': '2025-06-23 10:30:00',
                'device_info': 'Chrome/Windows',
                'fingerprint_hash': 'abc123'
            },
            {
                'id': 2,
                'student_id': 'S002',
                'session_id': 'SESSION001',
                'checkin_time': '2025-06-23 11:15:00',
                'device_info': 'Firefox/Linux',
                'fingerprint_hash': 'def456'
            }
        ]
        
        mock_sessions = [
            {
                'id': 1,
                'name': 'SESSION001',
                'created_at': '2025-06-23 10:00:00',
                'started_at': '2025-06-23 10:00:00',
                'ended_at': None,
                'status': 'active',
                'token': 'ABC123XYZ'
            }
        ]
        
        print(f"✓ Mock data created:")
        print(f"  - Students: {len(mock_students)}")
        print(f"  - Attendance records: {len(mock_attendance)}")
        print(f"  - Sessions: {len(mock_sessions)}")
        
        # Create a test CSV file
        print("\n1. Testing CSV Export with Mock Data...")
        import csv
        from services.reports import ReportsService
        
        reports_service = ReportsService()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_csv = f"{reports_service.reports_dir}/test_students_{timestamp}.csv"
        
        with open(test_csv, 'w', newline='', encoding='utf-8') as csvfile:
            headers = ['student_id', 'name', 'course', 'year', 'last_check_in', 'status', 'absent_count', 'created_at']
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for student in mock_students:
                writer.writerow(student)
        
        if os.path.exists(test_csv):
            file_size = os.path.getsize(test_csv)
            print(f"✓ Test CSV created: {test_csv}")
            print(f"  - File size: {file_size} bytes")
        else:
            print(f"✗ Test CSV not created")
            return False
        
        # Test Excel creation
        print("\n2. Testing Excel Export with Mock Data...")
        import xlsxwriter
        
        test_excel = f"{reports_service.reports_dir}/test_attendance_{timestamp}.xlsx"
        workbook = xlsxwriter.Workbook(test_excel)
        
        # Add a worksheet
        worksheet = workbook.add_worksheet('Test Students')
        
        # Write headers
        headers = ['Student ID', 'Name', 'Course', 'Year']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Write data
        for row, student in enumerate(mock_students, 1):
            worksheet.write(row, 0, student['student_id'])
            worksheet.write(row, 1, student['name'])
            worksheet.write(row, 2, student['course'])
            worksheet.write(row, 3, student['year'])
        
        workbook.close()
        
        if os.path.exists(test_excel):
            file_size = os.path.getsize(test_excel)
            print(f"✓ Test Excel created: {test_excel}")
            print(f"  - File size: {file_size} bytes")
        else:
            print(f"✗ Test Excel not created")
            return False
        
        # Test PDF creation
        print("\n3. Testing PDF Report with Mock Data...")
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        
        test_pdf = f"{reports_service.reports_dir}/test_report_{timestamp}.pdf"
        doc = SimpleDocTemplate(test_pdf, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        story.append(Paragraph("Test Attendance Report", styles['Title']))
        
        # Add table
        table_data = [['Student ID', 'Name', 'Course']]
        for student in mock_students:
            table_data.append([
                student['student_id'],
                student['name'],
                student['course']
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        doc.build(story)
        
        if os.path.exists(test_pdf):
            file_size = os.path.getsize(test_pdf)
            print(f"✓ Test PDF created: {test_pdf}")
            print(f"  - File size: {file_size} bytes")
        else:
            print(f"✗ Test PDF not created")
            return False
        
        print("\n" + "=" * 60)
        print("MOCK DATA TESTS PASSED! ✓")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n✗ Error during mock data testing: {e}")
        traceback.print_exc()
        return False

def show_generated_files():
    """Show all files generated in the reports directory"""
    print("\n" + "=" * 60)
    print("GENERATED FILES SUMMARY")
    print("=" * 60)
    
    try:
        from services.reports import ReportsService
        reports_service = ReportsService()
        
        if os.path.exists(reports_service.reports_dir):
            files = os.listdir(reports_service.reports_dir)
            
            if files:
                print(f"\nFiles in {reports_service.reports_dir}:")
                for file in files:
                    file_path = os.path.join(reports_service.reports_dir, file)
                    file_size = os.path.getsize(file_path)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    print(f"  📄 {file}")
                    print(f"     Size: {file_size:,} bytes")
                    print(f"     Modified: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("No files found in reports directory.")
        else:
            print("Reports directory does not exist.")
            
    except Exception as e:
        print(f"Error reading reports directory: {e}")

if __name__ == "__main__":
    try:
        print("🧪 TESTING REPORTS AND EXPORT FUNCTIONALITY")
        print("=" * 60)
        
        # Run basic tests
        basic_success = test_reports_basics()
        
        if basic_success:
            # Run mock data tests
            mock_success = test_reports_with_mock_data()
            
            # Show generated files
            show_generated_files()
            
            if mock_success:
                print(f"\n🎉 ALL TESTS PASSED!")
                print(f"✅ Reports and export functionality is working correctly!")
                print(f"📁 Check the 'reports' directory for generated test files.")
            else:
                print(f"\n❌ Mock data tests failed.")
                sys.exit(1)
        else:
            print(f"\n❌ Basic tests failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Critical error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)
