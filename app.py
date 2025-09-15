# app.py
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import func
from dotenv import load_dotenv
import os

# ------------------------------------------------------
# Load environment
# ------------------------------------------------------
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["https://standfindr.web.app", "http://localhost:5173", "http://127.0.0.1:5173"])

# ------------------------------------------------------
# Database
# ------------------------------------------------------
db_url = os.getenv("DATABASE_URL")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ------------------------------------------------------
# Models
# ------------------------------------------------------
class Route(db.Model):
    __tablename__ = "routes"
    id = db.Column(db.Integer, primary_key=True)
    start_location = db.Column(db.String(100), nullable=False)
    end_location = db.Column(db.String(100), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)

    fares = db.relationship("Fare", backref="route", cascade="all, delete-orphan")
    landmarks = db.relationship("Landmark", backref="route", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "start_location": self.start_location,
            "end_location": self.end_location,
            "vehicle_type": self.vehicle_type,
            "fares": [{"id": f.id, "estimated_fare": float(f.estimated_fare)} for f in self.fares],
            "landmarks": [{"id": l.id, "description": l.description, "image_url": l.image_url} for l in self.landmarks]
        }

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

# ------------------------------------------------------
# Routes
# ------------------------------------------------------
@app.route("/")
def hello():
    return "Flask backend is working!"

# -----------------------------
# Case-insensitive search route
# -----------------------------
@app.route("/api/search", methods=["GET"])
def search_routes():
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()

    if not start or not end:
        return jsonify([])

    routes = Route.query.filter(
        func.lower(Route.start_location) == func.lower(start),
        func.lower(Route.end_location) == func.lower(end)
    ).all()

    return jsonify([r.to_dict() for r in routes])

# -----------------------------
# Debug: see all routes
# -----------------------------
@app.route("/api/debug/all-routes", methods=["GET"])
def debug_all_routes():
    routes = Route.query.all()
    return jsonify([r.to_dict() for r in routes])

# ------------------------------------------------------
# Run
# ------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
