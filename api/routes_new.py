"""
Main Routes Module for Offline Attendance System

This module imports and registers all route blueprints for the Flask application.
It serves as the central point for route organization and management.

Route Modules:
- Core Routes: QR generation, scanning, check-in functionality  
- Student Routes: Student CRUD operations and data management
- Session Routes: Attendance session management and profiles
- Analytics Routes: Statistics, reporting, and performance metrics
- Class Routes: Class table management and operations
- Settings Routes: Configuration, data export, and system settings

All routes are organized into logical blueprints for better maintainability
and separation of concerns.
"""

from flask import Blueprint

# Import all route blueprints
from .core_routes import core_bp
from .student_routes import student_bp
from .session_routes import session_bp
from .analytics_routes import analytics_bp
from .class_routes import class_bp
from .settings_routes import settings_bp

# Create main API blueprint
api_bp = Blueprint('api', __name__)

def register_routes(app):
    """
    Register all route blueprints with the Flask application.
    
    Args:
        app: Flask application instance
    """
    # Register individual blueprints
    app.register_blueprint(core_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(class_bp)
    app.register_blueprint(settings_bp)
    
    # Register the main API blueprint (for any remaining routes)
    app.register_blueprint(api_bp)
    
    print("All route blueprints registered successfully")

# Re-export the main blueprint for backward compatibility
__all__ = ['api_bp', 'register_routes']