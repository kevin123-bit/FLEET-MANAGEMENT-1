import os
import sys
from datetime import datetime, timedelta
import logging
import json
from importlib.metadata import version, PackageNotFoundError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to check and install required packages
def check_dependencies():
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'flask_login',
        'geopy',
        'pytz'
    ]
    try:
        for package in required_packages:
            try:
                version(package.replace('_', '-'))
            except PackageNotFoundError:
                logger.error(f"Package {package} not found")
                logger.info("Please run 'pip install -r requirements.txt' to install required packages")
                sys.exit(1)
    except Exception as e:
        logger.error(f"Dependencies not satisfied: {e}")
        logger.info("Please run 'pip install -r requirements.txt' to install required packages")
        sys.exit(1)

# Check dependencies before imports
check_dependencies()

# Now import required packages
try:
    from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
    from flask_sqlalchemy import SQLAlchemy
    from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
    from geopy.geocoders import Nominatim
    import pytz
except ImportError as e:
    logger.error(f"Failed to import required package: {e}")
    sys.exit(1)

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load environment variables
if os.path.exists('.env'):
    from dotenv import load_dotenv
    load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # In production, use a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fleet.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # In production, use password hashing
    is_admin = db.Column(db.Boolean, default=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False, default='Truck')  # New field
    model = db.Column(db.String(100))  # New field
    year = db.Column(db.Integer)  # New field
    current_location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    fuel_level = db.Column(db.Float, default=100.0)
    status = db.Column(db.String(50), default='active')
    last_maintenance = db.Column(db.DateTime)
    tank_capacity = db.Column(db.Float, default=100.0)
    maintenance_records = db.relationship('MaintenanceRecord', backref='vehicle', lazy=True)
    fuel_records = db.relationship('FuelRecord', backref='vehicle', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    image_url = db.Column(db.String(500))  # New field for vehicle image

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    license_number = db.Column(db.String(50), unique=True)
    performance_rating = db.Column(db.Float, default=7.0)
    speed_score = db.Column(db.Float, default=7.0)
    braking_score = db.Column(db.Float, default=7.0)
    safety_rating = db.Column(db.String(20), default='Good')
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    fuel_records = db.relationship('FuelRecord', backref='driver', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MaintenanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200))
    cost = db.Column(db.Float)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FuelRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    quantity = db.Column(db.Float)
    cost = db.Column(db.Float)
    location = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def get_safety_badge_color(score):
    if score >= 8.0:
        return 'success'
    elif score >= 6.0:
        return 'warning'
    else:
        return 'danger'

def get_fuel_level_color(level):
    if level >= 70:
        return 'success'
    elif level >= 30:
        return 'warning'
    return 'danger'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:  # In production, use proper password verification
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered')
            return redirect(url_for('signup'))
        
        user = User(
            username=request.form['username'],
            password=request.form['password'],  # In production, use password hashing
            email=request.form['email']
        )
        db.session.add(user)
        try:
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    return render_template('dashboard.html', vehicles=vehicles, drivers=drivers)

@app.route('/vehicle/<int:id>')
@login_required
def vehicle_details(id):
    vehicle = Vehicle.query.get_or_404(id)
    maintenance_records = MaintenanceRecord.query.filter_by(vehicle_id=id).order_by(MaintenanceRecord.date.desc()).all()
    fuel_records = FuelRecord.query.filter_by(vehicle_id=id).order_by(FuelRecord.date.desc()).all()
    return render_template('vehicle_details.html', 
                         vehicle=vehicle, 
                         maintenance_records=maintenance_records,
                         fuel_records=fuel_records)

@app.route('/vehicle-tracking')
@login_required
def vehicle_tracking():
    vehicles = Vehicle.query.all()
    return render_template('vehicle_tracking.html', vehicles=vehicles)

@app.route('/maintenance')
@login_required
def maintenance():
    vehicles = Vehicle.query.all()
    upcoming_maintenance = MaintenanceRecord.query.filter_by(status='scheduled').all()
    maintenance_history = MaintenanceRecord.query.filter_by(status='completed').all()
    return render_template('maintenance.html', 
                         vehicles=vehicles,
                         upcoming_maintenance=upcoming_maintenance,
                         maintenance_history=maintenance_history)

@app.route('/driver-performance')
@login_required
def driver_performance():
    drivers = Driver.query.all()
    
    # Calculate average scores
    avg_speed_score = sum(d.speed_score for d in drivers) / len(drivers) if drivers else 0
    avg_braking_score = sum(d.braking_score for d in drivers) / len(drivers) if drivers else 0
    
    # Calculate safety ratings for each driver
    for driver in drivers:
        # Safety rating is weighted average of speed and braking scores
        driver.safety_rating = (driver.speed_score * 0.6 + driver.braking_score * 0.4)
    
    # Calculate overall safety index
    safety_index = sum(d.safety_rating for d in drivers) / len(drivers) if drivers else 0
    
    # Find top performing driver
    top_driver = max(drivers, key=lambda d: d.performance_rating) if drivers else None
    
    return render_template(
        'driver_performance.html',
        drivers=drivers,
        avg_speed_score=avg_speed_score,
        avg_braking_score=avg_braking_score,
        safety_index=safety_index,
        top_driver=top_driver,
        get_safety_badge_color=get_safety_badge_color
    )

