"""Application configuration for Silvies Club Reservation System."""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(basedir, 'instance', 'silvies.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Season configuration
    SEASON_MONTHS = [5, 6]  # May and June
    MAX_RESERVATION_DAYS = 7
    PHASE1_PICK_DAYS = 5  # Days each member has to pick in Phase 1
    PHASE3_PICK_DAYS = 3  # Days each member has to pick in Phase 3
    PHASE2_DURATION_DAYS = 31  # How long Phase 2 stays open

    # Club configuration
    MAX_MEMBERS = 30  # Maximum allowed members

    # Email (optional, configure for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@silviesclub.com')
