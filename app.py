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

# Enhanced database configuration with detailed error logging
try:
    db_url = os.getenv('DATABASE_URL')
    print(f"🔧 DATABASE_URL: {db_url}")
    
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        print(f"🔧 Converted to: {db_url}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {
            'sslmode': 'require'
        }
    }
    
    print("🔄 Attempting to initialize SQLAlchemy...")
    db = SQLAlchemy(app)
    print("✅ SQLAlchemy initialized successfully!")
    
except Exception as e:
    print(f"❌ SQLAlchemy initialization failed: {e}")
    import traceback
    traceback.print_exc()  # This will show the full error stack
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
        
    print("✅ Database models defined successfully!")
else:
    # Define empty classes if no database
    class Route: pass
    class Landmark: pass
    class Fare: pass
    print("⚠️  Using placeholder classes - database not connected")

# Debug route to check raw database connection
@app.route('/api/debug/raw-db')
def debug_raw_db():
    try:
        import psycopg2
        print("🔄 Attempting raw PostgreSQL connection...")
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        cur.execute('SELECT 1')
        result = cur.fetchone()
        conn.close()
        print("✅ Raw database connection successful!")
        return jsonify({'status': 'success', 'message': 'Raw database connection successful!'})
    except Exception as e:
        print(f"❌ Raw connection failed: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# Debug route to check SQLAlchemy database connection
@app.route('/api/debug/db')
def debug_db():
    if not db:
        return jsonify({'status': 'error', 'message': 'SQLAlchemy not initialized'})
    
    try:
        print("🔄 Testing SQLAlchemy connection...")
        result = db.session.execute(db.text('SELECT 1'))
        print("✅ SQLAlchemy connection successful!")
        return jsonify({'status': 'success', 'message': 'Database connected!'})
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return jsonify({'status': 'error', 'message': str(e), 'database_url': os.getenv('DATABASE_URL')})

# Debug route to check environment variables
@app.route('/api/debug/env')
def debug_env():
    return jsonify({
        'database_url': os.getenv('DATABASE_URL'),
        'flask_env': os.getenv('FLASK_ENV')
    })

# Simple health check
@app.route('/api/health', methods=['GET'])
def health_check():
    if db:
        try:
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

    # Sample data insertion endpoint
    @app.route('/api/insert-sample-data', methods=['POST'])
    def insert_sample_data():
        try:
            db.session.query(Fare).delete()
            db.session.query(Landmark).delete()
            db.session.query(Route).delete()

            sample_route = Route(
                start_location="Sangre Grande",
                end_location="Port of Spain",
                vehicle_type="Red Band Maxi"
            )
            db.session.add(sample_route)
            db.session.flush()

            landmarks = [
                Landmark(
                    route_id=sample_route.id,
                    description="Sangre Grande Maxi Stand (opposite the catholic church)",
                    image_url="http://localhost:5000/static/landmark.jpg"
                ),
                Landmark(
                    route_id=sample_route.id,
                    description="Port of Spain drop-off at City Gate",
                    image_url=None
                )
            ]

            fare = Fare(
                route_id=sample_route.id,
                estimated_fare=15.00
            )

            db.session.add_all(landmarks)
            db.session.add(fare)
            db.session.commit()

            return jsonify({
                'message': 'Sample data inserted successfully',
                'route_id': sample_route.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/routes', methods=['GET'])
    def get_routes():
        try:
            routes = Route.query.all()
            return jsonify([{
                'id': route.id,
                'start_location': route.start_location,
                'end_location': route.end_location,
                'vehicle_type': route.vehicle_type
            } for route in routes])
        except Exception as e:
            print(f"Error fetching routes: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/routes/<int:id>', methods=['GET'])
    def get_route(id):
        try:
            route = Route.query.get_or_404(id)
            landmarks = Landmark.query.filter_by(route_id=id).all()
            fares = Fare.query.filter_by(route_id=id).all()

            return jsonify({
                'route': {
                    'id': route.id,
                    'start_location': route.start_location,
                    'end_location': route.end_location,
                    'vehicle_type': route.vehicle_type
                },
                'landmarks': [{
                    'id': landmark.id,
                    'description': landmark.description,
                    'image_url': landmark.image_url
                } for landmark in landmarks],
                'fares': [{
                    'id': fare.id,
                    'estimated_fare': float(fare.estimated_fare)
                } for fare in fares]
            })
        except Exception as e:
            print(f"Error fetching route {id}: {e}")
            return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Starting Flask server on port {port}...")
    app.run(debug=True, host='0.0.0.0', port=port)