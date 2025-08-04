"""
System Management API Routes for Offline Attendance System

This module provides API endpoints for system health monitoring, database management,
backup/restore operations, and progress tracking.

Features:
- Health monitoring endpoints
- Database optimization and maintenance
- Backup and restore operations
- Progress tracking for long operations
- Performance metrics and statistics
- Schema management tools

Used by: Admin interface, system monitoring, maintenance operations
"""

from flask import Blueprint, request, jsonify, send_file
from utils.system_monitor import get_health_monitor, get_progress_tracker, get_backup_manager
from utils.logging_system import get_logger, get_error_handler
from database.schema_manager import SchemaManager
from database.performance_manager import get_optimized_db
import uuid
import os
from datetime import datetime

system_bp = Blueprint('system', __name__)
logger = get_logger()
error_handler = get_error_handler()

@system_bp.route('/api/system/health', methods=['GET'])
def get_system_health():
    """Get current system health status"""
    try:
        health_monitor = get_health_monitor()
        health_status = health_monitor.get_health_status()
        
        logger.log_event('info', "System health check requested",
                        component='system', action='health_check')
        
        return jsonify({
            'status': 'success',
            'data': health_status
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'get_system_health')
        return jsonify(error_response), 500

@system_bp.route('/api/system/health/start', methods=['POST'])
def start_health_monitoring():
    """Start continuous health monitoring"""
    try:
        data = request.get_json() or {}
        interval = data.get('interval_seconds', 30)
        
        health_monitor = get_health_monitor()
        health_monitor.start_monitoring(interval)
        
        logger.log_event('info', f"Health monitoring started with {interval}s interval",
                        component='system', action='start_monitoring',
                        interval_seconds=interval)
        
        return jsonify({
            'status': 'success',
            'message': f'Health monitoring started with {interval} second interval'
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'start_health_monitoring')
        return jsonify(error_response), 500

@system_bp.route('/api/system/health/stop', methods=['POST'])
def stop_health_monitoring():
    """Stop health monitoring"""
    try:
        health_monitor = get_health_monitor()
        health_monitor.stop_monitoring()
        
        logger.log_event('info', "Health monitoring stopped",
                        component='system', action='stop_monitoring')
        
        return jsonify({
            'status': 'success',
            'message': 'Health monitoring stopped'
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'stop_health_monitoring')
        return jsonify(error_response), 500

@system_bp.route('/api/system/database/optimize', methods=['POST'])
def optimize_database():
    """Optimize database performance"""
    try:
        # Start progress tracking
        progress_tracker = get_progress_tracker()
        operation_id = str(uuid.uuid4())
        progress = progress_tracker.start_operation(operation_id, "Database Optimization", 3)
        
        # Step 1: Get database instance
        progress_tracker.update_progress(operation_id, 1, "Initializing database connection...")
        db = get_optimized_db()
        
        # Step 2: Run optimization
        progress_tracker.update_progress(operation_id, 2, "Running VACUUM and ANALYZE...")
        db.optimize_database()
        
        # Step 3: Complete
        progress_tracker.update_progress(operation_id, 3, "Optimization completed")
        progress_tracker.complete_operation(operation_id, True, "Database optimization completed successfully")
        
        logger.log_event('info', "Database optimization completed",
                        component='system', action='database_optimize',
                        operation_id=operation_id)
        
        return jsonify({
            'status': 'success',
            'message': 'Database optimization completed',
            'operation_id': operation_id
        })
        
    except Exception as e:
        if 'operation_id' in locals():
            progress_tracker.complete_operation(operation_id, False, f"Optimization failed: {str(e)}")
        
        error_response = error_handler.handle_error(e, 'optimize_database')
        return jsonify(error_response), 500

@system_bp.route('/api/system/database/schema/validate', methods=['GET'])
def validate_schema():
    """Validate database schema"""
    try:
        schema_manager = SchemaManager()
        validation_results = schema_manager.validate_schema()
        
        logger.log_event('info', "Schema validation performed",
                        component='system', action='schema_validate',
                        issues_found=len(validation_results))
        
        return jsonify({
            'status': 'success',
            'data': validation_results
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'validate_schema')
        return jsonify(error_response), 500

@system_bp.route('/api/system/database/schema/cleanup', methods=['POST'])
def cleanup_schema():
    """Clean up old schema and redundant tables"""
    try:
        data = request.get_json() or {}
        backup = data.get('create_backup', True)
        
        # Start progress tracking
        progress_tracker = get_progress_tracker()
        operation_id = str(uuid.uuid4())
        progress = progress_tracker.start_operation(operation_id, "Schema Cleanup", 4)
        
        schema_manager = SchemaManager()
        
        # Step 1: Validate current schema
        progress_tracker.update_progress(operation_id, 1, "Validating current schema...")
        validation_results = schema_manager.validate_schema()
        
        # Step 2: Create backup if requested
        if backup:
            progress_tracker.update_progress(operation_id, 2, "Creating backup...")
            schema_manager._create_backup()
        else:
            progress_tracker.update_progress(operation_id, 2, "Skipping backup...")
        
        # Step 3: Cleanup
        progress_tracker.update_progress(operation_id, 3, "Cleaning up old schema...")
        success = schema_manager.cleanup_old_schema(backup=False)  # Already backed up
        
        # Step 4: Complete
        progress_tracker.update_progress(operation_id, 4, "Schema cleanup completed")
        progress_tracker.complete_operation(operation_id, success, 
                                          "Schema cleanup completed" if success else "Schema cleanup failed")
        
        logger.log_event('info', f"Schema cleanup {'completed' if success else 'failed'}",
                        component='system', action='schema_cleanup',
                        operation_id=operation_id, success=success)
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Schema cleanup completed' if success else 'Schema cleanup failed',
            'operation_id': operation_id,
            'validation_results': validation_results
        })
        
    except Exception as e:
        if 'operation_id' in locals():
            progress_tracker.complete_operation(operation_id, False, f"Cleanup failed: {str(e)}")
        
        error_response = error_handler.handle_error(e, 'cleanup_schema')
        return jsonify(error_response), 500

@system_bp.route('/api/system/backup/create', methods=['POST'])
def create_backup():
    """Create system backup"""
    try:
        # Start progress tracking
        progress_tracker = get_progress_tracker()
        operation_id = str(uuid.uuid4())
        progress = progress_tracker.start_operation(operation_id, "System Backup", 2)
        
        backup_manager = get_backup_manager()
        
        def progress_callback(current, total, message):
            progress_tracker.update_progress(operation_id, current, message)
        
        # Create backup
        result = backup_manager.create_backup(progress_callback)
        
        # Complete operation
        progress_tracker.complete_operation(operation_id, result['success'], 
                                          result.get('error', 'Backup completed'))
        
        logger.log_event('info', f"Backup creation {'completed' if result['success'] else 'failed'}",
                        component='system', action='backup_create',
                        operation_id=operation_id, success=result['success'])
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Backup created successfully',
                'operation_id': operation_id,
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Backup creation failed'),
                'operation_id': operation_id
            }), 500
        
    except Exception as e:
        if 'operation_id' in locals():
            progress_tracker.complete_operation(operation_id, False, f"Backup failed: {str(e)}")
        
        error_response = error_handler.handle_error(e, 'create_backup')
        return jsonify(error_response), 500

