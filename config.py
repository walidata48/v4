import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://waliy:12345@localhost/sportv1'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 