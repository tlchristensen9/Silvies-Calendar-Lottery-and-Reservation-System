"""Utility functions for the Silvies Club Reservation System."""

from datetime import datetime, date


def get_now():
    """Return the current datetime."""
    return datetime.utcnow()


def get_today():
    """Return the current date."""
    return get_now().date()
