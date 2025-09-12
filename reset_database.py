from app import app, db, Route, Landmark, Fare

with app.app_context():
    # Delete all data in correct order (to avoid foreign key issues)
    db.session.query(Fare).delete()
    db.session.query(Landmark).delete()
    db.session.query(Route).delete()
    db.session.commit()
    print("All data deleted successfully!")