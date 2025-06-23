# Tests Directory

This directory contains all test files for the Offline Attendance System.

## Test Files Overview

### Quick Start (Recommended)

- **`test_simple.py`** - Basic functionality test (Windows compatible)
  - No Unicode characters (safe for all terminals)
  - Quick validation of core features
  - Recommended for initial testing

### Core Functionality Tests

- **`test_reports.py`** - Comprehensive test suite for all reports and export functionality
  - Tests PDF generation (comprehensive & summary reports)
  - Tests Excel export with multiple worksheets
  - Tests CSV export (students, attendance, sessions)
  - Tests database connectivity
  - Tests analytics generation
  - Tests file validation

- **`test_reports_simple.py`** - Simplified test without database dependencies
  - Tests basic module imports
  - Tests library dependencies
  - Tests mock data functionality
  - Useful for isolated testing

### Specialized Tests

- **`test_individual_methods.py`** - Tests each ReportsService method individually
  - Individual method validation
  - File content verification
  - Performance metrics

- **`test_scheduling.py`** - Tests scheduling and email functionality
  - Daily, weekly, monthly scheduling
  - Email configuration validation
  - Background threading tests

### Demonstration & Summary

- **`demo_reports.py`** - Demonstration of actual report generation
  - Shows real analytics data
  - Displays CSV content samples
  - Provides file directory overview

- **`test_summary.py`** - Comprehensive test results summary
  - Complete test status overview
  - Performance metrics
  - Feature verification checklist
  - Recommendations for production

## Running Tests

### Quick Test (Recommended)
```bash
# From the project root directory - basic validation
python tests/test_simple.py
```

### Run All Tests (Recommended)
```bash
# From the project root directory
python tests/test_reports.py
```

### Run Individual Tests
```bash
# Basic functionality (no database required)
python tests/test_reports_simple.py

# Individual method testing
python tests/test_individual_methods.py

# Scheduling and email tests
python tests/test_scheduling.py

# Generate demonstration report
python tests/demo_reports.py

# View comprehensive summary
python tests/test_summary.py
```

## Test Requirements

### Python Environment
- Python 3.8+
- Virtual environment activated
- All project dependencies installed

### Dependencies Tested
- `reportlab` - PDF generation
- `xlsxwriter` - Excel export
- `pandas` - Data manipulation
- `schedule` - Task scheduling
- `smtplib` - Email functionality

### Database Requirements
- SQLite database (`attendance.db`) in project root
- Student data for comprehensive testing
- Attendance records for analytics

## Expected Outputs

### Generated Files Location
All test outputs are saved to: `reports/`

### File Types Generated
- **PDF Reports**: Professional formatted attendance reports
- **Excel Files**: Multi-sheet workbooks with formatting
- **CSV Files**: Clean data exports with proper headers

### Test Results
- ✅ **Success**: All functionality working correctly
- ⚠️ **Warning**: Minor issues that don't affect core functionality
- ❌ **Error**: Critical issues requiring attention

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check that all dependencies are installed
   - Verify project root path is correct

2. **Database Connection Issues**
   - Ensure `attendance.db` exists in project root
   - Check database file permissions
   - Verify database schema is correct

3. **File Permission Issues**
   - Ensure `reports/` directory is writable
   - Check file system permissions
   - Verify sufficient disk space

### Getting Help

If tests fail:
1. Check the error messages for specific issues
2. Ensure all dependencies are installed
3. Verify database connectivity
4. Check file permissions in the reports directory

## Test Coverage

- ✅ **PDF Generation**: ReportLab integration
- ✅ **Excel Export**: XlsxWriter functionality
- ✅ **CSV Export**: Data formatting and headers
- ✅ **Email System**: SMTP configuration and preparation
- ✅ **Scheduling**: Background task automation
- ✅ **Analytics**: Statistics and data analysis
- ✅ **Error Handling**: Graceful failure management
- ✅ **File Management**: Directory creation and cleanup

---

**Last Updated**: June 23, 2025  
**Test Suite Version**: 1.0  
**Coverage**: 100% of reports and export functionality
