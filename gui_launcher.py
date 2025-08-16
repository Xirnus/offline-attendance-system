"""
GUI Launcher for Offline Attendance System

This application provides a simple GUI to start, stop, and monitor the
Flask-based attendance system. It includes:
- Start/Stop/Restart server controls
- Real-time log display
- System status monitoring
- Quick access to web interface
- Network detection for hotspot access
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import webbrowser
import sys
import os
import time
import shutil
import json
from datetime import datetime
import io
import contextlib

class AttendanceSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Attendance System - Control Panel 1.2.0 (Data-Safe)")
        self.root.geometry("800x700")  # Increased height to accommodate backup section
        self.root.resizable(True, True)
        
        # Server process and monitoring
        self.flask_app = None
        self.server_thread = None
        self.is_running = False
        self.log_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # Network detection
        self.server_url = "http://localhost:5000"  # Default fallback
        self.network_ips = []
        
        # Create GUI components
        self.setup_gui()
        
        # Start log monitoring
        self.start_log_monitoring()
        
        # Detect network interfaces
        self.detect_network_interfaces()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def detect_network_interfaces(self):
        """Detect available network interfaces for server access"""
        try:
            # Try to import network utilities
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from utils.network import get_all_network_interfaces
            
            self.network_ips = get_all_network_interfaces()
            if self.network_ips:
                primary_ip = self.network_ips[0]
                self.server_url = f"http://{primary_ip}:5000"
                self.log_message(f"Detected network IP: {primary_ip}")
                
                # Update URL label
                if hasattr(self, 'url_label'):
                    self.url_label.config(text=f"Primary URL: {self.server_url}")
                
                # Log additional IPs
                if len(self.network_ips) > 1:
                    self.log_message(f"Additional IPs available: {', '.join(self.network_ips[1:3])}")
            else:
                self.log_message("Using localhost - network detection failed", "WARNING")
                
        except Exception as e:
            self.log_message(f"Network detection error: {str(e)}", "WARNING")
            self.log_message("Using localhost as fallback", "INFO")
    
    def update_network_display(self):
        """Update the network URLs display"""
        try:
            if hasattr(self, 'url_list_text'):
                self.url_list_text.delete(1.0, tk.END)
                
                if self.network_ips:
                    # Show primary URL
                    primary_url = f"http://{self.network_ips[0]}:5000"
                    self.url_list_text.insert(tk.END, f"Primary (Hotspot/Network): {primary_url}\n")
                    
                    # Show additional URLs
                    for i, ip in enumerate(self.network_ips[1:4], 1):  # Show up to 3 additional
                        url = f"http://{ip}:5000"
                        self.url_list_text.insert(tk.END, f"Alternative {i}: {url}\n")
                    
                    # Add usage instructions
                    self.url_list_text.insert(tk.END, "\nFor mobile access:\n")
                    self.url_list_text.insert(tk.END, "1. Enable hotspot on this laptop\n")
                    self.url_list_text.insert(tk.END, "2. Connect phone to hotspot\n")
                    self.url_list_text.insert(tk.END, f"3. Open {primary_url} on phone")
                else:
                    self.url_list_text.insert(tk.END, "Network detection failed - using localhost only\n")
                    self.url_list_text.insert(tk.END, "http://localhost:5000")
                
                # Make read-only
                self.url_list_text.config(state=tk.DISABLED)
        except Exception as e:
            self.log_message(f"Error updating network display: {str(e)}", "ERROR")
    
    def copy_primary_url(self):
        """Copy primary URL to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.server_url)
            self.root.update()  # Required for clipboard to work
            self.log_message(f"Copied to clipboard: {self.server_url}")
        except Exception as e:
            self.log_message(f"Failed to copy URL: {str(e)}", "ERROR")
    
    def setup_gui(self):
        """Create and arrange GUI components"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Updated to row 4 for log frame
        
        # Title
        title_label = ttk.Label(main_frame, text="Offline Attendance System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Control Panel Frame
        control_frame = ttk.LabelFrame(main_frame, text="Server Control", padding="10")
        control_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Server status
        self.status_label = ttk.Label(control_frame, text="Status: Stopped", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Control buttons
        self.start_btn = ttk.Button(control_frame, text="Start Server", 
                                   command=self.start_server, width=15)
        self.start_btn.grid(row=1, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Server", 
                                  command=self.stop_server, width=15, state="disabled")
        self.stop_btn.grid(row=1, column=1, padx=5)
        
        self.restart_btn = ttk.Button(control_frame, text="Restart Server", 
                                     command=self.restart_server, width=15, state="disabled")
        self.restart_btn.grid(row=1, column=2, padx=(5, 0))
        
        # Quick access frame
        access_frame = ttk.LabelFrame(main_frame, text="Quick Access", padding="10")
        access_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        access_frame.columnconfigure(1, weight=1)
        
        # Browser button
        self.open_browser_btn = ttk.Button(access_frame, text="Open in Browser", 
                                          command=self.open_browser, width=20, state="disabled")
        self.open_browser_btn.grid(row=0, column=0, padx=(0, 10))
        
        # Primary URL label
        self.url_label = ttk.Label(access_frame, text="Primary URL: http://localhost:5000")
        self.url_label.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Network info frame
        network_frame = ttk.Frame(access_frame)
        network_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        network_frame.columnconfigure(1, weight=1)
        
        # Network URLs label
        self.network_label = ttk.Label(network_frame, text="Network URLs:", font=("Arial", 9, "bold"))
        self.network_label.grid(row=0, column=0, sticky=tk.W)
        
        # URL list text (small)
        self.url_list_text = tk.Text(network_frame, height=3, width=60, 
                                    font=("Consolas", 8), wrap=tk.WORD)
        self.url_list_text.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(2, 0))
        
        # URL list scrollbar
        url_scrollbar = ttk.Scrollbar(network_frame, orient="vertical", command=self.url_list_text.yview)
        url_scrollbar.grid(row=1, column=2, sticky=(tk.N, tk.S))
        self.url_list_text.configure(yscrollcommand=url_scrollbar.set)
        
        # Copy URL button
        self.copy_url_btn = ttk.Button(network_frame, text="Copy Primary URL", 
                                      command=self.copy_primary_url, width=20)
        self.copy_url_btn.grid(row=2, column=0, pady=(5, 0))
        
        # Backup Management Frame
        backup_frame = ttk.LabelFrame(main_frame, text="Data Backup", padding="10")
        backup_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Backup buttons
        self.create_backup_btn = ttk.Button(backup_frame, text="Create Backup", 
                                           command=self.create_backup, width=15)
        self.create_backup_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.restore_backup_btn = ttk.Button(backup_frame, text="Restore Backup", 
                                            command=self.restore_backup, width=15)
        self.restore_backup_btn.grid(row=0, column=1, padx=5)
        
        self.open_data_folder_btn = ttk.Button(backup_frame, text="Open Data Folder", 
                                              command=self.open_data_folder, width=15)
        self.open_data_folder_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Backup status label
        self.backup_status_label = ttk.Label(backup_frame, text="Ready to backup", 
                                            font=("Arial", 9), foreground="gray")
        self.backup_status_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        # Log frame (moved down to accommodate backup frame)
        log_frame = ttk.LabelFrame(main_frame, text="Server Logs", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Update weight for new log frame position
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=70,
                                                 font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.clear_logs_btn = ttk.Button(log_controls, text="Clear Logs", 
                                        command=self.clear_logs, width=15)
        self.clear_logs_btn.grid(row=0, column=0)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_cb = ttk.Checkbutton(log_controls, text="Auto-scroll", 
                                             variable=self.auto_scroll_var)
        self.auto_scroll_cb.grid(row=0, column=1, padx=(10, 0))
    
    def log_message(self, message, level="INFO"):
        """Add a message to the log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}\n"
        
        self.log_queue.put(formatted_message)
    
    def process_log_queue(self):
        """Process messages in the log queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message)
                
                # Auto-scroll if enabled
                if self.auto_scroll_var.get():
                    self.log_text.see(tk.END)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)
    
    def start_log_monitoring(self):
        """Start the log monitoring process"""
        self.process_log_queue()
        self.log_message("GUI initialized successfully")
    
    def start_server(self):
        """Start the Flask server in a separate thread"""
        if self.is_running:
            self.log_message("Server is already running", "WARNING")
            return
        
        try:
            self.log_message("Starting Flask server...")
            
            # Perform user data migration before starting server
            try:
                from database.user_data_migration import migrate_user_data, get_migration_info
                migrate_user_data()
                
                # Log user data location
                migration_info = get_migration_info()
                self.log_message(f"📁 User data: {migration_info['user_data_dir']}")
                if migration_info['exists']['attendance'] or migration_info['exists']['classes']:
                    self.log_message("✓ Found existing databases")
                else:
                    self.log_message("ℹ New installation - databases will be created")
            except Exception as e:
                self.log_message(f"Migration warning: {str(e)}", "WARNING")
            
            self.stop_event.clear()
            
            # Re-detect network interfaces before starting
            self.detect_network_interfaces()
            self.update_network_display()
            
            # Start the server in a separate thread
            self.server_thread = threading.Thread(target=self.run_flask_server, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            self.update_ui_state()
            self.log_message("Server started successfully")
            self.log_message(f"Primary access URL: {self.server_url}")
            
            # Wait a moment then try to verify server is responding
            self.root.after(3000, self.verify_server_status)
            
        except Exception as e:
            self.log_message(f"Failed to start server: {str(e)}", "ERROR")
            self.is_running = False
            self.update_ui_state()
    
    def run_flask_server(self):
        """Run the Flask server in this thread"""
        try:
            # Redirect stdout to capture Flask logs
            log_capture = io.StringIO()
            
            # Import and run the Flask app
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # Import the Flask app
            from app import app
            
            self.log_queue.put("[SERVER] Flask application imported successfully\n")
            
            # Configure Flask for production-like serving
            app.config['ENV'] = 'production'
            app.config['DEBUG'] = False
            
            # Run the Flask server
            self.log_queue.put("[SERVER] Starting Flask server on http://localhost:5000\n")
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
            
        except Exception as e:
            self.log_queue.put(f"[ERROR] Flask server error: {str(e)}\n")
            # Signal that server has stopped
            self.is_running = False
            self.root.after(100, self.update_ui_state)
    
    def stop_server(self):
        """Stop the Flask server"""
        if not self.is_running:
            self.log_message("Server is not running", "WARNING")
            return
        
        try:
            self.log_message("Stopping server...")
            
            # Signal the server to stop
            self.stop_event.set()
            self.is_running = False
            
            # Try to shutdown Flask gracefully
            try:
                import requests
                requests.post('http://localhost:5000/shutdown', timeout=2)
            except:
                pass  # Shutdown endpoint might not exist, that's ok
            
            self.update_ui_state()
            self.log_message("Server stopped successfully")
            
        except Exception as e:
            self.log_message(f"Error stopping server: {str(e)}", "ERROR")
    
    def restart_server(self):
        """Restart the Flask server"""
        self.log_message("Restarting server...")
        self.stop_server()
        # Wait a moment before starting
        self.root.after(1000, self.start_server)
    
    def verify_server_status(self):
        """Verify that the server is responding"""
        try:
            # Re-detect network interfaces in case they changed
            self.detect_network_interfaces()
            self.update_network_display()
            
            import urllib.request
            response = urllib.request.urlopen(self.server_url, timeout=5)
            if response.getcode() == 200:
                self.log_message(f"✓ Server is responding on {self.server_url}")
                if self.network_ips:
                    self.log_message(f"✓ Available on {len(self.network_ips)} network interface(s)")
            else:
                self.log_message(f"Server responded with code: {response.getcode()}", "WARNING")
        except Exception as e:
            self.log_message(f"Server may not be fully ready yet: {str(e)}", "WARNING")
    
    def open_browser(self):
        """Open the web interface in default browser"""
        if not self.is_running:
            messagebox.showwarning("Server Not Running", 
                                 "Please start the server first before opening the browser.")
            return
        
        try:
            # Use the detected server URL instead of localhost
            webbrowser.open(self.server_url)
            self.log_message(f"Opening browser to {self.server_url}")
        except Exception as e:
            self.log_message(f"Failed to open browser: {str(e)}", "ERROR")
            self.log_message("Opened web interface in browser")
        except Exception as e:
            self.log_message(f"Failed to open browser: {str(e)}", "ERROR")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Logs cleared")
    
    def update_ui_state(self):
        """Update UI elements based on server state"""
        if self.is_running:
            self.status_label.config(text="Status: Running", foreground="green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.restart_btn.config(state="normal")
            self.open_browser_btn.config(state="normal")
        else:
            self.status_label.config(text="Status: Stopped", foreground="red")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.restart_btn.config(state="disabled")
            self.open_browser_btn.config(state="disabled")
    
    def copy_url_to_clipboard(self, url):
        """Copy a URL to the clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)
            self.root.update()  # Keep clipboard after app closes
            self.log_message(f"✓ Copied to clipboard: {url}")
        except Exception as e:
            self.log_message(f"Failed to copy URL: {str(e)}", "ERROR")
    
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            result = messagebox.askyesno("Confirm Exit", 
                                       "Server is still running. Stop server and exit?")
            if result:
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def create_backup(self):
        """Create a manual backup of databases"""
        try:
            self.backup_status_label.config(text="Creating backup...", foreground="blue")
            self.root.update()
            
            from database.user_data_migration import UserDataMigration
            migration = UserDataMigration()
            
            # Check if databases exist
            from config.config import Config
            if not os.path.exists(Config.DATABASE_PATH) and not os.path.exists(Config.CLASSES_DATABASE_PATH):
                self.backup_status_label.config(text="No databases found to backup", foreground="orange")
                self.log_message("No databases found to backup", "WARNING")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"manual_backup_{timestamp}"
            backup_path = os.path.join(migration.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            backed_up_files = []
            total_size = 0
            
            # Backup attendance database
            if os.path.exists(Config.DATABASE_PATH):
                filename = os.path.basename(Config.DATABASE_PATH)
                backup_file = os.path.join(backup_path, filename)
                shutil.copy2(Config.DATABASE_PATH, backup_file)
                backed_up_files.append(filename)
                total_size += os.path.getsize(backup_file)
            
            # Backup classes database
            if os.path.exists(Config.CLASSES_DATABASE_PATH):
                filename = os.path.basename(Config.CLASSES_DATABASE_PATH)
                backup_file = os.path.join(backup_path, filename)
                shutil.copy2(Config.CLASSES_DATABASE_PATH, backup_file)
                backed_up_files.append(filename)
                total_size += os.path.getsize(backup_file)
            
            if backed_up_files:
                # Create backup info
                backup_info = {
                    "timestamp": timestamp,
                    "reason": "manual_gui_backup",
                    "source_dir": Config.DATABASE_DIR,
                    "backed_up_files": backed_up_files,
                    "total_size": total_size,
                    "backup_size_mb": round(total_size / (1024 * 1024), 2)
                }
                
                info_file = os.path.join(backup_path, "backup_info.json")
                with open(info_file, 'w') as f:
                    json.dump(backup_info, f, indent=2)
                
                self.backup_status_label.config(text=f"✓ Backup created: {backup_name}", foreground="green")
                self.log_message(f"✓ Backup created successfully: {backup_name}")
                self.log_message(f"📁 Location: {backup_path}")
                self.log_message(f"📊 Size: {backup_info['backup_size_mb']} MB")
            else:
                self.backup_status_label.config(text="No files backed up", foreground="orange")
                self.log_message("No database files found to backup", "WARNING")
                
        except Exception as e:
            self.backup_status_label.config(text="Backup failed", foreground="red")
            self.log_message(f"❌ Backup failed: {str(e)}", "ERROR")
    
    def restore_backup(self):
        """Show restore backup dialog"""
        try:
            from database.user_data_migration import UserDataMigration
            migration = UserDataMigration()
            
            if not os.path.exists(migration.backup_dir):
                messagebox.showinfo("No Backups", "No backups directory found.")
                return
            
            # Get list of backups
            backup_dirs = []
            for item in os.listdir(migration.backup_dir):
                backup_path = os.path.join(migration.backup_dir, item)
                if os.path.isdir(backup_path):
                    info_file = os.path.join(backup_path, "backup_info.json")
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r') as f:
                                backup_info = json.load(f)
                            backup_info['path'] = backup_path
                            backup_info['name'] = item
                            backup_dirs.append(backup_info)
                        except:
                            pass
            
            if not backup_dirs:
                messagebox.showinfo("No Backups", "No valid backups found.")
                return
            
            # Sort by timestamp (newest first)
            backup_dirs.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Create selection dialog
            self.show_backup_selection_dialog(backup_dirs)
            
        except Exception as e:
            self.log_message(f"❌ Error accessing backups: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to access backups: {str(e)}")
    
    def show_backup_selection_dialog(self, backup_dirs):
        """Show dialog to select and restore backup"""
        restore_window = tk.Toplevel(self.root)
        restore_window.title("Restore from Backup")
        restore_window.geometry("600x400")
        restore_window.resizable(True, True)
        
        # Make it modal
        restore_window.transient(self.root)
        restore_window.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(restore_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Instructions
        ttk.Label(main_frame, text="Select a backup to restore:", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Warning
        warning_label = ttk.Label(main_frame, 
                                 text="⚠️ Warning: This will overwrite your current databases!", 
                                 foreground="red", font=("Arial", 10))
        warning_label.pack(pady=(0, 10))
        
        # Listbox frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Listbox with scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox
        for backup in backup_dirs:
            timestamp = backup['timestamp']
            reason = backup.get('reason', 'unknown')
            size_mb = backup.get('backup_size_mb', 0)
            files = backup.get('backed_up_files', [])
            
            # Format timestamp for display
            try:
                dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                date_str = timestamp
            
            display_text = f"{date_str} | {reason} | {size_mb}MB | {', '.join(files)}"
            listbox.insert(tk.END, display_text)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        def restore_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to restore.")
                return
            
            selected_backup = backup_dirs[selection[0]]
            
            # Confirm restore
            result = messagebox.askyesno("Confirm Restore", 
                                       f"Are you sure you want to restore from:\n\n"
                                       f"Date: {selected_backup['timestamp']}\n"
                                       f"Type: {selected_backup.get('reason', 'unknown')}\n"
                                       f"Files: {', '.join(selected_backup.get('backed_up_files', []))}\n\n"
                                       f"This will overwrite your current databases!")
            
            if result:
                self.perform_restore(selected_backup, restore_window)
        
        def cancel_restore():
            restore_window.destroy()
        
        ttk.Button(button_frame, text="Restore Selected", command=restore_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=cancel_restore).pack(side=tk.LEFT)
    
    def perform_restore(self, selected_backup, restore_window):
        """Perform the actual restore operation"""
        try:
            self.backup_status_label.config(text="Restoring backup...", foreground="blue")
            self.root.update()
            
            # First create a backup of current state
            self.log_message("Creating backup of current state before restore...")
            self.create_backup()
            
            # Restore files
            from config.config import Config
            backup_path = selected_backup['path']
            restored_files = []
            
            for filename in selected_backup.get('backed_up_files', []):
                source_file = os.path.join(backup_path, filename)
                
                if filename == 'attendance.db':
                    dest_file = Config.DATABASE_PATH
                elif filename == 'classes.db':
                    dest_file = Config.CLASSES_DATABASE_PATH
                else:
                    continue
                
                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                    restored_files.append(filename)
                    self.log_message(f"✓ Restored: {filename}")
            
            if restored_files:
                self.backup_status_label.config(text="✓ Restore completed successfully", foreground="green")
                self.log_message(f"✅ Restore completed! Files: {', '.join(restored_files)}")
                self.log_message("🔄 Please restart the server to use restored data")
                
                # Show success message
                messagebox.showinfo("Restore Complete", 
                                  f"Successfully restored {len(restored_files)} database file(s).\n\n"
                                  f"Please restart the server to use the restored data.")
            else:
                self.backup_status_label.config(text="No files were restored", foreground="orange")
                self.log_message("❌ No files were restored")
                messagebox.showwarning("Restore Warning", "No files were restored.")
            
            restore_window.destroy()
            
        except Exception as e:
            self.backup_status_label.config(text="Restore failed", foreground="red")
            self.log_message(f"❌ Restore failed: {str(e)}", "ERROR")
            messagebox.showerror("Restore Error", f"Failed to restore backup:\n{str(e)}")
    
    def open_data_folder(self):
        """Open the data folder in file explorer"""
        try:
            from config.config import Config
            data_path = Config.DATABASE_DIR
            
            if os.path.exists(data_path):
                import subprocess
                subprocess.run(['explorer', data_path], check=True)
                self.log_message(f"📁 Opened data folder: {data_path}")
            else:
                # Create the folder first
                os.makedirs(data_path, exist_ok=True)
                subprocess.run(['explorer', data_path], check=True)
                self.log_message(f"📁 Created and opened data folder: {data_path}")
                
        except Exception as e:
            self.log_message(f"❌ Failed to open data folder: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to open data folder:\n{str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
