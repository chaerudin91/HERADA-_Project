from flask import Flask
from .routes import main

def create_app():
    app = Flask(__name__)
    app.secret_key = 'inichatbotherada' 
    app.jinja_env.globals.update(enumerate=enumerate)
    app.register_blueprint(main)

    return app
