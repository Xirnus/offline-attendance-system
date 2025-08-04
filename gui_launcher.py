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
from datetime import datetime
import io
import contextlib

class AttendanceSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Offline Attendance System - Control Panel 1.0.0")
        self.root.geometry("800x600")
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
        main_frame.rowconfigure(3, weight=1)
        
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
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Server Logs", padding="10")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70,
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

def main():
    """Main entry point"""
    root = tk.Tk()
    app = AttendanceSystemGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
