from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Session, Registration
from config import Config
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
# db = SQLAlchemy(app)
# migrate = Migrate(app, db)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, age=age, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/coach_register', methods=['GET', 'POST'])
def coach_register():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_coach = User(name=name, age=age, email=email, password=hashed_password, is_coach=True)
        db.session.add(new_coach)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('coach_register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_coach'] = user.is_coach
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if session['is_coach']:
        registrations = Registration.query.all()
        return render_template('coach_dashboard.html', user=user, registrations=registrations)
    else:
        return redirect(url_for('select_location'))

@app.route('/select_location', methods=['GET', 'POST'])
def select_location():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        location = request.form['location']
        return redirect(url_for('select_session', location=location))
    
    locations = Session.query.with_entities(Session.location).distinct().all()
    return render_template('select_location.html', locations=locations)

@app.route('/select_session/<location>', methods=['GET', 'POST'])
def select_session(location):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get current date
    today = datetime.today()
    
    # Find the start of the current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    
    # Create a mapping of day names to their dates this week
    day_to_date = {
        'Monday': start_of_week,
        'Tuesday': start_of_week + timedelta(days=1),
        'Wednesday': start_of_week + timedelta(days=2),
        'Thursday': start_of_week + timedelta(days=3),
        'Friday': start_of_week + timedelta(days=4),
        'Saturday': start_of_week + timedelta(days=5),
        'Sunday': start_of_week + timedelta(days=6)
    }
    
    # Get sessions from database
    available_sessions = Session.query.filter_by(location=location).all()
    
    # Add date attribute to each session based on its day name
    for sess in available_sessions:
        sess.date = day_to_date[sess.day]
    
    return render_template('select_session.html', 
                         sessions=available_sessions, 
                         location=location)

@app.route('/register_for_session/<int:session_id>', methods=['GET', 'POST'])
def register_for_session(session_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    session_obj = Session.query.get(session_id)
    
    if request.method == 'POST':
        # Check if user has already registered for 4 sessions
        user_registrations = Registration.query.filter_by(user_id=user_id).count()
        if user_registrations >= 4:
            return "You have reached your registration limit."
        
        # Register the user for the session
        new_registration = Registration(user_id=user_id, session_id=session_id)
        db.session.add(new_registration)
        db.session.commit()
        
        return redirect(url_for('view_schedule'))
    
    return render_template('register_for_session.html', session=session_obj)

@app.route('/view_schedule')
def view_schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    registrations = Registration.query.filter_by(user_id=user_id).all()
    
    # Calculate the schedule based on the first session date
    schedule = []
    for registration in registrations:
        session_obj = Session.query.get(registration.session_id)
        # Assuming the session_obj has a start_date attribute
        start_date = session_obj.start_time  # Adjust this to your actual start date attribute
        for i in range(4):
            schedule.append(start_date + timedelta(weeks=i))
    
    return render_template('view_schedule.html', schedule=schedule)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_coach', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 