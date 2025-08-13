"""
Test script to verify that the build fixes resolve the class upload issue

This script simulates the conditions that occur when the application runs
as a PyInstaller executable on different computers.
"""

import os
import sys
import tempfile
import shutil

def test_path_resolution():
    """Test if path resolution works correctly in bundled environment"""
    print("🧪 Testing path resolution...")
    
    # Simulate PyInstaller environment
    original_frozen = getattr(sys, 'frozen', False)
    original_executable = sys.executable
    
    try:
        # Simulate bundled environment
        sys.frozen = True
        sys.executable = r"C:\SomeRandomPath\AttendanceSystem.exe"
        
        # Import and test config
        from config.config import Config
        
        print(f"   PROJECT_ROOT: {Config.PROJECT_ROOT}")
        print(f"   DATABASE_PATH: {Config.DATABASE_PATH}")
        print(f"   CLASSES_DATABASE_PATH: {Config.CLASSES_DATABASE_PATH}")
        
        # Check if paths are reasonable
        if "SomeRandomPath" in Config.PROJECT_ROOT:
            print("✅ Path resolution working correctly")
            return True
        else:
            print("❌ Path resolution not working")
            return False
            
    finally:
        # Restore original values
        if original_frozen:
            sys.frozen = original_frozen
        else:
            if hasattr(sys, 'frozen'):
                delattr(sys, 'frozen')
        sys.executable = original_executable

def test_database_creation():
    """Test if database creation works in a temporary directory"""
    print("🧪 Testing database creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test database path
        test_db_path = os.path.join(temp_dir, 'test_classes.db')
        
        try:
            from database.models import create_optimized_classes_schema
            
            print(f"   Creating test database at: {test_db_path}")
            result = create_optimized_classes_schema(test_db_path)
            
            if result and os.path.exists(test_db_path):
                print("✅ Database creation working correctly")
                return True
            else:
                print("❌ Database creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Database creation error: {e}")
            return False

def test_class_manager():
    """Test OptimizedClassManager initialization"""
    print("🧪 Testing OptimizedClassManager...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Create test database paths
            classes_db = os.path.join(temp_dir, 'classes.db')
            attendance_db = os.path.join(temp_dir, 'attendance.db')
            
            # Create attendance database schema first
            from database.models import create_all_tables
            
            # Temporarily override the database path for testing
            from config.config import Config
            original_db_path = Config.DATABASE_PATH
            Config.DATABASE_PATH = attendance_db
            
            try:
                create_all_tables()
            finally:
                # Restore original path
                Config.DATABASE_PATH = original_db_path
            
            # Test manager
            from database.class_table_manager import OptimizedClassManager
            
            print(f"   Initializing manager with test paths...")
            manager = OptimizedClassManager(classes_db, attendance_db)
            
            print("✅ OptimizedClassManager initialization working correctly")
            return True
            
        except Exception as e:
            print(f"❌ OptimizedClassManager error: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False

def test_file_upload_simulation():
    """Simulate a file upload scenario"""
    print("🧪 Testing file upload simulation...")
    
    try:
        # Create sample student data
        student_data = [
            {
                'studentId': 'TEST-001',
                'studentName': 'Test Student 1',
                'yearLevel': '1',
                'course': 'TEST'
            },
            {
                'studentId': 'TEST-002', 
                'studentName': 'Test Student 2',
                'yearLevel': '2',
                'course': 'TEST'
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            classes_db = os.path.join(temp_dir, 'classes.db')
            attendance_db = os.path.join(temp_dir, 'attendance.db')
            
            # Create databases
            from database.models import create_all_tables, create_optimized_classes_schema
            from config.config import Config
            
            # Temporarily override the database path for testing
            original_db_path = Config.DATABASE_PATH
            Config.DATABASE_PATH = attendance_db
            
            try:
                create_all_tables()
                create_optimized_classes_schema(classes_db)
            finally:
                # Restore original path
                Config.DATABASE_PATH = original_db_path
            
            # Test import
            from database.class_table_manager import OptimizedClassManager
            manager = OptimizedClassManager(classes_db, attendance_db)
            
            class_id = manager.import_from_excel_data(
                class_name="Test Class",
                professor_name="Test Professor",
                student_data=student_data
            )
            
            if class_id:
                print(f"✅ File upload simulation successful, class_id: {class_id}")
                return True
            else:
                print("❌ File upload simulation failed")
                return False
                
    except Exception as e:
        print(f"❌ File upload simulation error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🔬 Running Build Verification Tests")
    print("=" * 50)
    
    tests = [
        ("Path Resolution", test_path_resolution),
        ("Database Creation", test_database_creation),
        ("Class Manager", test_class_manager),
        ("File Upload Simulation", test_file_upload_simulation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📝 {test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 Test Results:")
    print("=" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Build should work correctly.")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Review issues before building.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
