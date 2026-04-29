"""Silvies Club Calendar Reservation System — Flask application factory."""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access the reservation system.'
login_manager.login_message_category = 'info'


def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if config_class:
        app.config.from_object(config_class)
    else:
        from config import Config
        app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.calendar import calendar_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(calendar_bp, url_prefix='/calendar')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Create tables on first request
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
