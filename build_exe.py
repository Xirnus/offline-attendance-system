"""
Build script to create a standalone executable for the Offline Attendance System

This script uses PyInstaller to package the Flask application and all dependencies
into a single executable file that can be distributed to other computers.

Usage:
    python build_exe.py

Output:
    - Creates dist/attendance_system.exe (standalone executable)
    - Includes all Python dependencies and data files
    - Bundles templates, static files, and database
"""

import PyInstaller.__main__
import os
import shutil

def build_executable():
    """Build the standalone executable using PyInstaller"""
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # PyInstaller arguments for GUI launcher
    args = [
        'gui_launcher.py',                  # Main GUI script
        '--name=AttendanceSystem',          # Output name
        '--onefile',                        # Single executable
        '--windowed',                       # No console window (GUI only)
        '--add-data=templates;templates',   # Include templates
        '--add-data=static;static',         # Include static files
        '--add-data=database/db;database/db',  # Include database files
        '--add-data=.flaskenv;.',           # Include Flask config
        '--add-data=app.py;.',              # Include main Flask app
        '--add-data=api;api',               # Include API modules
        '--add-data=config;config',         # Include config modules
        '--add-data=database;database',     # Include database modules
        '--add-data=services;services',     # Include services modules
        '--add-data=utils;utils',           # Include utils modules
        '--hidden-import=sqlalchemy.dialects.sqlite',  # SQLite support
        '--hidden-import=openpyxl',         # Excel support
        '--hidden-import=reportlab',        # PDF support
        '--hidden-import=qrcode',           # QR code support
        '--hidden-import=tkinter',          # GUI support
        '--hidden-import=flask',            # Flask framework
        '--clean',                          # Clean cache
        '--noconfirm',                      # Overwrite without asking
        '--icon=static/images/ccs.png',     # App icon (if available)
    ]
    
    print("Building standalone executable...")
    print("This may take several minutes...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build completed successfully!")
        print("📁 Executable location: dist/AttendanceSystem.exe")
        print("📦 File size: ~80-150MB (includes Python runtime + GUI)")
        print("\n🚀 Distribution Instructions:")
        print("1. Copy AttendanceSystem.exe to target computer")
        print("2. Double-click to run (GUI will open)")
        print("3. Use GUI controls to start/stop server")
        print("4. Click 'Open in Browser' to access the web interface")
        print("5. Server runs on http://localhost:5000")
        
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_executable()