@system_bp.route('/api/system/backup/list', methods=['GET'])
def list_backups():
    """List available backups"""
    try:
        backup_manager = get_backup_manager()
        backups = backup_manager.list_backups()
        
        logger.log_event('info', f"Listed {len(backups)} backups",
                        component='system', action='backup_list')
        
        return jsonify({
            'status': 'success',
            'data': backups
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'list_backups')
        return jsonify(error_response), 500

@system_bp.route('/api/system/backup/restore', methods=['POST'])
def restore_backup():
    """Restore from backup"""
    try:
        data = request.get_json()
        backup_name = data.get('backup_name')
        
        if not backup_name:
            return jsonify({
                'status': 'error',
                'message': 'Backup name is required'
            }), 400
        
        # Start progress tracking
        progress_tracker = get_progress_tracker()
        operation_id = str(uuid.uuid4())
        progress = progress_tracker.start_operation(operation_id, f"Restore from {backup_name}", 2)
        
        backup_manager = get_backup_manager()
        
        def progress_callback(current, total, message):
            progress_tracker.update_progress(operation_id, current, message)
        
        # Restore backup
        result = backup_manager.restore_backup(backup_name, progress_callback)
        
        # Complete operation
        progress_tracker.complete_operation(operation_id, result['success'], 
                                          result.get('error', 'Restore completed'))
        
        logger.log_event('info', f"Backup restore {'completed' if result['success'] else 'failed'}",
                        component='system', action='backup_restore',
                        operation_id=operation_id, backup_name=backup_name,
                        success=result['success'])
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': 'Backup restored successfully',
                'operation_id': operation_id,
                'data': result
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Backup restore failed'),
                'operation_id': operation_id
            }), 500
        
    except Exception as e:
        if 'operation_id' in locals():
            progress_tracker.complete_operation(operation_id, False, f"Restore failed: {str(e)}")
        
        error_response = error_handler.handle_error(e, 'restore_backup')
        return jsonify(error_response), 500

