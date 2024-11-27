import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://waliy:12345@localhost/sportigo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 