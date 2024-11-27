from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Session, Registration, RegistrationGroup
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
    
    if request.method == 'POST':
        session_id = request.form.get('session_id')
        base_session = Session.query.get_or_404(session_id)
        
        # Check if user already has registrations
        existing_registrations = Registration.query.filter_by(user_id=session['user_id']).first()
        if existing_registrations:
            flash('You already have registered sessions.', 'error')
            return redirect(url_for('view_schedule'))
        
        # Calculate dates for 4 weekly sessions
        today = datetime.today()
        start_of_week = today - timedelta(days=today.weekday())
        day_to_date = {
            'Monday': start_of_week,
            'Tuesday': start_of_week + timedelta(days=1),
            'Wednesday': start_of_week + timedelta(days=2),
            'Thursday': start_of_week + timedelta(days=3),
            'Friday': start_of_week + timedelta(days=4),
            'Saturday': start_of_week + timedelta(days=5),
            'Sunday': start_of_week + timedelta(days=6)
        }
        
        base_date = day_to_date[base_session.day]
        
        # Create registration group
        registration_group = RegistrationGroup(user_id=session['user_id'])
        db.session.add(registration_group)
        db.session.flush()  # To get the registration_group.id
        
        # Create 4 weekly sessions
        for week in range(4):
            session_date = base_date + timedelta(weeks=week)
            
            # Check quota for this specific date
            existing_count = Registration.query.filter_by(
                session_id=session_id,
                session_date=session_date
            ).count()
            
            if existing_count >= base_session.quota:
                db.session.rollback()
                flash(f'Session on {session_date.strftime("%d %B %Y")} is full.', 'error')
                return redirect(url_for('select_session', location=location))
            
            new_registration = Registration(
                user_id=session['user_id'],
                session_id=session_id,
                session_date=session_date,
                registration_group_id=registration_group.id
            )
            db.session.add(new_registration)
        
        try:
            db.session.commit()
            flash('Successfully registered for 4 weekly sessions!', 'success')
        except:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            
        return redirect(url_for('view_schedule'))
    
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

@app.route('/register_for_session/<int:session_id>', methods=['POST'])
def register_for_session(session_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Check if user has already registered for any sessions
    existing_registrations = Registration.query.filter_by(user_id=user_id).count()
    if existing_registrations >= 1:  # Since each registration represents 4 weekly sessions
        flash('You have already registered for sessions.', 'error')
        return redirect(url_for('view_schedule'))
    
    # Get the selected session
    session_obj = Session.query.get_or_404(session_id)
    
    # Create new registration
    new_registration = Registration(
        user_id=user_id,
        session_id=session_id
    )
    
    db.session.add(new_registration)
    db.session.commit()
    
    return redirect(url_for('view_schedule'))

@app.route('/view_schedule')
def view_schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's registrations
    registrations = Registration.query.filter_by(user_id=session['user_id']).all()
    
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
    
    weekly_schedules = []
    
    for reg in registrations:
        base_session = reg.session
        # Get the base date for this session's day
        base_date = day_to_date[base_session.day]
        
        # Generate 4 consecutive weekly sessions
        for week in range(4):
            # Calculate the date for this week's session
            session_date = base_date + timedelta(weeks=week)
            
            weekly_schedules.append({
                'registration_id': reg.id,
                'location': base_session.location,
                'day': base_session.day,
                'date': session_date,
                'start_time': base_session.start_time,
                'end_time': base_session.end_time
            })
    
    # Sort schedules by date
    weekly_schedules.sort(key=lambda x: x['date'])
    
    return render_template('view_schedule.html', weekly_schedules=weekly_schedules)

@app.route('/cancel_registration/<int:registration_id>', methods=['POST'])
def cancel_registration(registration_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    registration = Registration.query.get_or_404(registration_id)
    
    # Verify that the registration belongs to the logged-in user
    if registration.user_id != session['user_id']:
        abort(403)
    
    db.session.delete(registration)
    db.session.commit()
    
    return redirect(url_for('view_schedule'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_coach', None)
    return redirect(url_for('home'))

@app.route('/coach/sessions')
def coach_sessions():
    if 'user_id' not in session or not session.get('is_coach'):
        return redirect(url_for('login'))
    
    # Get all sessions with their registrations
    sessions = Session.query.all()
    session_data = []
    
    for base_session in sessions:
        # Get all dates for this session
        registrations = Registration.query.filter_by(session_id=base_session.id)\
            .order_by(Registration.session_date).all()
        
        # Group registrations by date
        date_groups = {}
        for reg in registrations:
            date_str = reg.session_date.strftime('%Y-%m-%d')
            if date_str not in date_groups:
                date_groups[date_str] = {
                    'date': reg.session_date,
                    'registered_users': [],
                    'count': 0
                }
            date_groups[date_str]['registered_users'].append(reg.user)
            date_groups[date_str]['count'] += 1
        
        session_data.append({
            'session': base_session,
            'dates': date_groups
        })
    
    return render_template('coach_sessions.html', session_data=session_data)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 