#!/usr/bin/env python3
"""
Final demonstration: Generate and inspect actual report content
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.reports import ReportsService

def demonstrate_report_generation():
    """Generate actual reports and show their content"""
    print("=" * 60)
    print("📋 REPORT GENERATION DEMONSTRATION")
    print("=" * 60)
    
    reports_service = ReportsService()
    
    # Generate a comprehensive report
    print("\n1. Generating Comprehensive PDF Report...")
    pdf_file = reports_service.generate_pdf_report("comprehensive")
    print(f"✓ Generated: {os.path.basename(pdf_file)}")
    print(f"  Size: {os.path.getsize(pdf_file):,} bytes")
    
    # Generate analytics
    print("\n2. Generating Analytics...")
    analytics = reports_service.get_attendance_analytics()
    
    print("📊 Analytics Summary:")
    print(f"  Total Students: {analytics['overview']['total_students']}")
    print(f"  Total Sessions: {analytics['overview']['total_sessions']}")
    print(f"  Total Check-ins: {analytics['overview']['total_checkins']}")
    print(f"  Active Sessions: {analytics['overview']['active_sessions']}")
    
    print("\n📈 Course Breakdown:")
    for course, data in analytics['course_breakdown'].items():
        print(f"  {course}: {data['students']} students, {data['checkins']} check-ins")
    
    print("\n🎯 Top Attendance Rates:")
    # Sort by attendance rate and show top 3
    sorted_rates = sorted(analytics['attendance_rates'].items(), 
                         key=lambda x: x[1]['rate'], reverse=True)[:3]
    
    for student_id, data in sorted_rates:
        print(f"  {data['name']} ({student_id}): {data['rate']}% attendance")
        print(f"    Present: {data['present']}, Absent: {data['absent']}")
    
    # Show CSV content
    print("\n3. CSV Export Sample...")
    csv_file = reports_service.export_to_csv("students")
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"✓ Students CSV has {len(lines)} lines")
            print("📄 First few lines:")
            for i, line in enumerate(lines[:4]):
                print(f"  {i+1}: {line.strip()}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    # Directory overview
    print("\n4. Reports Directory Overview...")
    if os.path.exists(reports_service.reports_dir):
        files = [f for f in os.listdir(reports_service.reports_dir) 
                if os.path.isfile(os.path.join(reports_service.reports_dir, f))]
        
        print(f"📁 Total files: {len(files)}")
        
        # Group by type
        file_types = {}
        for file in files:
            ext = file.split('.')[-1].lower()
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(file)
        
        for file_type, file_list in file_types.items():
            total_size = sum(os.path.getsize(os.path.join(reports_service.reports_dir, f)) 
                           for f in file_list)
            print(f"  .{file_type}: {len(file_list)} files, {total_size:,} bytes")
    
    print("\n" + "=" * 60)
    print("✅ REPORT GENERATION DEMONSTRATION COMPLETE!")
    print("📁 Check the 'reports' directory for all generated files.")
    print("=" * 60)

if __name__ == "__main__":
    demonstrate_report_generation()
