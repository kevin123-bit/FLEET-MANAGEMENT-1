from app import app, db, User, Vehicle, Driver, MaintenanceRecord, FuelRecord
from datetime import datetime, timedelta
import random

def init_db():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create admin user
        admin = User(
            username='admin',
            password='admin123',  # In production, use proper password hashing
            email='admin@fleet.com',
            is_admin=True
        )
        db.session.add(admin)

        # Create vehicles
        vehicle_types = ['Truck', 'Van', 'Pickup', 'Car']
        vehicles = [
            Vehicle(
                name=f'Truck-{i}',
                vehicle_type=vehicle_types[i % len(vehicle_types)],
                current_location=f'Location {i}',
                latitude=random.uniform(40.7, 41.0),
                longitude=random.uniform(-74.1, -73.9),
                fuel_level=random.uniform(30.0, 100.0),
                status='active' if random.random() > 0.2 else 'maintenance',
                last_maintenance=datetime.now() - timedelta(days=random.randint(1, 30))
            ) for i in range(1, 6)
        ]
        for v in vehicles:
            db.session.add(v)

        # Create drivers
        drivers = [
            Driver(
                name=f'Driver {i}',
                license_number=f'LIC-{1000+i}',
                performance_rating=random.uniform(6.0, 9.5),
                speed_score=random.uniform(6.0, 9.5),
                braking_score=random.uniform(6.0, 9.5),
                safety_rating='Good',
                vehicle_id=i
            ) for i in range(1, 6)
        ]
        for d in drivers:
            db.session.add(d)

        # Create maintenance records
        for vehicle in vehicles:
            for _ in range(3):
                record = MaintenanceRecord(
                    vehicle_id=vehicle.id,
                    date=datetime.now() - timedelta(days=random.randint(1, 60)),
                    description=random.choice([
                        'Oil Change',
                        'Tire Rotation',
                        'Brake Inspection',
                        'Engine Maintenance',
                        'General Service'
                    ]),
                    cost=random.uniform(100, 1000),
                    status=random.choice(['completed', 'scheduled'])
                )
                db.session.add(record)

        # Create fuel records
        for _ in range(20):
            record = FuelRecord(
                vehicle_id=random.randint(1, 5),
                driver_id=random.randint(1, 5),
                date=datetime.now() - timedelta(days=random.randint(1, 30)),
                quantity=random.uniform(20, 100),
                cost=random.uniform(50, 250),
                location=f'Gas Station {random.randint(1, 5)}'
            )
            db.session.add(record)

        db.session.commit()
        print("Database initialized with sample data!")

if __name__ == '__main__':
    init_db()
