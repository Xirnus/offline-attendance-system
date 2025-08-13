"""
Enhanced Build script for Offline Attendance System with PyInstaller fixes

This script creates a standalone executable that works properly on different computers
by fixing the common PyInstaller issues with database paths and schema creation.

Key fixes:
1. Proper path resolution for PyInstaller bundled environment
2. Enhanced hidden imports for all required modules
3. Database schema verification and creation
4. Better error handling and logging

Usage:
    python build_exe_enhanced.py

Output:
    - Creates dist/AttendanceSystem.exe (standalone executable)
    - Includes all dependencies with proper path handling
    - Ensures database schema is created on first run
"""

import PyInstaller.__main__
import os
import shutil
import sys

def clean_previous_builds():
    """Clean previous builds"""
    print("🧹 Cleaning previous builds...")
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Remove spec file if it exists
    if os.path.exists('AttendanceSystem.spec'):
        os.remove('AttendanceSystem.spec')

def build_executable():
    """Build the standalone executable using PyInstaller with enhanced configuration"""
    
    clean_previous_builds()
    
    # Comprehensive PyInstaller arguments
    args = [
        'gui_launcher.py',                  # Main GUI script
        '--name=AttendanceSystem',          # Output name
        '--onefile',                        # Single executable
        '--windowed',                       # No console window (GUI only)
        
        # Data files - include all necessary files
        '--add-data=templates;templates',   
        '--add-data=static;static',         
        '--add-data=database/db;database/db',  
        '--add-data=.flaskenv;.',           
        '--add-data=app.py;.',              
        '--add-data=api;api',               
        '--add-data=config;config',         
        '--add-data=database;database',     
        '--add-data=services;services',     
        '--add-data=utils;utils',           
        
        # Core Python modules
        '--hidden-import=sqlite3',          
        '--hidden-import=csv',              
        '--hidden-import=io',               
        '--hidden-import=json',             
        '--hidden-import=re',               
        '--hidden-import=datetime',         
        '--hidden-import=time',             
        '--hidden-import=hashlib',          
        '--hidden-import=secrets',          
        '--hidden-import=threading',        
        '--hidden-import=queue',            
        '--hidden-import=webbrowser',       
        '--hidden-import=sys',              
        '--hidden-import=os',               
        
        # Database and Excel support
        '--hidden-import=sqlalchemy.dialects.sqlite',  
        '--hidden-import=openpyxl',         
        '--hidden-import=openpyxl.workbook', 
        '--hidden-import=openpyxl.worksheet', 
        '--hidden-import=openpyxl.reader.excel',
        '--hidden-import=openpyxl.writer.excel',
        
        # Flask and web framework
        '--hidden-import=flask',            
        '--hidden-import=werkzeug',         
        '--hidden-import=werkzeug.serving',         
        '--hidden-import=jinja2',           
        '--hidden-import=jinja2.ext',           
        '--hidden-import=markupsafe',           
        
        # GUI support
        '--hidden-import=tkinter',          
        '--hidden-import=tkinter.ttk',          
        '--hidden-import=tkinter.scrolledtext',          
        '--hidden-import=tkinter.messagebox',          
        
        # Additional libraries
        '--hidden-import=reportlab',        
        '--hidden-import=qrcode',           
        '--hidden-import=PIL',              
        '--hidden-import=PIL.Image',              
        
        # Build options
        '--clean',                          
        '--noconfirm',                      
        '--icon=static/images/ccs.png',     
        
        # Debug and optimization
        '--log-level=INFO',
        '--strip',                          # Strip debug symbols
    ]
    
    print("🔨 Building standalone executable with enhanced configuration...")
    print("⏳ This may take several minutes...")
    
    try:
        PyInstaller.__main__.run(args)
        
        # Verify the build
        exe_path = os.path.join('dist', 'AttendanceSystem.exe')
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # Size in MB
            print(f"\n✅ Build completed successfully!")
            print(f"📁 Executable location: {exe_path}")
            print(f"📦 File size: {file_size:.1f} MB")
            
            print(f"\n🚀 Enhanced Distribution Instructions:")
            print(f"1. Copy AttendanceSystem.exe to target computer")
            print(f"2. No installation required - just double-click to run")
            print(f"3. Database will be created automatically on first run")
            print(f"4. Class upload functionality should work properly")
            print(f"5. Server runs on http://localhost:5000")
            print(f"6. GUI will show available network addresses for mobile access")
            
            print(f"\n🔧 Troubleshooting:")
            print(f"- If class upload fails, check Windows Defender/antivirus")
            print(f"- Ensure the executable has write permissions to its directory")
            print(f"- Database files will be created in the same directory as the .exe")
            
            return True
        else:
            print(f"❌ Build failed: Executable not found at {exe_path}")
            return False
            
    except Exception as e:
        print(f"❌ Build failed with error: {e}")
        return False

def test_build():
    """Test if the build would work by checking dependencies"""
    print("🧪 Testing build dependencies...")
    
    required_modules = [
        'flask', 'sqlite3', 'openpyxl', 'tkinter', 
        'qrcode', 'PIL', 'csv', 'json'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} - MISSING")
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {', '.join(missing_modules)}")
        print("Install missing modules before building:")
        print(f"pip install {' '.join(missing_modules)}")
        return False
    else:
        print("\n✅ All dependencies available")
        return True

if __name__ == "__main__":
    print("🏗️  Enhanced Offline Attendance System Builder")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        test_build()
    else:
        if test_build():
            build_executable()
        else:
            print("❌ Cannot build due to missing dependencies")
