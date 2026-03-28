import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///PLACEMENT_PORTAL.sqlite3"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "placement_secret_key")
    app.debug = True
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = "main.login"
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    
    from .controllers import bp
    app.register_blueprint(bp)
    
    from .api import api_bp
    app.register_blueprint(api_bp)
    
    return app
