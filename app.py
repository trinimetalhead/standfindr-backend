from flask import Flask, jsonify, send_from_directory, request
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
# SAMPLE DATA INSERTION
# ------------------------------
@app.route('/api/insert-sample-data', methods=['POST'])
def insert_sample_data():
    if not db:
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 500

    try:
        # Clear tables first (optional)
        db.session.query(Fare).delete()
        db.session.query(Landmark).delete()
        db.session.query(Route).delete()
        db.session.commit()

        # Sample routes
        route1 = Route(start_location="Point A", end_location="Point B", vehicle_type="Bus")
        route2 = Route(start_location="Point C", end_location="Point D", vehicle_type="Taxi")
        db.session.add_all([route1, route2])
        db.session.commit()

        # Sample landmarks
        lm1 = Landmark(route_id=route1.id, description="Landmark 1", image_url=None)
        lm2 = Landmark(route_id=route2.id, description="Landmark 2", image_url=None)
        db.session.add_all([lm1, lm2])
        db.session.commit()

        # Sample fares
        fare1 = Fare(route_id=route1.id, estimated_fare=12.50)
        fare2 = Fare(route_id=route2.id, estimated_fare=8.75)
        db.session.add_all([fare1, fare2])
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Sample data inserted!'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)})

# ------------------------------
# GET ALL ROUTES
# ------------------------------
@app.route('/api/routes', methods=['GET'])
def get_routes():
    if not db:
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
    routes = Route.query.all()
    return jsonify([{
        'id': r.id,
        'start_location': r.start_location,
        'end_location': r.end_location,
        'vehicle_type': r.vehicle_type
    } for r in routes])

# ------------------------------
# GET SPECIFIC ROUTE
# ------------------------------
@app.route('/api/routes/<int:route_id>', methods=['GET'])
def get_route(route_id):
    if not db:
        return jsonify({'status': 'error', 'message': 'Database not connected'}), 500
    r = Route.query.get(route_id)
    if not r:
        return jsonify({'status': 'error', 'message': 'Route not found'}), 404
    return jsonify({
        'id': r.id,
        'start_location': r.start_location,
        'end_location': r.end_location,
        'vehicle_type': r.vehicle_type
    })

# ------------------------------
# DEBUG ROUTES
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
