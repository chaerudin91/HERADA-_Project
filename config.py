import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '5e4c3d2b1a0f9e8c7b6a5d4c3e2f1a0b0f9e8c7d6b5a4bg43')
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'wajah_db'