from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# ------------------------------
# DATABASE CONFIGURATION
# ------------------------------
db = None
try:
    db_url = os.getenv("DATABASE_URL")
    print(f"🔧 DATABASE_URL: {db_url}")

    if not db_url:
        raise ValueError("DATABASE_URL is not set!")

    # For Render with psycopg[binary] and Python 3.13
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print("🔄 Attempting to initialize SQLAlchemy...")
    db = SQLAlchemy(app)
    print("✅ SQLAlchemy initialized successfully!")

except Exception as e:
    print(f"❌ SQLAlchemy initialization failed: {e}")
    traceback.print_exc()
    db = None

# ------------------------------
# DATABASE MODELS
# ------------------------------
if db:
    class Route(db.Model):
        __tablename__ = 'routes'
        id = db.Column(db.Integer, primary_key=True)
        start_location = db.Column(db.String(100), nullable=False)
        end_location = db.Column(db.String(100), nullable=False)
        vehicle_type = db.Column(db.String(50), nullable=False)

    class Landmark(db.Model):
        __tablename__ = 'landmarks'
        id = db.Column(db.Integer, primary_key=True)
        route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
        description = db.Column(db.Text, nullable=False)
        image_url = db.Column(db.String(255))

    class Fare(db.Model):
        __tablename__ = 'fares'
        id = db.Column(db.Integer, primary_key=True)
        route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
        estimated_fare = db.Column(db.Numeric(10, 2), nullable=False)

    print("✅ Database models defined successfully!")
else:
    class Route: pass
    class Landmark: pass
    class Fare: pass
    print("⚠️ Using placeholder classes - database not connected")

# ------------------------------
# ROUTES
# ------------------------------
@app.route('/')
def hello():
    return 'Flask backend is working!'

@app.route('/api/health')
def health_check():
    if db:
        try:
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'healthy', 'database': 'connected'})
        except Exception as e:
            return jsonify({'status': 'degraded', 'database': 'disconnected', 'error': str(e)})
    else:
        return jsonify({'status': 'degraded', 'database': 'not configured'})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ------------------------------
# DEBUG ROUTES (optional)
# ------------------------------
@app.route('/api/debug/db')
def debug_db():
    if not db:
        return jsonify({'status': 'error', 'message': 'SQLAlchemy not initialized'})
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'success', 'message': 'Database connected!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ------------------------------
# RUN APP
# ------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(debug=True, host='0.0.0.0', port=port)
