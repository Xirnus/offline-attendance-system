from flask import Flask

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    
    # Register API routes
    from .routes_new import register_routes
    register_routes(app)
    
    return app