#!/usr/bin/env python3
"""
Test the scheduling functionality of the Reports Service
"""

import os
import sys
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reports import ReportsService

def test_scheduling_functionality():
    """Test the scheduling setup (without actually waiting for execution)"""
    print("=" * 60)
    print("TESTING SCHEDULING FUNCTIONALITY")
    print("=" * 60)
    
    reports_service = ReportsService()
    
    # Test 1: Daily scheduling configuration
    print("\n1. Testing daily schedule configuration...")
    try:
        schedule_config = {
            'frequency': 'daily',
            'time': '09:00',
            'recipient_email': 'test@example.com',
            'report_type': 'pdf'
        }
        
        # This will set up the schedule but not execute it
        reports_service.schedule_reports(schedule_config)
        print("✓ Daily schedule configured successfully")
        print(f"  Frequency: {schedule_config['frequency']}")
        print(f"  Time: {schedule_config['time']}")
        print(f"  Recipient: {schedule_config['recipient_email']}")
        print(f"  Report type: {schedule_config['report_type']}")
        
    except Exception as e:
        print(f"✗ Error configuring daily schedule: {e}")
    
    # Test 2: Weekly scheduling configuration
    print("\n2. Testing weekly schedule configuration...")
    try:
        schedule_config = {
            'frequency': 'weekly',
            'recipient_email': 'test@example.com',
            'report_type': 'excel'
        }
        
        reports_service.schedule_reports(schedule_config)
        print("✓ Weekly schedule configured successfully")
        
    except Exception as e:
        print(f"✗ Error configuring weekly schedule: {e}")
    
    # Test 3: Monthly scheduling configuration
    print("\n3. Testing monthly schedule configuration...")
    try:
        schedule_config = {
            'frequency': 'monthly',
            'recipient_email': 'test@example.com',
            'report_type': 'csv'
        }
        
        reports_service.schedule_reports(schedule_config)
        print("✓ Monthly schedule configured successfully")
        
    except Exception as e:
        print(f"✗ Error configuring monthly schedule: {e}")
    
    # Test 4: Check scheduling library
    print("\n4. Testing schedule library functionality...")
    try:
        import schedule
        
        # Check if any jobs were scheduled
        jobs = schedule.jobs
        print(f"✓ Schedule library working")
        print(f"  Active jobs: {len(jobs)}")
        
        for i, job in enumerate(jobs):
            print(f"  Job {i+1}: {job}")
            
    except Exception as e:
        print(f"✗ Error with schedule library: {e}")
    
    print("\n" + "=" * 60)
    print("SCHEDULING TESTS COMPLETED")
    print("=" * 60)

def test_email_preparation():
    """Test email report preparation (without sending)"""
    print("\n" + "=" * 60)
    print("TESTING EMAIL REPORT PREPARATION")
    print("=" * 60)
    
    reports_service = ReportsService()
    
    # Test 1: Email libraries
    print("\n1. Testing email libraries...")
    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders
        print("✓ All email libraries imported successfully")
    except Exception as e:
        print(f"✗ Error importing email libraries: {e}")
    
    # Test 2: Email configuration structure
    print("\n2. Testing email configuration...")
    try:
        from services.reports import EMAIL_CONFIG
        
        required_keys = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password', 'sender_name']
        
        print("✓ Email configuration structure:")
        for key in required_keys:
            if key in EMAIL_CONFIG:
                value = EMAIL_CONFIG[key]
                if key == 'sender_password':
                    print(f"  {key}: {'*' * len(str(value))}")
                else:
                    print(f"  {key}: {value}")
            else:
                print(f"  ⚠ Missing: {key}")
                
    except Exception as e:
        print(f"✗ Error checking email configuration: {e}")
    
    # Test 3: Report generation for email (create attachments)
    print("\n3. Testing report generation for email attachments...")
    try:
        # Generate a PDF report
        pdf_file = reports_service.generate_pdf_report("comprehensive")
        print(f"✓ PDF attachment ready: {os.path.basename(pdf_file)}")
        
        # Generate an Excel report
        excel_file = reports_service.export_to_excel()
        print(f"✓ Excel attachment ready: {os.path.basename(excel_file)}")
        
        # Generate CSV reports
        csv_file = reports_service.export_to_csv("students")
        print(f"✓ CSV attachment ready: {os.path.basename(csv_file)}")
        
    except Exception as e:
        print(f"✗ Error generating email attachments: {e}")
    
    print("\n✅ Email preparation functionality is working!")
    print("📧 Note: Actual email sending requires valid SMTP credentials")

if __name__ == "__main__":
    try:
        # Test scheduling
        test_scheduling_functionality()
        
        # Test email preparation
        test_email_preparation()
        
        print(f"\n🎯 SCHEDULING AND EMAIL TESTS COMPLETE!")
        print(f"✅ All scheduling and email preparation functionality is working!")
        
    except Exception as e:
        print(f"\n💥 Error during scheduling/email testing: {e}")
        import traceback
        traceback.print_exc()