@system_bp.route('/api/system/progress/<operation_id>', methods=['GET'])
def get_operation_progress(operation_id):
    """Get progress of a specific operation"""
    try:
        progress_tracker = get_progress_tracker()
        progress = progress_tracker.get_progress(operation_id)
        
        if progress is None:
            return jsonify({
                'status': 'error',
                'message': 'Operation not found'
            }), 404
        
        # Convert to dict for JSON serialization
        progress_dict = {
            'operation_id': progress.operation_id,
            'operation_name': progress.operation_name,
            'current_step': progress.current_step,
            'total_steps': progress.total_steps,
            'status': progress.status,
            'message': progress.message,
            'start_time': progress.start_time.isoformat(),
            'estimated_completion': progress.estimated_completion.isoformat() if progress.estimated_completion else None,
            'details': progress.details
        }
        
        return jsonify({
            'status': 'success',
            'data': progress_dict
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'get_operation_progress')
        return jsonify(error_response), 500

@system_bp.route('/api/system/progress', methods=['GET'])
def get_all_operations():
    """Get all tracked operations"""
    try:
        progress_tracker = get_progress_tracker()
        operations = progress_tracker.get_all_operations()
        
        # Convert to list of dicts
        operations_list = []
        for progress in operations:
            operations_list.append({
                'operation_id': progress.operation_id,
                'operation_name': progress.operation_name,
                'current_step': progress.current_step,
                'total_steps': progress.total_steps,
                'status': progress.status,
                'message': progress.message,
                'start_time': progress.start_time.isoformat(),
                'estimated_completion': progress.estimated_completion.isoformat() if progress.estimated_completion else None
            })
        
        return jsonify({
            'status': 'success',
            'data': operations_list
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'get_all_operations')
        return jsonify(error_response), 500

@system_bp.route('/api/system/performance', methods=['GET'])
def get_performance_stats():
    """Get system performance statistics"""
    try:
        db = get_optimized_db()
        stats = db.get_performance_stats()
        
        logger.log_event('info', "Performance stats requested",
                        component='system', action='performance_stats')
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'get_performance_stats')
        return jsonify(error_response), 500

@system_bp.route('/api/system/logs/download', methods=['GET'])
def download_logs():
    """Download system logs"""
    try:
        log_type = request.args.get('type', 'system')  # system, errors
        
        from config.config import Config
        log_dir = os.path.join(Config.PROJECT_ROOT, 'logs')
        
        if log_type == 'errors':
            log_file = os.path.join(log_dir, 'errors.log')
        else:
            log_file = os.path.join(log_dir, 'attendance_system.log')
        
        if not os.path.exists(log_file):
            return jsonify({
                'status': 'error',
                'message': 'Log file not found'
            }), 404
        
        logger.log_event('info', f"Log download requested: {log_type}",
                        component='system', action='log_download',
                        log_type=log_type)
        
        return send_file(
            log_file,
            as_attachment=True,
            download_name=f"{log_type}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
    except Exception as e:
        error_response = error_handler.handle_error(e, 'download_logs')
        return jsonify(error_response), 500
