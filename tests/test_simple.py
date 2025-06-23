#!/usr/bin/env python3
"""
Simple Test Runner - No Unicode characters for Windows compatibility
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_simple_test():
    """Run a simple test without Unicode issues"""
    print("=" * 60)
    print("REPORTS AND EXPORT FUNCTIONALITY TEST")
    print("=" * 60)
    
    try:
        # Test basic imports
        print("\n1. Testing imports...")
        from services.reports import ReportsService
        print("OK - ReportsService imported successfully")
        
        # Test initialization
        print("\n2. Testing initialization...")
        reports_service = ReportsService()
        print("OK - ReportsService initialized")
        
        # Test directory creation
        print("\n3. Testing directory creation...")
        if os.path.exists(reports_service.reports_dir):
            print(f"OK - Reports directory exists: {reports_service.reports_dir}")
        else:
            print("FAIL - Reports directory not found")
            return False
        
        # Test PDF generation
        print("\n4. Testing PDF generation...")
        pdf_file = reports_service.generate_pdf_report("comprehensive")
        if os.path.exists(pdf_file):
            print(f"OK - PDF generated: {os.path.basename(pdf_file)}")
        else:
            print("FAIL - PDF not generated")
            return False
        
        # Test Excel export
        print("\n5. Testing Excel export...")
        excel_file = reports_service.export_to_excel()
        if os.path.exists(excel_file):
            print(f"OK - Excel generated: {os.path.basename(excel_file)}")
        else:
            print("FAIL - Excel not generated")
            return False
        
        # Test CSV export
        print("\n6. Testing CSV export...")
        csv_file = reports_service.export_to_csv("students")
        if os.path.exists(csv_file):
            print(f"OK - CSV generated: {os.path.basename(csv_file)}")
        else:
            print("FAIL - CSV not generated")
            return False
        
        # Test analytics
        print("\n7. Testing analytics...")
        analytics = reports_service.get_attendance_analytics()
        if analytics and 'overview' in analytics:
            print("OK - Analytics generated successfully")
            print(f"    Total students: {analytics['overview']['total_students']}")
            print(f"    Total sessions: {analytics['overview']['total_sessions']}")
        else:
            print("FAIL - Analytics not generated")
            return False
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_simple_test()
    if success:
        print("\nSUCCESS: All export and reports functionality is working!")
    else:
        print("\nFAILED: Some tests failed. Check the output above.")
    sys.exit(0 if success else 1)
