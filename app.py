from flask import Flask, render_template, request, jsonify, current_app
from database import init_db, migrate_database
from utils.network import get_all_network_interfaces

app = Flask(__name__)

print("About to import api_bp...")
try:
    from api.routes import api_bp
    print("Successfully imported api_bp")
    print(f"Blueprint name: {api_bp.name}")
    
    print("About to register blueprint...")
    app.register_blueprint(api_bp)
    print("Blueprint registered successfully")
    
except Exception as e:
    print(f"ERROR importing/registering api_bp: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Debug: Print all registered routes
print("\n=== REGISTERED ROUTES ===")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} -> {rule.methods}")
print("========================\n")

if __name__ == '__main__':
    print("Starting Flask Attendance System")
    print("=" * 40)
    
    try:
        init_db()
        migrate_database()
        
        interfaces = get_all_network_interfaces()
        print(f"Primary IP: {interfaces[0]}")
        print("\nAccess URLs:")
        for ip in interfaces[:3]:  # Show top 3
            print(f"  → http://{ip}:5000")
        
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/students')
def students():
    return render_template('students.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')