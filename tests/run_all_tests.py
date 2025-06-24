#!/usr/bin/env python3
"""
Test Runner for Offline Attendance System
Executes all available tests in sequence
"""

import os
import sys
import subprocess
from datetime import datetime

def run_test_suite():
    """Run all tests in the test suite"""
    print("=" * 80)
    print("🧪 OFFLINE ATTENDANCE SYSTEM - COMPLETE TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get the directory where this script is located
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(tests_dir)
    
    # Python executable path
    python_exe = os.path.join(project_root, "attendance-system", "Scripts", "python.exe")
    
    # Test files to run in order
    test_files = [
        ("Basic Functionality Test", "test_reports_simple.py"),
        ("Individual Methods Test", "test_individual_methods.py"), 
        ("Comprehensive Reports Test", "test_reports.py"),
        ("Scheduling & Email Test", "test_scheduling.py"),
        ("Report Demonstration", "demo_reports.py"),
        ("Test Summary", "test_summary.py")
    ]
    
    results = []
    
    for test_name, test_file in test_files:
        print(f"\n📋 Running: {test_name}")
        print("-" * 50)
        
        test_path = os.path.join(tests_dir, test_file)
        
        try:
            # Change to project root directory before running test
            original_cwd = os.getcwd()
            os.chdir(project_root)
            
            # Run the test
            result = subprocess.run([python_exe, test_path], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=120)
            
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                print(f"✅ {test_name} - PASSED")
                results.append((test_name, "PASSED", None))
            else:
                print(f"❌ {test_name} - FAILED")
                print(f"Error: {result.stderr}")
                results.append((test_name, "FAILED", result.stderr))
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} - TIMEOUT")
            results.append((test_name, "TIMEOUT", "Test exceeded 120 seconds"))
        except Exception as e:
            print(f"💥 {test_name} - ERROR")
            print(f"Exception: {e}")
            results.append((test_name, "ERROR", str(e)))
    
    # Print final summary
    print("\n" + "=" * 80)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 80)
    
    passed = failed = timeout = error = 0
    
    for test_name, status, error_msg in results:
        status_icon = {
            "PASSED": "✅",
            "FAILED": "❌", 
            "TIMEOUT": "⏰",
            "ERROR": "💥"
        }.get(status, "❓")
        
        print(f"{status_icon} {test_name:<40} {status}")
        
        if status == "PASSED":
            passed += 1
        elif status == "FAILED":
            failed += 1
        elif status == "TIMEOUT":
            timeout += 1
        elif status == "ERROR":
            error += 1
    
    total = len(results)
    success_rate = (passed / total) * 100 if total > 0 else 0
    
    print("-" * 80)
    print(f"Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏰ Timeout: {timeout}")
    print(f"💥 Error: {error}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) had issues. Please review the results above.")
        return False

if __name__ == "__main__":
    try:
        success = run_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Critical error running test suite: {e}")
        sys.exit(1)
