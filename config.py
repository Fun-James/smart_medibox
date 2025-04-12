import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:123456a@localhost:3306/medicine_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.urandom(24)
