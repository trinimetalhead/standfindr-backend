from flask import Flask, jsonify, send_from_directory, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
import os
import traceback

# ------------------------------------------------------
# Load environment
# ------------------------------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://standfindr.web.app"])

# ------------------------------------------------------
# Database
# ------------------------------------------------------
db = None
try:
    db_url = os.getenv("DATABASE_URL")
    print(f"🔧 DATABASE_URL: {db_url}")

    if not db_url:
        raise ValueError("DATABASE_URL is not set!")

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

# ------------------------------------------------------
# Models
# ------------------------------------------------------
if db:
    class Route(db.Model):
        __tablename__ = "routes"
        id = db.Column(db.Integer, primary_key=True)
        start_location = db.Column(db.String(100), nullable=False)
        end_location = db.Column(db.String(100), nullable=False)
        vehicle_type = db.Column(db.String(50), nullable=False)

        fares = db.relationship("Fare", backref="route", cascade="all, delete-orphan")
        landmarks = db.relationship("Landmark", backref="route", cascade="all, delete-orphan")

    class Landmark(db.Model):
        __tablename__ = "landmarks"
        id = db.Column(db.Integer, primary_key=True)
        route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False)
        description = db.Column(db.Text, nullable=False)
        image_url = db.Column(db.String(255))

    class Fare(db.Model):
        __tablename__ = "fares"
        id = db.Column(db.Integer, primary_key=True)
        route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=False)
        estimated_fare = db.Column(db.Numeric(10, 2), nullable=False)

    print("✅ Database models defined successfully!")
else:
    print("⚠️ Using placeholder classes - database not connected")

# ------------------------------------------------------
# Routes
# ------------------------------------------------------
@app.route("/")
def hello():
    return "Flask backend is working!"

@app.route("/api/health")
def health_check():
    if not db:
        return jsonify({"status": "degraded", "database": "not configured"})
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"})
    except Exception as e:
        return jsonify({"status": "degraded", "database": "disconnected", "error": str(e)})

@app.route("/api/routes", methods=["GET"])
def get_routes():
    if not db:
        return jsonify({"status": "error", "message": "Database not connected"}), 500

    routes = Route.query.all()
    return jsonify([
        {
            "id": r.id,
            "start_location": r.start_location,
            "end_location": r.end_location,
            "vehicle_type": r.vehicle_type,
            "fares": [{"id": f.id, "estimated_fare": float(f.estimated_fare)} for f in r.fares],
            "landmarks": [{"id": l.id, "description": l.description, "image_url": l.image_url} for l in r.landmarks]
        }
        for r in routes
    ])

@app.route("/api/routes/<int:route_id>", methods=["GET"])
def get_route(route_id):
    if not db:
        return jsonify({"status": "error", "message": "Database not connected"}), 500

    r = Route.query.get(route_id)
    if not r:
        return jsonify({"status": "error", "message": "Route not found"}), 404

    return jsonify({
        "id": r.id,
        "start_location": r.start_location,
        "end_location": r.end_location,
        "vehicle_type": r.vehicle_type,
        "fares": [{"id": f.id, "estimated_fare": float(f.estimated_fare)} for f in r.fares],
        "landmarks": [{"id": l.id, "description": l.description, "image_url": l.image_url} for l in r.landmarks]
    })

@app.route("/api/search", methods=["GET"])
def search_routes():
    if not db:
        return jsonify({"status": "error", "message": "Database not connected"}), 500

    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()
    print(f"🔍 Searching for start='{start}' end='{end}'")

    query = Route.query
    if start:
        query = query.filter(Route.start_location.ilike(f"%{start}%"))
    if end:
        query = query.filter(Route.end_location.ilike(f"%{end}%"))

    routes = query.all()
    return jsonify([
        {
            "id": r.id,
            "start_location": r.start_location,
            "end_location": r.end_location,
            "vehicle_type": r.vehicle_type,
            "fares": [{"id": f.id, "estimated_fare": float(f.estimated_fare)} for f in r.fares],
            "landmarks": [{"id": l.id, "description": l.description, "image_url": l.image_url} for l in r.landmarks]
        }
        for r in routes
    ])

@app.route("/api/debug/db")
def debug_db():
    if not db:
        return jsonify({"status": "error", "message": "SQLAlchemy not initialized"})
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify({"status": "success", "message": "Database connected!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ------------------------------------------------------
# Run
# ------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(debug=True, host="0.0.0.0", port=port)
