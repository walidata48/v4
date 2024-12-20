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

class SessionDateCount(db.Model):
    __tablename__ = 'session_date_counts'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    registration_count = db.Column(db.Integer, default=0)
    
    # Add unique constraint to prevent duplicate counts for same session-date
    __table_args__ = (
        db.UniqueConstraint('session_id', 'session_date', name='unique_session_date'),
    )
    
    session = db.relationship('Session', backref='date_counts', lazy=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    coach_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='attendances_as_user')
    coach = db.relationship('User', foreign_keys=[coach_id], backref='attendances_as_coach')
    registration = db.relationship('Registration', backref='attendances')

    def __repr__(self):
        return f'<Attendance {self.id} User:{self.user_id} Date:{self.date}>'

