from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Session, Registration
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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
        sessions = Session.query.all()
        return render_template('user_dashboard.html', user=user, sessions=sessions)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_coach', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 