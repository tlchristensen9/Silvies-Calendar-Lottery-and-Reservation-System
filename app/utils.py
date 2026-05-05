"""Utility functions for the Silvies Club Reservation System."""

from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask import current_app


def _tz():
    """Return the configured timezone (falls back to US/Pacific)."""
    try:
        tz_name = current_app.config.get('TIMEZONE', 'US/Pacific')
    except RuntimeError:
        # Outside application context (e.g., during startup)
        tz_name = 'US/Pacific'
    return ZoneInfo(tz_name)


def get_now():
    """Return the current datetime in the configured local timezone (naive)."""
    # Return naive datetime so SQLite round-trips are consistent.
    return datetime.now(_tz()).replace(tzinfo=None)


def get_today():
    """Return the current date in the configured local timezone."""
    return get_now().date()