@app.route('/fuel-management')
@login_required
def fuel_management():
    vehicles = Vehicle.query.all()
    drivers = Driver.query.all()
    fuel_records = FuelRecord.query.order_by(FuelRecord.date.desc()).all()
    
    # Calculate fuel statistics for the current month
    current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_records = [r for r in fuel_records if r.date >= current_month]
    
    total_fuel_consumption = sum(record.quantity for record in month_records)
    total_fuel_cost = sum(record.cost for record in month_records)
    avg_consumption = total_fuel_consumption / len(vehicles) if vehicles else 0
    
    # Calculate efficiency rating (example calculation)
    efficiency_rating = 7.5  # This should be calculated based on actual metrics
    
    return render_template('fuel_management.html',
                         vehicles=vehicles,
                         drivers=drivers,
                         fuel_records=fuel_records,
                         total_fuel_consumption=total_fuel_consumption,
                         total_fuel_cost=total_fuel_cost,
                         avg_consumption=avg_consumption,
                         efficiency_rating=efficiency_rating)

# Vehicle Management Routes
@app.route('/vehicles')
@login_required
def vehicles():
    vehicles = Vehicle.query.all()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/add-vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    current_year = datetime.utcnow().year
    if request.method == 'POST':
        try:
            vehicle = Vehicle(
                name=request.form['name'],
                vehicle_type=request.form['vehicle_type'],
                model=request.form['model'],
                year=int(request.form['year']),
                tank_capacity=float(request.form['tank_capacity']),
                image_url=request.form['image_url']
            )
            db.session.add(vehicle)
            db.session.commit()
            flash('Vehicle added successfully')
            return redirect(url_for('vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding vehicle: {str(e)}')
            return redirect(url_for('add_vehicle'))
    
    return render_template('add_vehicle.html', current_year=current_year)

@app.route('/edit-vehicle/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(id):
    vehicle = Vehicle.query.get_or_404(id)
    current_year = datetime.utcnow().year
    if request.method == 'POST':
        try:
            vehicle.name = request.form['name']
            vehicle.vehicle_type = request.form['vehicle_type']
            vehicle.model = request.form['model']
            vehicle.year = int(request.form['year'])
            vehicle.tank_capacity = float(request.form['tank_capacity'])
            vehicle.image_url = request.form['image_url']
            db.session.commit()
            flash('Vehicle updated successfully')
            return redirect(url_for('vehicles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating vehicle: {str(e)}')
    
    return render_template('edit_vehicle.html', vehicle=vehicle, current_year=current_year)

# API Routes
@app.route('/api/vehicle-locations')
@login_required
def vehicle_locations():
    vehicles = Vehicle.query.all()
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'latitude': v.latitude,
        'longitude': v.longitude,
        'status': v.status,
        'fuel_level': v.fuel_level
    } for v in vehicles])

@app.route('/api/maintenance-alerts')
@login_required
def maintenance_alerts():
    alerts = MaintenanceRecord.query.filter_by(status='scheduled').all()
    return jsonify([{
        'id': alert.id,
        'vehicle_id': alert.vehicle_id,
        'vehicle_name': alert.vehicle.name,
        'description': alert.description,
        'date': alert.date.strftime('%Y-%m-%d')
    } for alert in alerts])

@app.route('/api/driver-performance/<int:driver_id>')
@login_required
def driver_performance_data(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    # This would typically fetch historical performance data from a time-series database
    # For now, returning sample data
    return jsonify({
        'name': driver.name,
        'current_rating': driver.performance_rating,
        'dates': [(datetime.utcnow() - timedelta(days=x*30)).strftime('%Y-%m') for x in range(5, -1, -1)],
        'scores': [max(5.0, min(9.5, driver.performance_rating + (x/10 - 0.3))) for x in range(6)]
    })

@app.route('/complete-maintenance', methods=['POST'])
@login_required
def complete_maintenance():
    try:
        data = request.get_json()
        maintenance_id = data.get('maintenance_id')
        if not maintenance_id:
            return jsonify({'success': False, 'error': 'Maintenance ID is required'}), 400
            
        maintenance = MaintenanceRecord.query.get_or_404(maintenance_id)
        maintenance.status = 'completed'
        
        # Update vehicle's last maintenance date
        vehicle = maintenance.vehicle
        vehicle.last_maintenance = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add-fuel-record', methods=['POST'])
@login_required
def add_fuel_record():
    try:
        record = FuelRecord(
            vehicle_id=request.form['vehicle_id'],
            driver_id=request.form['driver_id'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%dT%H:%M'),
            quantity=float(request.form['quantity']),
            cost=float(request.form['cost']),
            location=request.form['location']
        )
        db.session.add(record)
        
        # Update vehicle fuel level
        vehicle = Vehicle.query.get(record.vehicle_id)
        if vehicle:
            vehicle.fuel_level = min(100, vehicle.fuel_level + (record.quantity / vehicle.tank_capacity) * 100)
        
        db.session.commit()
        flash('Fuel record added successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding fuel record: {str(e)}')
    return redirect(url_for('fuel_management'))

@app.route('/add-maintenance', methods=['POST'])
@login_required
def add_maintenance():
    try:
        record = MaintenanceRecord(
            vehicle_id=request.form['vehicle_id'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            description=request.form['description'],
            cost=float(request.form['cost']),
            status='scheduled'
        )
        db.session.add(record)
        db.session.commit()
        flash('Maintenance record added successfully')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding maintenance record: {str(e)}')
    return redirect(url_for('maintenance'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
