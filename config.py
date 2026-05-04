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

    # Season configuration — lottery period is date-based (not month-based)
    LOTTERY_START_MONTH = 4       # April
    LOTTERY_START_DAY = 1         # April 1
    LOTTERY_END_MONTH = 8         # August
    LOTTERY_END_DAY = 7           # August 7
    HUNTING_SEASON_MONTHS = [8, 9, 10, 11]  # Aug-Nov — cabin open, no reservations needed
    # Note: Hunting season starts Aug 8 (after lottery ends Aug 7)
    # Open booking months: Dec, Jan, Feb, Mar (and Aug 8+ is hunting, not bookable)
    MAX_RESERVATION_DAYS = 7
    PHASE1_PICK_DAYS = 5  # Days each member has to pick in Phase 1
    PHASE3_PICK_DAYS = 3  # Days each member has to pick in Phase 3
    PHASE2_DURATION_DAYS = 31  # How long Phase 2 stays open

    # Club configuration
    MAX_MEMBERS = 30  # Maximum allowed members

    # Email — Gmail SMTP for password recovery
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'silviesclubreservations@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'yknt weut oego ftdb')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'silviesclubreservations@gmail.com')

    # Password reset token expiry (seconds)
    RESET_TOKEN_EXPIRY = 3600  # 1 hour

