# App constants and configuration
"""
Application Constants and Configuration

This module contains all the constants and configuration settings
for the Hunting Club Reservation System.
"""

from datetime import datetime, timedelta
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Application Information
APP_NAME = "Hunting Club Reservation System"
APP_VERSION = "1.0.0"

# Season Configuration
SEASON_START_YEAR = 2025
SEASON_MONTHS = [5, 6, 7]  # May, June, July
RESERVATION_DAYS = 7  # 7-day periods
CONFIRMATION_DAYS = 5  # 5 days to confirm reservation

# Week Configuration
WEEK_START_DAY = 4  # Friday (0=Monday, 4=Friday)
WEEK_END_DAY = 3    # Thursday (0=Monday, 3=Thursday)

# File Paths
DATA_DIR = "data"
MEMBERS_FILE = "members.json"
RESERVATIONS_FILE = "reservations.json"
LOTTERY_HISTORY_FILE = "lottery_history.json"

# UI Colors (Hunting/Outdoor Theme)
class Colors:
    # Primary Colors
    PRIMARY_GREEN = QColor(76, 108, 73)      # Dark Forest Green
    SECONDARY_GREEN = QColor(103, 146, 99)   # Medium Forest Green
    ACCENT_GREEN = QColor(144, 184, 141)     # Light Forest Green
    
    # Earth Tones
    EARTH_BROWN = QColor(139, 117, 95)       # Dark Earth Brown
    LIGHT_BROWN = QColor(186, 157, 125)      # Light Earth Brown
    SAND = QColor(218, 203, 178)             # Sand Color
    
    # Status Colors
    AVAILABLE = QColor(144, 184, 141)        # Light Green
    RESERVED = QColor(139, 117, 95)          # Brown
    IN_LOTTERY = QColor(255, 193, 7)         # Amber
    PENDING_CONFIRMATION = QColor(255, 152, 0) # Orange
    EXPIRED = QColor(220, 53, 69)            # Red
    
    # UI Colors
    BACKGROUND = QColor(245, 245, 245)       # Light Gray
    CARD_BACKGROUND = QColor(255, 255, 255)  # White
    BORDER = QColor(200, 200, 200)           # Gray
    TEXT_PRIMARY = QColor(51, 51, 51)        # Dark Gray
    TEXT_SECONDARY = QColor(102, 102, 102)   # Medium Gray
    
    # Button Colors
    BUTTON_PRIMARY = PRIMARY_GREEN
    BUTTON_SECONDARY = SECONDARY_GREEN
    BUTTON_DANGER = QColor(220, 53, 69)      # Red
    BUTTON_WARNING = QColor(255, 193, 7)     # Amber

# Reservation Status
class ReservationStatus:
    AVAILABLE = "available"
    RESERVED = "reserved"
    IN_LOTTERY = "in_lottery"
    PENDING_CONFIRMATION = "pending_confirmation"
    EXPIRED = "expired"

