"""Utility functions for the Silvies Club Reservation System.

Provides time-travel support: get_now() and get_today() check for an admin-set
time override before falling back to real system time.  When DEBUG_TIME_TRAVEL
is False (the default), these are simple pass-throughs to the standard library.
"""

from datetime import datetime, date


def get_now():
    """Return the current datetime, respecting any admin time override."""
    from flask import current_app
    if not current_app.config.get('DEBUG_TIME_TRAVEL', False):
        return datetime.utcnow()
    from app.models import AppSetting
    override = AppSetting.get('time_override')
    if override:
        try:
            return datetime.fromisoformat(override)
        except (ValueError, TypeError):
            pass
    return datetime.utcnow()


def get_today():
    """Return the current date, respecting any admin time override."""
    return get_now().date()
