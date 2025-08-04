"""
System Health Monitor and User Experience Manager

This module provides system health monitoring, progress indicators,
and user-friendly status reporting for the attendance system.

Features:
- Real-time system health monitoring
- Progress tracking for long operations
- User-friendly status messages
- Performance metrics dashboard
- Backup and restore functionality
- System diagnostics and troubleshooting

Improves user experience with better feedback and monitoring.
"""

import os
import time
import json
import shutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from config.config import Config
from utils.logging_system import get_logger, monitor_performance

class SystemStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"

@dataclass
class HealthMetric:
    name: str
    status: SystemStatus
    value: float
    threshold: float
    message: str
    timestamp: datetime
    details: Dict[str, Any] = None

@dataclass
class ProgressInfo:
    operation_id: str
    operation_name: str
    current_step: int
    total_steps: int
    status: str
    message: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    details: Dict[str, Any] = None

class ProgressTracker:
    """Track progress of long-running operations"""
    
    def __init__(self):
        self.operations = {}
        self.lock = threading.Lock()
        self.logger = get_logger()
    
    def start_operation(self, operation_id: str, operation_name: str, 
                       total_steps: int) -> ProgressInfo:
        """Start tracking a new operation"""
        progress = ProgressInfo(
            operation_id=operation_id,
            operation_name=operation_name,
            current_step=0,
            total_steps=total_steps,
            status="running",
            message="Starting operation...",
            start_time=datetime.now()
        )
        
        with self.lock:
            self.operations[operation_id] = progress
        
        self.logger.log_event('info', f"Started operation: {operation_name}",
                            component='progress', action='start',
                            operation_id=operation_id, total_steps=total_steps)
        
        return progress
    
    def update_progress(self, operation_id: str, current_step: int, 
                       message: str = None, details: Dict[str, Any] = None):
        """Update operation progress"""
        with self.lock:
            if operation_id in self.operations:
                progress = self.operations[operation_id]
                progress.current_step = current_step
                if message:
                    progress.message = message
                if details:
                    progress.details = details
                
                # Estimate completion time
                if current_step > 0:
                    elapsed = datetime.now() - progress.start_time
                    rate = current_step / elapsed.total_seconds()
                    remaining_steps = progress.total_steps - current_step
                    remaining_time = remaining_steps / rate if rate > 0 else 0
                    progress.estimated_completion = datetime.now() + timedelta(seconds=remaining_time)
        
        self.logger.log_event('debug', f"Progress update: {current_step}",
                            component='progress', action='update',
                            operation_id=operation_id, current_step=current_step)
    
    def complete_operation(self, operation_id: str, success: bool = True, 
                         message: str = None):
        """Mark operation as completed"""
        with self.lock:
            if operation_id in self.operations:
                progress = self.operations[operation_id]
                progress.status = "completed" if success else "failed"
                progress.current_step = progress.total_steps
                progress.estimated_completion = datetime.now()
                if message:
                    progress.message = message
        
        self.logger.log_event('info', f"Operation {'completed' if success else 'failed'}",
                            component='progress', action='complete',
                            operation_id=operation_id, success=success)
    
    def get_progress(self, operation_id: str) -> Optional[ProgressInfo]:
        """Get current progress for an operation"""
        with self.lock:
            return self.operations.get(operation_id)
    
    def get_all_operations(self) -> List[ProgressInfo]:
        """Get all tracked operations"""
        with self.lock:
            return list(self.operations.values())
    
    def cleanup_old_operations(self, max_age_hours: int = 24):
        """Remove old completed operations"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with self.lock:
            to_remove = []
            for op_id, progress in self.operations.items():
                if (progress.status in ["completed", "failed"] and 
                    progress.start_time < cutoff_time):
                    to_remove.append(op_id)
            
            for op_id in to_remove:
                del self.operations[op_id]

class SystemHealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self):
        self.logger = get_logger()
        self.metrics = {}
        self.lock = threading.Lock()
        self.monitoring_active = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval_seconds: int = 30):
        """Start continuous health monitoring"""
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        
        self.logger.log_event('info', "Health monitoring started",
                            component='health', action='start')
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        self.logger.log_event('info', "Health monitoring stopped",
                            component='health', action='stop')
    
    def _monitoring_loop(self, interval_seconds: int):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                time.sleep(interval_seconds)
            except Exception as e:
                self.logger.log_error(e, "health_monitoring_loop")
                time.sleep(interval_seconds)
    
    def _collect_metrics(self):
        """Collect system health metrics"""
        metrics = []
        
        # Database health
        metrics.append(self._check_database_health())
        
        # Disk space
        metrics.append(self._check_disk_space())
        
        # Memory usage (basic check)
        metrics.append(self._check_memory_usage())
        
        # File system health
        metrics.append(self._check_file_system())
        
        # Update stored metrics
        with self.lock:
            for metric in metrics:
                self.metrics[metric.name] = metric
    
    def _check_database_health(self) -> HealthMetric:
        """Check database connectivity and performance"""
        try:
            from database.performance_manager import get_optimized_db
            
            start_time = time.time()
            db = get_optimized_db()
            
            # Test query
            result = db.execute_query("SELECT COUNT(*) FROM sqlite_master", fetch='one')
            response_time = (time.time() - start_time) * 1000
            
            # Get database file size
            db_size = os.path.getsize(Config.DATABASE_PATH) / (1024 * 1024)  # MB
            
            status = SystemStatus.HEALTHY
            message = f"Database responsive ({response_time:.1f}ms, {db_size:.1f}MB)"
            
            if response_time > 1000:  # > 1 second
                status = SystemStatus.WARNING
                message = f"Database slow ({response_time:.1f}ms)"
            elif response_time > 5000:  # > 5 seconds
                status = SystemStatus.ERROR
                message = f"Database very slow ({response_time:.1f}ms)"
            
            return HealthMetric(
                name="database",
                status=status,
                value=response_time,
                threshold=1000,
                message=message,
                timestamp=datetime.now(),
                details={"size_mb": db_size, "response_time_ms": response_time}
            )
            
        except Exception as e:
            return HealthMetric(
                name="database",
                status=SystemStatus.ERROR,
                value=0,
                threshold=1000,
                message=f"Database error: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def _check_disk_space(self) -> HealthMetric:
        """Check available disk space"""
        try:
            db_dir = os.path.dirname(Config.DATABASE_PATH)
            stat = shutil.disk_usage(db_dir)
            
            free_gb = stat.free / (1024 ** 3)
            total_gb = stat.total / (1024 ** 3)
            used_percent = ((stat.total - stat.free) / stat.total) * 100
            
            status = SystemStatus.HEALTHY
            message = f"Disk space: {free_gb:.1f}GB free ({used_percent:.1f}% used)"
            
            if used_percent > 90:
                status = SystemStatus.ERROR
                message = f"Disk space critical: {free_gb:.1f}GB free"
            elif used_percent > 80:
                status = SystemStatus.WARNING
                message = f"Disk space low: {free_gb:.1f}GB free"
            
            return HealthMetric(
                name="disk_space",
                status=status,
                value=free_gb,
                threshold=1.0,  # 1GB threshold
                message=message,
                timestamp=datetime.now(),
                details={
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "used_percent": used_percent
                }
            )
            
        except Exception as e:
            return HealthMetric(
                name="disk_space",
                status=SystemStatus.ERROR,
                value=0,
                threshold=1.0,
                message=f"Disk check error: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def _check_memory_usage(self) -> HealthMetric:
        """Check basic memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            status = SystemStatus.HEALTHY
            message = f"Memory: {memory.percent:.1f}% used"
            
            if memory.percent > 90:
                status = SystemStatus.ERROR
                message = f"Memory critical: {memory.percent:.1f}% used"
            elif memory.percent > 80:
                status = SystemStatus.WARNING
                message = f"Memory high: {memory.percent:.1f}% used"
            
            return HealthMetric(
                name="memory",
                status=status,
                value=memory.percent,
                threshold=80.0,
                message=message,
                timestamp=datetime.now(),
                details={
                    "used_percent": memory.percent,
                    "available_mb": memory.available / (1024 ** 2)
                }
            )
            
        except ImportError:
            # psutil not available, return basic metric
            return HealthMetric(
                name="memory",
                status=SystemStatus.HEALTHY,
                value=0,
                threshold=80.0,
                message="Memory monitoring unavailable (install psutil)",
                timestamp=datetime.now(),
                details={"note": "psutil package required for memory monitoring"}
            )
        except Exception as e:
            return HealthMetric(
                name="memory",
                status=SystemStatus.ERROR,
                value=0,
                threshold=80.0,
                message=f"Memory check error: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def _check_file_system(self) -> HealthMetric:
        """Check file system health"""
        try:
            required_files = [
                Config.DATABASE_PATH,
                Config.CLASSES_DATABASE_PATH
            ]
            
            missing_files = []
            file_details = {}
            
            for file_path in required_files:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    file_details[os.path.basename(file_path)] = {
                        "size_mb": size / (1024 ** 2),
                        "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    }
                else:
                    missing_files.append(os.path.basename(file_path))
            
            status = SystemStatus.HEALTHY
            message = "All system files present"
            
            if missing_files:
                status = SystemStatus.ERROR
                message = f"Missing files: {', '.join(missing_files)}"
            
            return HealthMetric(
                name="file_system",
                status=status,
                value=len(required_files) - len(missing_files),
                threshold=len(required_files),
                message=message,
                timestamp=datetime.now(),
                details={
                    "files": file_details,
                    "missing": missing_files
                }
            )
            
        except Exception as e:
            return HealthMetric(
                name="file_system",
                status=SystemStatus.ERROR,
                value=0,
                threshold=1,
                message=f"File system check error: {str(e)}",
                timestamp=datetime.now(),
                details={"error": str(e)}
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        with self.lock:
            if not self.metrics:
                return {
                    "overall_status": SystemStatus.WARNING.value,
                    "message": "Health monitoring not started",
                    "metrics": {},
                    "last_check": None
                }
            
            # Determine overall status
            error_count = sum(1 for m in self.metrics.values() if m.status == SystemStatus.ERROR)
            warning_count = sum(1 for m in self.metrics.values() if m.status == SystemStatus.WARNING)
            
            if error_count > 0:
                overall_status = SystemStatus.ERROR
                message = f"{error_count} critical issue(s) detected"
            elif warning_count > 0:
                overall_status = SystemStatus.WARNING
                message = f"{warning_count} warning(s) detected"
            else:
                overall_status = SystemStatus.HEALTHY
                message = "All systems operational"
            
            # Convert metrics to dict
            metrics_dict = {}
            last_check = None
            
            for name, metric in self.metrics.items():
                metrics_dict[name] = {
                    "status": metric.status.value,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "message": metric.message,
                    "timestamp": metric.timestamp.isoformat(),
                    "details": metric.details
                }
                
                if last_check is None or metric.timestamp > last_check:
                    last_check = metric.timestamp
            
            return {
                "overall_status": overall_status.value,
                "message": message,
                "metrics": metrics_dict,
                "last_check": last_check.isoformat() if last_check else None,
                "error_count": error_count,
                "warning_count": warning_count
            }

class BackupManager:
    """Manage database backups and restoration"""
    
    def __init__(self):
        self.logger = get_logger()
        self.backup_dir = os.path.join(Config.PROJECT_ROOT, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    @monitor_performance("backup_create")
    def create_backup(self, progress_callback: Callable = None) -> Dict[str, Any]:
        """Create system backup with progress tracking"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            os.makedirs(backup_path, exist_ok=True)
            
            files_to_backup = [
                (Config.DATABASE_PATH, 'attendance.db'),
                (Config.CLASSES_DATABASE_PATH, 'classes.db')
            ]
            
            total_size = sum(os.path.getsize(src) for src, _ in files_to_backup if os.path.exists(src))
            copied_size = 0
            
            for i, (src_path, dst_name) in enumerate(files_to_backup):
                if progress_callback:
                    progress_callback(i, len(files_to_backup), f"Backing up {dst_name}...")
                
                if os.path.exists(src_path):
                    dst_path = os.path.join(backup_path, dst_name)
                    shutil.copy2(src_path, dst_path)
                    copied_size += os.path.getsize(src_path)
            
            # Create backup metadata
            metadata = {
                'created_at': datetime.now().isoformat(),
                'files': [dst for _, dst in files_to_backup],
                'total_size': total_size,
                'version': 'v2.0'
            }
            
            metadata_path = os.path.join(backup_path, 'backup_info.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            if progress_callback:
                progress_callback(len(files_to_backup), len(files_to_backup), "Backup completed")
            
            self.logger.log_event('info', f"Backup created: {backup_name}",
                                component='backup', action='create',
                                backup_path=backup_path, size_mb=total_size/(1024**2))
            
            return {
                'success': True,
                'backup_name': backup_name,
                'backup_path': backup_path,
                'size_mb': total_size / (1024 ** 2)
            }
            
        except Exception as e:
            self.logger.log_error(e, "backup_create")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        try:
            for backup_name in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                if os.path.isdir(backup_path):
                    metadata_path = os.path.join(backup_path, 'backup_info.json')
                    
                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        
                        backup_info = {
                            'name': backup_name,
                            'path': backup_path,
                            'created_at': metadata.get('created_at'),
                            'size_mb': metadata.get('total_size', 0) / (1024 ** 2),
                            'files': metadata.get('files', []),
                            'version': metadata.get('version', 'unknown')
                        }
                        
                        backups.append(backup_info)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            self.logger.log_error(e, "backup_list")
        
        return backups
    
    @monitor_performance("backup_restore")
    def restore_backup(self, backup_name: str, progress_callback: Callable = None) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if not os.path.exists(backup_path):
                return {'success': False, 'error': 'Backup not found'}
            
            # Load backup metadata
            metadata_path = os.path.join(backup_path, 'backup_info.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                files_to_restore = metadata.get('files', [])
            else:
                # Fallback: detect files
                files_to_restore = [f for f in os.listdir(backup_path) if f.endswith('.db')]
            
            # Create current backup before restore
            current_backup = self.create_backup()
            
            # Restore files
            file_mapping = {
                'attendance.db': Config.DATABASE_PATH,
                'classes.db': Config.CLASSES_DATABASE_PATH
            }
            
            for i, filename in enumerate(files_to_restore):
                if progress_callback:
                    progress_callback(i, len(files_to_restore), f"Restoring {filename}...")
                
                src_path = os.path.join(backup_path, filename)
                dst_path = file_mapping.get(filename)
                
                if dst_path and os.path.exists(src_path):
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
            
            if progress_callback:
                progress_callback(len(files_to_restore), len(files_to_restore), "Restore completed")
            
            self.logger.log_event('info', f"Backup restored: {backup_name}",
                                component='backup', action='restore',
                                backup_name=backup_name)
            
            return {
                'success': True,
                'restored_backup': backup_name,
                'current_backup': current_backup.get('backup_name')
            }
            
        except Exception as e:
            self.logger.log_error(e, "backup_restore")
            return {
                'success': False,
                'error': str(e)
            }

# Global instances
_progress_tracker = None
_health_monitor = None
_backup_manager = None

def get_progress_tracker() -> ProgressTracker:
    """Get global progress tracker instance"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker

def get_health_monitor() -> SystemHealthMonitor:
    """Get global health monitor instance"""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = SystemHealthMonitor()
    return _health_monitor

def get_backup_manager() -> BackupManager:
    """Get global backup manager instance"""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager
