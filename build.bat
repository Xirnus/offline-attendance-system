@echo off
echo Building Offline Attendance System Executable...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages
        pause
        exit /b 1
    )
)

REM Run the build script
echo.
echo Starting build process...
python build_exe.py

echo.
echo Build process completed!
echo Check the 'dist' folder for the executable.
echo.
pause
