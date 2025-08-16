# Database Persistence Guide

## Problem Solved

This system prevents database loss during application updates and exe rebuilds by storing user data in a dedicated folder beside the executable, separate from the bundled application files.

## How It Works

### Database Locations

**For Development (Running from source):**
- Databases stored in: `project_folder/database/db/`
- Location: `d:\Github\offline-attendance-system\database\db\`

**For Production (Built .exe):**
- Databases stored in: `exe_folder/data/`
- Example: `C:\AttendanceSystem\data\` (beside AttendanceSystem.exe)

### Automatic Migration

The system automatically migrates databases from old locations to the new `data` folder when:

1. Running the application for the first time after update
2. Old databases exist in previous locations (bundled folder or user directory)
3. New `data` folder doesn't already have databases

### Backup System

**GUI Backup Controls:**
- **Create Backup**: Manual backup creation with one click
- **Restore Backup**: Select and restore from available backups
- **Open Data Folder**: Quick access to database location

**Automatic Backups:**
- Created before each migration
- Created before restore operations
- Stored in: `exe_folder/backups/`

## File Structure

```
Application Directory (beside .exe):
├── AttendanceSystem.exe
├── data/                       # User databases (persistent)
│   ├── attendance.db          # Main attendance data
│   └── classes.db             # Class and student data
└── backups/                   # Backup storage
    ├── backup_20250816_143022/
    │   ├── attendance.db
    │   ├── classes.db
    │   └── backup_info.json
    └── manual_backup_20250816_144500/
        ├── attendance.db
        ├── classes.db
        └── backup_info.json
```

## Benefits

1. **Update-Safe**: Databases survive application updates
2. **Build-Safe**: Rebuilding the .exe won't overwrite data
3. **Portable**: Can move entire application folder anywhere
4. **Simple**: Data is always beside the executable
5. **Automatic Migration**: Seamless upgrade from old versions
6. **GUI Backup Controls**: Easy backup/restore with buttons
7. **No Permissions Issues**: Uses same directory as executable

## For Users

### GUI Backup Controls

The Control Panel now includes a "Data Backup" section with three buttons:

1. **Create Backup**: Creates a timestamped backup of your databases
2. **Restore Backup**: Shows a list of available backups to restore from
3. **Open Data Folder**: Opens the folder containing your databases

### Manual Data Management

**To find your databases:**
1. Navigate to the folder containing `AttendanceSystem.exe`
2. Look for the `data` folder
3. Your databases (`attendance.db`, `classes.db`) are inside

**To backup manually:**
1. Copy the entire `data` folder to a safe location
2. To restore: replace the `data` folder with your backup

**To move to another computer:**
1. Copy the entire application folder (including `data` and `backups`)
2. Place it anywhere on the new computer
3. Run `AttendanceSystem.exe` - your data will be preserved

## For Developers

### Building the Application

The `AttendanceSystem.spec` file excludes database files from the bundle:

```python
# Excludes database files - they go in /data folder instead
datas=[('templates', 'templates'), ('static', 'static'), ...]  # No database/db
```

### Configuration Changes

The `config/config.py` automatically detects the runtime environment:

```python
if getattr(sys, 'frozen', False):
    # Running as .exe - use data folder beside exe
    PROJECT_ROOT = os.path.dirname(sys.executable)
    DATABASE_DIR = os.path.join(PROJECT_ROOT, 'data')
else:
    # Running from source - use project directory
    DATABASE_DIR = os.path.join(PROJECT_ROOT, 'database', 'db')
```

## Troubleshooting

### If Migration Fails

1. **Check file permissions**: Ensure the user can write to their home directory
2. **Run as administrator**: Try running the application as administrator once
3. **Manual backup**: Use `backup_utility.py backup` to secure your data
4. **Check logs**: Look for migration messages in the application logs

### Locating Your Data

**To find your databases:**
1. Navigate to the folder containing `AttendanceSystem.exe`
2. Look for the `data` folder
3. Your databases (`attendance.db`, `classes.db`) are inside

**To find backups:**
1. In the same folder as `AttendanceSystem.exe`
2. Look for the `backups` folder
3. Each subfolder contains a complete backup with timestamp

### Moving Data Manually

If you need to manually move data between computers:

1. **Export data**: Copy the entire application folder (including `data` and `backups`)
2. **Import data**: Place the folder anywhere on the new computer  
3. **Verify**: Run `AttendanceSystem.exe` and check that your data is present

## Version Compatibility

- **v1.2.0+**: Uses `data` folder beside executable (current approach)
- **v1.1.2**: Used user profile directory (previous fix attempt)
- **v1.1.1 and earlier**: Used application directory (problematic)

The migration system handles upgrades from any previous version automatically.
