import os
from datetime import datetime
import random
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'traveloop_super_secret_key_hackathon'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///traveloop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Upload Folder for Profile Pictures
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    country = db.Column(db.String(50), nullable=True)
    pincode = db.Column(db.String(20), nullable=True) 
    join_date = db.Column(db.DateTime, default=datetime.utcnow) 
    password_hash = db.Column(db.String(256), nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)
    
    trips = db.relationship('Trip', backref='traveler', lazy=True)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trip_type = db.Column(db.String(20), nullable=False) # 'ongoing', 'preplanned', or 'completed'
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(20), nullable=False)
    end_date = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

class PackingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(100), nullable=False)
    is_packed = db.Column(db.Boolean, default=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)

class TripNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    note_text = db.Column(db.Text, nullable=False)
    day_reference = db.Column(db.String(50), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

# --- CURATED IMAGES FOR BETTER UI ---
BEAUTIFUL_PLACE_IMAGES = [
    "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?auto=format&fit=crop&w=800&q=80", # Paris
    "https://images.unsplash.com/photo-1535139262971-c51845709a48?auto=format&fit=crop&w=800&q=80", # Asia
    "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?auto=format&fit=crop&w=800&q=80", # NY
    "https://images.unsplash.com/photo-1516026672322-bc52d61a55d5?auto=format&fit=crop&w=800&q=80", # Africa
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=800&q=80", # Europe City
    "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?auto=format&fit=crop&w=800&q=80", # Venice
    "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?auto=format&fit=crop&w=800&q=80", # Mountains/Lake
]

# --- CONTEXT PROCESSOR ---
@app.context_processor
def inject_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return dict(user=user)
    return dict(user=None)

# --- AUTH ROUTES ---
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email address already exists. Please log in.', 'error')
            return redirect(url_for('register'))
            
        new_user = User(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=email,
            phone_number=request.form.get('phone_number'),
            city=request.form.get('city'),
            country=request.form.get('country'),
            pincode=request.form.get('pincode'),
            password_hash=generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password_hash, request.form.get('password')):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

# --- MAIN ROUTES ---
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Suggestions for dummy data
    suggestions = ["Tokyo, Japan", "Paris, France", "New York City, USA", "London, UK", "Rome, Italy"]
    regions = [
        {"name": "Europe", "image": BEAUTIFUL_PLACE_IMAGES[0]},
        {"name": "Asia", "image": BEAUTIFUL_PLACE_IMAGES[1]},
        {"name": "Americas", "image": BEAUTIFUL_PLACE_IMAGES[2]},
        {"name": "Africa", "image": BEAUTIFUL_PLACE_IMAGES[3]}
    ]
    return render_template('dashboard.html', suggestions=suggestions, regions=regions)

@app.route('/my-trips')
def my_trips():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    return render_template(
        'my_trips.html', 
        ongoing_trips=Trip.query.filter_by(user_id=user_id, trip_type='ongoing').all(), 
        preplanned_trips=Trip.query.filter_by(user_id=user_id, trip_type='preplanned').all(), 
        completed_trips=Trip.query.filter_by(user_id=user_id, trip_type='completed').all()
    )

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Fetch all types of trips to match the updated profile.html requirements
    return render_template(
        'profile.html', 
        ongoing_trips=Trip.query.filter_by(user_id=user_id, trip_type='ongoing').all(),
        preplanned_trips=Trip.query.filter_by(user_id=user_id, trip_type='preplanned').all(), 
        completed_trips=Trip.query.filter_by(user_id=user_id, trip_type='completed').all()
    )

@app.route('/edit-profile', methods=['POST'])
def edit_profile():
    """Handles updating basic details and uploading profile picture"""
    if 'user_id' not in session: return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    # Update text fields
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.email = request.form.get('email', user.email)
    user.phone_number = request.form.get('phone_number', user.phone_number)
    user.city = request.form.get('city', user.city)
    user.country = request.form.get('country', user.country)
    user.pincode = request.form.get('pincode', user.pincode)
    
    # Handle File Upload
    if 'profile_pic' in request.files:
        file = request.files['profile_pic']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            # Save file to static/uploads
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Save the path to the database
            user.profile_image = f"/static/uploads/{filename}"
            
    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/create-trip', methods=['GET', 'POST'])
def create_trip():
    if 'user_id' not in session: return redirect(url_for('login'))
        
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        # --- LOGIC: Auto-Categorize Trip Based on Dates ---
        calc_trip_type = 'preplanned' # Default
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            today = datetime.today().date()
            
            if end_date < today:
                calc_trip_type = 'completed'
            elif start_date > today:
                calc_trip_type = 'preplanned'
            else:
                calc_trip_type = 'ongoing'
        except (ValueError, TypeError):
            # If dates are missing or invalid, fallback to whatever the user selected
            calc_trip_type = request.form.get('trip_type', 'preplanned')

        new_trip = Trip(
            user_id=session['user_id'],
            trip_type=calc_trip_type,
            destination=request.form.get('destination', 'Unknown'),
            start_date=start_date_str,
            end_date=end_date_str,
            description=request.form.get('description', ''),
            image_url=random.choice(BEAUTIFUL_PLACE_IMAGES) # Assign a beautiful curated image
        )
        db.session.add(new_trip)
        db.session.commit()
        
        flash('Trip categorized and created successfully!', 'success')
        return redirect(url_for('my_trips'))
        
    dummy_places = ["Tokyo, Japan", "Paris, France", "New York City, USA", "London, UK", "Rome, Italy"]
    suggested_places = [
        {"name": "Taj Mahal, India", "image": "https://images.unsplash.com/photo-1548013146-72479768bada?w=800&q=80"},
        {"name": "Maldives", "image": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800&q=80"},
        {"name": "Rio de Janeiro", "image": "https://images.unsplash.com/photo-1483729558449-99ef09a8c325?w=800&q=80"}
    ]
    
    return render_template('create_trip.html', places=dummy_places, suggested_places=suggested_places)

@app.route('/explore/<category>')
def explore_category(category):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    formatted_category = category.replace('-', ' ').title()
    dummy_items = []
    
    for i in range(1, 7):
        dummy_items.append({
            "name": f"{formatted_category} Spot {i}",
            "image": random.choice(BEAUTIFUL_PLACE_IMAGES),
            "budget": f"${random.randint(150, 800)}",
            "description": f"Experience the absolute best of {formatted_category.lower()} here."
        })
        
    return render_template('explore_category.html', category_name=formatted_category, items=dummy_items)


# --- ITINERARY ROUTES (Integrated from recent changes) ---

@app.route('/itinerary/select')
def select_itinerary():
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # Dummy data simulating database fetch for Ongoing/Preplanned
    available_trips = [
        {"id": 1, "destination": "Tokyo, Japan", "type": "Preplanned", "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&q=80"},
        {"id": 2, "destination": "Paris, France", "type": "Ongoing", "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=80"}
    ]
    return render_template('select_itinerary.html', trips=available_trips)

@app.route('/itinerary/build/<int:trip_id>')
def build_itinerary(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    destination = "Tokyo, Japan" if trip_id == 1 else "Paris, France"
    return render_template('itinerary_builder.html', destination=destination, trip_id=trip_id)

@app.route('/itinerary/view/<int:trip_id>')
def view_itinerary(trip_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    # If a trip doesn't have an itinerary, you'd normally fetch it from DB. 
    # For dummy purposes, returning dummy data for previous trips, else None.
    if trip_id in [97, 98, 99]: # Our dummy previous trip IDs
        dummy_previous_itinerary = {
            "destination": "London, UK" if trip_id == 99 else ("Venice, Italy" if trip_id == 98 else "Maldives"),
            "days": [
                {
                    "day_number": 1,
                    "activities": [
                        {"name": "Arrival & Check-in", "expense": 50},
                        {"name": "Lunch at local cafe", "expense": 35},
                        {"name": "City Sightseeing", "expense": 40}
                    ]
                },
                {
                    "day_number": 2,
                    "activities": [
                        {"name": "Museum Tour", "expense": 30},
                        {"name": "Dinner Cruise", "expense": 85}
                    ]
                }
            ],
            "total_expense": 240
        }
        return render_template('itinerary_view.html', itinerary=dummy_previous_itinerary)
        
    return render_template('itinerary_view.html', itinerary=None)

# --- NEW MODULE ROUTES (Updated Navigation Logic) ---

@app.route('/packing', methods=['GET', 'POST'])
def packing_list():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Fetch all trips for the dropdown
    trips = Trip.query.filter_by(user_id=user_id).all()
    selected_trip_id = request.args.get('trip_id', type=int)
    
    # Handle Form Submission
    if request.method == 'POST' and selected_trip_id:
        category = request.form.get('category')
        item_name = request.form.get('item_name')
        if category and item_name:
            new_item = PackingItem(trip_id=selected_trip_id, category=category, item_name=item_name)
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('packing_list', trip_id=selected_trip_id))

    items = PackingItem.query.filter_by(trip_id=selected_trip_id).all() if selected_trip_id else []
    
    grouped_items = {}
    total_packed = 0
    for item in items:
        if item.category not in grouped_items:
            grouped_items[item.category] = []
        grouped_items[item.category].append(item)
        if item.is_packed: total_packed += 1

    progress = int((total_packed / len(items)) * 100) if items else 0

    return render_template('packing_list.html', trips=trips, selected_trip_id=selected_trip_id, 
                           grouped_items=grouped_items, progress=progress, 
                           total_items=len(items), total_packed=total_packed)

@app.route('/packing/toggle/<int:item_id>')
def toggle_packing_item(item_id):
    item = PackingItem.query.get_or_404(item_id)
    item.is_packed = not item.is_packed
    db.session.commit()
    return redirect(url_for('packing_list', trip_id=item.trip_id))

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    trips = Trip.query.filter_by(user_id=user_id).all()
    selected_trip_id = request.args.get('trip_id', type=int)
    selected_trip = Trip.query.get(selected_trip_id) if selected_trip_id else None

    if request.method == 'POST' and selected_trip_id:
        category = request.form.get('category')
        description = request.form.get('description')
        qty = request.form.get('quantity', '1')
        unit_cost = float(request.form.get('unit_cost', 0))
        
        # Calculate total amount
        qty_num = float(qty.split()[0]) if qty and qty.split()[0].replace('.','',1).isdigit() else 1
        amount = unit_cost * qty_num

        new_expense = Expense(trip_id=selected_trip_id, category=category, description=description, 
                              quantity=qty, unit_cost=unit_cost, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('expenses', trip_id=selected_trip_id))

    expense_list = Expense.query.filter_by(trip_id=selected_trip_id).all() if selected_trip_id else []
    total_spent = sum(e.amount for e in expense_list)

    return render_template('expenses.html', trips=trips, selected_trip=selected_trip, 
                           expenses=expense_list, total_spent=total_spent)

@app.route('/notes', methods=['GET', 'POST'])
def trip_notes():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_id = session['user_id']
    
    trips = Trip.query.filter_by(user_id=user_id).all()
    selected_trip_id = request.args.get('trip_id', type=int)

    if request.method == 'POST' and selected_trip_id:
        new_note = TripNote(
            trip_id=selected_trip_id,
            title=request.form.get('title'),
            note_text=request.form.get('note_text'),
            day_reference=request.form.get('day_reference')
        )
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for('trip_notes', trip_id=selected_trip_id))

    notes = TripNote.query.filter_by(trip_id=selected_trip_id).order_by(TripNote.date_added.desc()).all() if selected_trip_id else []
    return render_template('notes.html', trips=trips, selected_trip_id=selected_trip_id, notes=notes)

@app.route('/notes/delete/<int:note_id>')
def delete_note(note_id):
    note = TripNote.query.get_or_404(note_id)
    trip_id = note.trip_id
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('trip_notes', trip_id=trip_id))
# --- INITIALIZATION ---
with app.app_context():
    # Because we added new columns (pincode, join_date), drop old tables to recreate schema 
    # (WARNING: This clears old data. Remove db.drop_all() if you are using Flask-Migrate later)
    db.drop_all() 
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)