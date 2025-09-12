from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import load_dotenv
from flask import send_from_directory
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration with error handling
try:
    db_url = os.getenv('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db = SQLAlchemy(app)
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection error: {e}")
    # Set db to None to avoid errors
    db = None

# Define models only if database is connected
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
else:
    # Define empty classes if no database
    class Route: pass
    class Landmark: pass
    class Fare: pass

# Simple health check that doesn't require database
@app.route('/api/health', methods=['GET'])
def health_check():
    if db:
        try:
            # Try a simple database query
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'healthy', 'database': 'connected'})
        except Exception as e:
            return jsonify({'status': 'degraded', 'database': 'disconnected', 'error': str(e)})
    else:
        return jsonify({'status': 'degraded', 'database': 'not configured'})

# Simple test route
@app.route('/')
def hello():
    return 'Flask backend is working!'

# Only add database routes if database is connected
if db:
    @app.route('/api/debug/routes', methods=['GET'])
    def debug_routes():
        try:
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            has_routes_table = 'routes' in tables
            
            if not has_routes_table:
                return jsonify({'error': 'Routes table does not exist'}), 500
            
            routes_count = db.session.query(Route).count()
            result = db.session.execute(db.text('SELECT * FROM routes'))
            routes_data = [dict(row._mapping) for row in result]
            
            return jsonify({
                'tables_in_database': tables,
                'routes_table_exists': has_routes_table,
                'routes_count': routes_count,
                'routes_data': routes_data
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Add your other database routes here (get_routes, get_route, etc.)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)