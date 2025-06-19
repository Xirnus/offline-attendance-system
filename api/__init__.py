from flask import Flask

def create_app():
    """Create and configure Flask app"""
    app = Flask(__name__)
    
    # Register API routes
    from .routes import api_bp
    app.register_blueprint(api_bp)
    
    return app