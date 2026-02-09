import os
from flask import Flask
from .models import db

def create_app():
    app = Flask(__name__, template_folder="../templates")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///PLACEMENT_PORTAL.sqlite3"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "placement_secret_key")
    app.debug = True
    db.init_app(app)
    
    
    from .controllers import bp
    app.register_blueprint(bp)
    return app
