from app import app, db, Route, Landmark, Fare

with app.app_context():
    # Clear existing data first
    db.session.query(Fare).delete()
    db.session.query(Landmark).delete()
    db.session.query(Route).delete()
    
    # Create sample route
    sample_route = Route(
        start_location="Sangre Grande",
        end_location="Port of Spain",
        vehicle_type="Red Band Maxi"
    )
    db.session.add(sample_route)
    db.session.flush()
    
    # Create sample landmarks
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
    
    # Create sample fare
    fare = Fare(
        route_id=sample_route.id,
        estimated_fare=15.00
    )
    
    # Add all to session and commit
    db.session.add_all(landmarks)
    db.session.add(fare)
    db.session.commit()
    
    print("✅ Sample data inserted successfully!")
    print("Vehicle Type: Red Band Maxi")
    print("Landmark: Sangre Grande Maxi Stand (opposite the catholic church)")
    print("Fare: $15.00")