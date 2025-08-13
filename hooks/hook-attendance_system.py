"""
PyInstaller hook for Offline Attendance System

This hook ensures that all necessary modules and dependencies are included
when building the executable with PyInstaller.
"""

from PyInstaller.utils.hooks import collect_all

# Collect all openpyxl modules and data
datas, binaries, hiddenimports = collect_all('openpyxl')

# Additional hidden imports
hiddenimports += [
    'sqlite3',
    'csv',
    'io',
    'json',
    'datetime',
    'hashlib',
    'secrets',
    'threading',
    'queue',
    'webbrowser',
    'sys',
    'os',
    'werkzeug.serving',
    'jinja2.ext',
    'markupsafe',
    'tkinter.ttk',
    'tkinter.scrolledtext',
    'tkinter.messagebox',
    'openpyxl.reader.excel',
    'openpyxl.writer.excel',
    'openpyxl.styles',
    'openpyxl.utils',
    'PIL.Image',
    'PIL.ImageTk',
]
