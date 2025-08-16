# Quick Start: Database Persistence & Backup

## ✅ Problem Solved!

Your attendance data is now **100% safe** from application updates and rebuilds!

## 📁 Where Your Data Lives

**Development Mode** (running from source code):
- `project_folder/database/db/`

**Production Mode** (using .exe file):
- `data/` folder right beside `AttendanceSystem.exe`

## 🎛️ New GUI Features

The Control Panel now has a **"Data Backup"** section with three buttons:

### 🔄 Create Backup
- Click to instantly backup your databases
- Creates timestamped backup in `backups/` folder
- Status shown in the GUI

### 📥 Restore Backup  
- Click to see list of available backups
- Select any backup to restore from
- Automatically creates backup of current data before restoring

### 📂 Open Data Folder
- Click to open your database folder in Windows Explorer
- Quick access to `data/` folder containing your databases

## 🚀 Benefits

✅ **Update-Safe**: Application updates won't delete your data  
✅ **Portable**: Move entire folder anywhere  
✅ **Simple**: Data always beside the .exe file  
✅ **GUI Controls**: Easy backup/restore with buttons  
✅ **Automatic Migration**: Upgrades from old versions seamlessly  

## 📋 File Structure

```
Your Application Folder:
📁 AttendanceSystem/
├── 📄 AttendanceSystem.exe
├── 📁 data/                    ← Your databases are here
│   ├── 📄 attendance.db
│   └── 📄 classes.db
└── 📁 backups/                 ← Your backups are here
    ├── 📁 backup_20250816_143022/
    └── 📁 manual_backup_20250816_144500/
```

## 🔧 Manual Backup (Alternative)

If you prefer manual control:

1. **To backup**: Copy the entire `data` folder
2. **To restore**: Replace `data` folder with your backup  
3. **To move**: Copy entire application folder to new location

## 🆙 Version Upgrade

When you download a new version:

1. **Replace only** the `AttendanceSystem.exe` file
2. **Keep** your `data/` and `backups/` folders
3. Your data will be preserved automatically!

## ⚠️ Important Notes

- Always create a backup before major operations
- The "Restore Backup" button automatically creates a backup before restoring
- You can move the entire application folder anywhere on your computer
- Each backup includes information about when it was created and why

---

**Your data is now completely safe! 🎉**