# Member Configuration
TOTAL_MEMBERS = 21
DEFAULT_MEMBERS = [
    {"id": 1, "name": "John Smith", "email": "john.smith@email.com", "phone": "555-0101"},
    {"id": 2, "name": "Mike Johnson", "email": "mike.johnson@email.com", "phone": "555-0102"},
    {"id": 3, "name": "Robert Brown", "email": "robert.brown@email.com", "phone": "555-0103"},
    {"id": 4, "name": "William Davis", "email": "william.davis@email.com", "phone": "555-0104"},
    {"id": 5, "name": "James Miller", "email": "james.miller@email.com", "phone": "555-0105"},
    {"id": 6, "name": "David Wilson", "email": "david.wilson@email.com", "phone": "555-0106"},
    {"id": 7, "name": "Richard Moore", "email": "richard.moore@email.com", "phone": "555-0107"},
    {"id": 8, "name": "Joseph Taylor", "email": "joseph.taylor@email.com", "phone": "555-0108"},
    {"id": 9, "name": "Thomas Anderson", "email": "thomas.anderson@email.com", "phone": "555-0109"},
    {"id": 10, "name": "Charles Thomas", "email": "charles.thomas@email.com", "phone": "555-0110"},
    {"id": 11, "name": "Christopher Jackson", "email": "christopher.jackson@email.com", "phone": "555-0111"},
    {"id": 12, "name": "Daniel White", "email": "daniel.white@email.com", "phone": "555-0112"},
    {"id": 13, "name": "Matthew Harris", "email": "matthew.harris@email.com", "phone": "555-0113"},
    {"id": 14, "name": "Anthony Martin", "email": "anthony.martin@email.com", "phone": "555-0114"},
    {"id": 15, "name": "Mark Thompson", "email": "mark.thompson@email.com", "phone": "555-0115"},
    {"id": 16, "name": "Donald Garcia", "email": "donald.garcia@email.com", "phone": "555-0116"},
    {"id": 17, "name": "Steven Martinez", "email": "steven.martinez@email.com", "phone": "555-0117"},
    {"id": 18, "name": "Paul Rodriguez", "email": "paul.rodriguez@email.com", "phone": "555-0118"},
    {"id": 19, "name": "Andrew Lewis", "email": "andrew.lewis@email.com", "phone": "555-0119"},
    {"id": 20, "name": "Kenneth Walker", "email": "kenneth.walker@email.com", "phone": "555-0120"},
    {"id": 21, "name": "Joshua Hall", "email": "joshua.hall@email.com", "phone": "555-0121"}
]

# UI Styling
MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #f5f5f5;
    }
    QWidget {
        font-family: 'Arial', sans-serif;
        font-size: 10pt;
    }
    QPushButton {
        background-color: #4c6c49;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #679563;
    }
    QPushButton:pressed {
        background-color: #3d5a3b;
    }
    QPushButton:disabled {
        background-color: #cccccc;
        color: #666666;
    }
    QComboBox {
        padding: 6px;
        border: 1px solid #cccccc;
        border-radius: 4px;
        background-color: white;
    }
    QComboBox:focus {
        border: 2px solid #4c6c49;
    }
    QLabel {
        color: #333333;
    }
    QGroupBox {
        font-weight: bold;
        border: 2px solid #cccccc;
        border-radius: 8px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
"""

CALENDAR_WIDGET_STYLE = """
    QWidget {
        background-color: white;
        border: 1px solid #cccccc;
        border-radius: 4px;
    }
"""

# Dialog Sizes
DIALOG_MIN_WIDTH = 400
DIALOG_MIN_HEIGHT = 300
MAIN_WINDOW_MIN_WIDTH = 1000
MAIN_WINDOW_MIN_HEIGHT = 700

# Tooltip Styles
TOOLTIP_STYLE = """
    QToolTip {
        background-color: #4c6c49;
        color: white;
        border: 1px solid #3d5a3b;
        padding: 5px;
        border-radius: 3px;
        font-size: 9pt;
    }
"""

def get_season_periods(year=SEASON_START_YEAR):
    """
    Generate all reservation periods for the hunting season.
    
    Args:
        year (int): The year for the season
        
    Returns:
        list: List of (start_date, end_date) tuples for each period
    """
    periods = []
    
    # Start with the first Friday of May
    start_date = datetime(year, 5, 1)
    
    # Find the first Friday
    days_ahead = WEEK_START_DAY - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    start_date += timedelta(days_ahead)
    
    # Generate periods until the end of July
    while start_date.month <= 7:
        end_date = start_date + timedelta(days=RESERVATION_DAYS-1)
        
        # Only include periods that are primarily within the season
        if start_date.month in SEASON_MONTHS:
            periods.append((start_date, end_date))
        
        start_date += timedelta(days=RESERVATION_DAYS)
    
    return periods

def get_period_id(start_date, end_date):
    """
    Generate a unique identifier for a reservation period.
    
    Args:
        start_date (datetime): Period start date
        end_date (datetime): Period end date
        
    Returns:
        str: Unique period identifier
    """
    return f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

def format_date_range(start_date, end_date):
    """
    Format a date range for display.
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        str: Formatted date range
    """
    if start_date.month == end_date.month:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%d, %Y')}"
    else:
        return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"