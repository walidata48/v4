import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:BvflFpthahDyBvVyeyCzDgEMTqIAVSdN@junction.proxy.rlwy.net:52028/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
