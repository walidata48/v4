from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Session, Registration, RegistrationGroup, SessionDateCount, Attendance
from config import Config
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
# db = SQLAlchemy(app)
migrate = Migrate(app, db)

@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('home.html')
    return render_template('landing.html')

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

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if session['is_coach']:
        # Get date filter from request args
        date_filter = request.args.get('date_filter')
        
        # Set default to today's date if no filter is applied
        if not date_filter:
            date_filter = datetime.today().strftime('%Y-%m-%d')
        
        # Convert string date to datetime for filtering
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        
        # Query registrations with joined data, excluding those already marked
        registrations = Registration.query\
            .join(User, Registration.user_id == User.id)\
            .join(Session, Registration.session_id == Session.id)\
            .outerjoin(Attendance, (Attendance.registration_id == Registration.id) & 
                       (Attendance.date == filter_date))\
            .filter(
                Attendance.id == None,  # Only include registrations without attendance records
                Registration.session_date == filter_date  # Ensure the session date matches
            )\
            .add_columns(
                User.name.label('user_name'),
                Session.location,
                Session.day,
                Session.start_time,
                Session.end_time,
                Registration.session_date
            )\
            .all()
        
        return render_template('coach_dashboard.html', 
                             user=user, 
                             registrations=registrations,
                             selected_date=date_filter)
    else:
        return redirect(url_for('home'))

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
            # Update counts after successful registration
            update_session_date_counts()
            flash('Successfully registered for 4 weekly sessions!', 'success')
        except:
            db.session.rollback()
            flash('An error occurred during registration.', 'error')
            
        return redirect(url_for('view_schedule'))
    
    # Get current date
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
    
    # First, ensure counts are up to date
    update_session_date_counts()
    
    # Get sessions with their counts
    base_sessions = Session.query.filter_by(location=location).all()
    sessions_with_quota = []
    
    for base_session in base_sessions:
        session_date = day_to_date[base_session.day].date()
        
        # Get count using both session_id and date
        registration_count = Registration.query.filter(
            Registration.session_id == base_session.id,
            Registration.session_date == session_date
        ).count()
        
        print(f"\nDEBUG: Checking session {base_session.id} for date {session_date}")
        print(f"DEBUG: Found {registration_count} registrations")
        
        session_info = {
            'id': base_session.id,
            'location': base_session.location,
            'day': base_session.day,
            'date': session_date,
            'start_time': base_session.start_time,
            'end_time': base_session.end_time,
            'quota': base_session.quota,
            'registered_users': registration_count,
            'available_quota': base_session.quota - registration_count
        }
        sessions_with_quota.append(session_info)
        
        # Debug print the actual registrations
        registrations = Registration.query.filter(
            Registration.session_id == base_session.id,
            Registration.session_date == session_date
        ).all()
        print("\nDetailed registrations:")
        for reg in registrations:
            print(f"Registration ID: {reg.id}")
            print(f"Session ID: {reg.session_id}")
            print(f"User ID: {reg.user_id}")
            print(f"Date: {reg.session_date}")
            print("---")
    
    return render_template('select_session.html', 
                         sessions=sessions_with_quota, 
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
    registrations = Registration.query.filter_by(user_id=session['user_id']).order_by(Registration.session_date).limit(4).all()
    
    weekly_schedules = []
    for reg in registrations:
        weekly_schedules.append({
            'registration_id': reg.id,
            'location': reg.session.location,
            'day': reg.session.day,
            'date': reg.session_date,
            'start_time': reg.session.start_time,
            'end_time': reg.session.end_time
        })
    
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

@app.route('/coach/check_users', methods=['GET', 'POST'])
def check_users():
    if 'user_id' not in session or not session.get('is_coach'):
        return redirect(url_for('login'))
    
    # Get date filter from either POST or GET request
    date_filter = request.form.get('date_filter') or request.args.get('date_filter')
    if not date_filter:
        date_filter = datetime.today().strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        checked_registration_ids = request.form.getlist('checked_users')
        
        if not checked_registration_ids:
            flash('No users were selected.', 'error')
            return redirect(url_for('dashboard'))
        
        try:
            # Save attendance records
            registrations = Registration.query\
                .filter(Registration.id.in_(checked_registration_ids))\
                .all()
            
            for registration in registrations:
                existing_attendance = Attendance.query.filter_by(
                    registration_id=registration.id,
                    date=datetime.strptime(date_filter, '%Y-%m-%d').date()
                ).first()
                
                if not existing_attendance:
                    attendance = Attendance(
                        user_id=registration.user_id,
                        coach_id=session['user_id'],
                        registration_id=registration.id,
                        date=datetime.strptime(date_filter, '%Y-%m-%d').date()
                    )
                    db.session.add(attendance)
            
            db.session.commit()
            flash('Attendance recorded successfully!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Error recording attendance. Please try again.', 'error')
            print(f"Error: {str(e)}")
            return redirect(url_for('dashboard'))
    
    # Get all registrations for the selected date
    all_attendances = Attendance.query\
        .join(User, Attendance.user_id == User.id)\
        .join(Registration)\
        .join(Session)\
        .filter(
            Attendance.date == datetime.strptime(date_filter, '%Y-%m-%d').date(),
            Attendance.coach_id == session['user_id']
        )\
        .all()
        
    return render_template('attendance_recap.html', 
                         attendances=all_attendances,
                         date=date_filter)

def update_session_date_counts():
    """Update the session date counts table based on registrations"""
    # Clear existing counts
    SessionDateCount.query.delete()
    
    # Get all unique session-date combinations and their counts
    counts = db.session.query(
        Registration.session_id,
        Registration.session_date,
        db.func.count(Registration.id).label('count')
    ).group_by(
        Registration.session_id,
        Registration.session_date
    ).all()
    
    # Create new count records
    for session_id, session_date, count in counts:
        new_count = SessionDateCount(
            session_id=session_id,
            session_date=session_date,
            registration_count=count
        )
        db.session.add(new_count)
    
    try:
        db.session.commit()
    except:
        db.session.rollback()
        raise

@app.route('/edit_registration/<int:registration_id>', methods=['GET', 'POST'])
def edit_registration(registration_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    registration = Registration.query.get_or_404(registration_id)
    
    # Verify that the registration belongs to the logged-in user
    if registration.user_id != session['user_id']:
        abort(403)
    
    if request.method == 'POST':
        new_session_id = request.form.get('session_id')
        
        if not new_session_id:
            flash('Please select a session', 'error')
            return redirect(url_for('edit_registration', registration_id=registration_id))
            
        new_session = Session.query.get_or_404(new_session_id)
        
        # Calculate the new date based on the selected session's day
        # First, get the start of the week for the original session date
        original_week_start = registration.session_date - timedelta(days=registration.session_date.weekday())
        
        # Calculate the new date by adding the appropriate number of days based on the new session's day
        day_to_number = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6
        }
        new_date = original_week_start + timedelta(days=day_to_number[new_session.day])
        
        # Check quota for the new session
        existing_count = Registration.query.filter_by(
            session_id=new_session_id,
            session_date=new_date
        ).count()
        
        if existing_count >= new_session.quota:
            flash('Selected session is full for this date.', 'error')
            return redirect(url_for('edit_registration', registration_id=registration_id))
        
        try:
            # Update both session_id and session_date
            registration.session_id = new_session_id
            registration.session_date = new_date
            
            db.session.commit()
            flash('Registration updated successfully!', 'success')
            return redirect(url_for('view_schedule'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating registration. Please try again.', 'error')
            print(f"Error: {str(e)}")  # For debugging
            return redirect(url_for('edit_registration', registration_id=registration_id))
    
    # GET request - show the edit form
    # Get available sessions for the same location
    current_location = registration.session.location
    available_sessions = Session.query.filter_by(location=current_location).all()
    
    return render_template('edit_registration.html', 
                         registration=registration, 
                         sessions=available_sessions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 