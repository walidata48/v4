from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_coach = db.Column(db.Boolean, default=False)
    registrations = db.relationship('Registration', backref='registered_user', lazy=True)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    quota = db.Column(db.Integer, nullable=False)

    @classmethod
    def get(cls, session_id):
        """Helper method to get a session by ID"""
        return cls.query.get_or_404(session_id)


class RegistrationGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    registrations = db.relationship('Registration', backref='group', lazy=True)
    user = db.relationship('User', backref='registration_groups')

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    registration_group_id = db.Column(db.Integer, db.ForeignKey('registration_group.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    session = db.relationship('Session', backref='registrations', lazy=True)

