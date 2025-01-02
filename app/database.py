from flask import g
import mysql.connector

def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Ganti dengan password Anda
            database='herada_db'  # Ganti dengan nama database Anda
        )
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


