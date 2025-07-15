"""
Google Calendar Style Widget Module

This module contains a Google Calendar-inspired calendar widget for displaying
reservation periods in the Hunting Club Reservation System.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from calendar import monthrange

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QToolTip, QHeaderView, QTableWidget,
    QTableWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QColor, QBrush, QPen, QPainter

from utils.constants import (
    Colors, ReservationStatus, get_season_periods, get_period_id,
    format_date_range
)
from models.reservation import ReservationPeriod

class GoogleCalendarWidget(QWidget):
    """
    Google Calendar-style widget for displaying reservation periods.
    
    This widget mimics the look and feel of Google Calendar with a
    clean month view showing reservation periods as events.
    """
    
    period_clicked = pyqtSignal(str)  # Emits period_id when a period is clicked
    
    def __init__(self, parent=None):
        """Initialize the GoogleCalendarWidget."""
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.periods = []  # List of ReservationPeriod objects
        self.members = {}  # member_id -> member_data
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the Google Calendar-style UI."""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header section
        header_section = self.create_header_section()
        
        # Calendar container
        calendar_container = self.create_calendar_container()
        
        main_layout.addWidget(header_section)
        main_layout.addWidget(calendar_container)
        
        self.setLayout(main_layout)
        
        # Apply Google Calendar styling
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                font-family: "Segoe UI", "Google Sans", Arial, sans-serif;
            }
        """)
    
    def create_header_section(self) -> QWidget:
        """Create the header section with navigation and title."""
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 8, 24, 8)
        
        # Title
        self.title_label = QLabel("Hunting Season Calendar")
        self.title_label.setStyleSheet("""
            QLabel {
                color: #3c4043;
                font-size: 22px;
                font-weight: 400;
                padding: 8px 0px;
            }
        """)
        
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(8)
        
        self.prev_button = QPushButton("‹")
        self.next_button = QPushButton("›")
        
        nav_button_style = """
            QPushButton {
                border: none;
                background-color: transparent;
                color: #5f6368;
                font-size: 20px;
                font-weight: bold;
                width: 32px;
                height: 32px;
                border-radius: 16px;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
        """
        
        self.prev_button.setStyleSheet(nav_button_style)
        self.next_button.setStyleSheet(nav_button_style)
        
        self.prev_button.clicked.connect(self.previous_month)
        self.next_button.clicked.connect(self.next_month)
        
        # Month/Year label
        self.month_label = QLabel()
        self.month_label.setStyleSheet("""
            QLabel {
                color: #3c4043;
                font-size: 18px;
                font-weight: 500;
                padding: 8px 16px;
            }
        """)
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.month_label)
        nav_layout.addWidget(self.next_button)
        nav_layout.addStretch()
        
        layout.addWidget(self.title_label)
        layout.addStretch()
        layout.addLayout(nav_layout)
        
        return header
    
    def create_calendar_container(self) -> QWidget:
        """Create the main calendar grid container."""
        container = QWidget()
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 0, 24, 24)
        layout.setSpacing(0)
        
        # Day headers (S M T W T F S)
        day_headers = self.create_day_headers()
        layout.addWidget(day_headers)
        
        # Calendar grid
        self.calendar_table = QTableWidget(6, 7)  # 6 weeks x 7 days
        self.setup_calendar_table()
        
        layout.addWidget(self.calendar_table)
        
        return container
    
    def create_day_headers(self) -> QWidget:
        """Create the day of week headers."""
        headers_frame = QFrame()
        headers_frame.setFixedHeight(40)
        headers_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-bottom: 1px solid #e0e0e0;
            }
        """)
        
        layout = QGridLayout(headers_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        for i, day in enumerate(days):
            label = QLabel(day[0])  # Just first letter
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    color: #70757a;
                    font-size: 11px;
                    font-weight: 500;
                    padding: 8px;
                }
            """)
            layout.addWidget(label, 0, i)
        
        return headers_frame
    
    def setup_calendar_table(self):
        """Set up the calendar table widget."""
        # Remove headers
        self.calendar_table.horizontalHeader().setVisible(False)
        self.calendar_table.verticalHeader().setVisible(False)
        
        # Set uniform row/column sizes
        self.calendar_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.calendar_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Remove grid lines and selection
        self.calendar_table.setShowGrid(False)
        self.calendar_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.calendar_table.setFocusPolicy(Qt.NoFocus)
        
        # Set minimum height for rows
        for row in range(6):
            self.calendar_table.setRowHeight(row, 120)
        
        # Style the table
        self.calendar_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                border: none;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                border-right: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
                padding: 4px;
                vertical-align: top;
            }
            QTableWidget::item:selected {
                background-color: transparent;
            }
        """)
        
        # Connect cell click
        self.calendar_table.cellClicked.connect(self.on_cell_clicked)
    
    def load_periods(self, periods: List[Dict], members: Dict[int, Dict]):
        """
        Load reservation periods into the calendar.
        
        Args:
            periods (List[Dict]): List of reservation period dictionaries
            members (Dict[int, Dict]): Dictionary of member data by ID
        """
        try:
            self.members = members
            self.periods = []
            
            # Convert dictionaries to ReservationPeriod objects
            for period_data in periods:
                try:
                    period = ReservationPeriod.from_dict(period_data)
                    self.periods.append(period)
                except ValueError as e:
                    self.logger.warning(f"Invalid period data: {e}")
                    continue
            
            # Sort periods by start date
            self.periods.sort(key=lambda p: p.start_date)
            
            # Set initial view to first period's month or current month
            if self.periods:
                first_period = self.periods[0]
                self.current_month = first_period.start_date.month
                self.current_year = first_period.start_date.year
            
            # Populate the calendar
            self.populate_calendar()
            
            self.logger.info(f"Loaded {len(self.periods)} periods into Google Calendar widget")
            
        except Exception as e:
            self.logger.error(f"Error loading periods: {e}")
    
    def populate_calendar(self):
        """Populate the calendar with the current month's data."""
        # Update month label
        month_name = datetime(self.current_year, self.current_month, 1).strftime("%B %Y")
        self.month_label.setText(month_name)
        
        # Clear existing content
        self.calendar_table.clearContents()
        
        # Get first day of month and number of days
        first_day = datetime(self.current_year, self.current_month, 1)
        days_in_month = monthrange(self.current_year, self.current_month)[1]
        
        # Calculate starting position (Sunday = 0)
        start_weekday = first_day.weekday()
        if start_weekday == 6:  # Sunday
            start_pos = 0
        else:
            start_pos = start_weekday + 1
        
        # Fill in the calendar
        for day in range(1, days_in_month + 1):
            row = (start_pos + day - 1) // 7
            col = (start_pos + day - 1) % 7
            
            # Create day cell
            cell_widget = self.create_day_cell(day)
            self.calendar_table.setCellWidget(row, col, cell_widget)
    
    def create_day_cell(self, day: int) -> QWidget:
        """
        Create a day cell widget.
        
        Args:
            day (int): Day of the month
            
        Returns:
            QWidget: Day cell widget
        """
        cell = QFrame()
        cell.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
            }
            QFrame:hover {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignTop)
        
        # Day number
        day_label = QLabel(str(day))
        day_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Check if this is today
        today = datetime.now()
        if (self.current_year == today.year and 
            self.current_month == today.month and 
            day == today.day):
            day_label.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    background-color: #1a73e8;
                    border-radius: 12px;
                    font-weight: 500;
                    font-size: 12px;
                    padding: 4px 8px;
                    max-width: 24px;
                    max-height: 24px;
                }
            """)
        else:
            day_label.setStyleSheet("""
                QLabel {
                    color: #3c4043;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px;
                }
            """)
        
        layout.addWidget(day_label)
        
        # Add periods for this day
        current_date = datetime(self.current_year, self.current_month, day)
        day_periods = self.get_periods_for_date(current_date)
        
        for period in day_periods:
            event_widget = self.create_event_widget(period, current_date)
            layout.addWidget(event_widget)
        
        layout.addStretch()
        return cell
    
    def get_periods_for_date(self, date: datetime) -> List[ReservationPeriod]:
        """
        Get periods that include the given date.
        
        Args:
            date (datetime): Date to check
            
        Returns:
            List[ReservationPeriod]: Periods that include this date
        """
        periods_for_date = []
        
        for period in self.periods:
            # Check if date falls within period
            if period.start_date.date() <= date.date() <= period.end_date.date():
                periods_for_date.append(period)
        
        return periods_for_date
    
    def create_event_widget(self, period: ReservationPeriod, current_date: datetime) -> QWidget:
        """
        Create an event widget for a period.
        
        Args:
            period (ReservationPeriod): Reservation period
            current_date (datetime): Current date being displayed
            
        Returns:
            QWidget: Event widget
        """
        event = QPushButton()
        event.setCursor(Qt.PointingHandCursor)
        
        # Get status color
        status_colors = {
            ReservationStatus.AVAILABLE: "#34a853",      # Google Green
            ReservationStatus.RESERVED: "#ea4335",       # Google Red
            ReservationStatus.IN_LOTTERY: "#fbbc04",     # Google Yellow
            ReservationStatus.PENDING_CONFIRMATION: "#ff6d01",  # Google Orange
            ReservationStatus.EXPIRED: "#9aa0a6"         # Google Grey
        }
        
        color = status_colors.get(period.status, "#9aa0a6")
        
        # Determine event text
        if current_date.date() == period.start_date.date():
            # Show full period info on start date
            if period.member_id and period.member_id in self.members:
                member_name = self.members[period.member_id]['name']
                # Show just first name
                first_name = member_name.split()[0] if member_name else "Unknown"
                event_text = f"{first_name} ({period.get_status_display()})"
            else:
                event_text = period.get_status_display()
        else:
            # Show continuation indicator
            event_text = "▶ Continued"
        
        # Style the event
        event.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 10px;
                font-weight: 500;
                text-align: left;
                margin: 1px;
                min-height: 16px;
                max-height: 16px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.2)};
            }}
        """)
        
        event.setText(event_text)
        event.setToolTip(period.get_tooltip_text(
            self.members.get(period.member_id, {}).get('name') if period.member_id else None
        ))
        
        # Connect click event
        event.clicked.connect(lambda: self.period_clicked.emit(period.period_id))
        
        return event
    
    def darken_color(self, hex_color: str, factor: float = 0.1) -> str:
        """
        Darken a hex color by a given factor.
        
        Args:
            hex_color (str): Hex color string
            factor (float): Darkening factor (0.0 to 1.0)
            
        Returns:
            str: Darkened hex color
        """
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color
    
    def previous_month(self):
        """Navigate to previous month."""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        
        self.populate_calendar()
    
    def next_month(self):
        """Navigate to next month."""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        
        self.populate_calendar()
    
    def on_cell_clicked(self, row: int, column: int):
        """Handle cell click events."""
        # This could be used for creating new events or other interactions
        pass
    
    def update_period(self, period_data: Dict):
        """
        Update a specific period in the calendar.
        
        Args:
            period_data (Dict): Updated period data
        """
        try:
            period = ReservationPeriod.from_dict(period_data)
            
            # Update our internal list
            for i, existing_period in enumerate(self.periods):
                if existing_period.period_id == period.period_id:
                    self.periods[i] = period
                    break
            
            # Refresh the current month view
            self.populate_calendar()
            
            self.logger.debug(f"Updated period {period.period_id}")
                
        except ValueError as e:
            self.logger.error(f"Error updating period: {e}")
    
    def update_members(self, members: Dict[int, Dict]):
        """
        Update member data and refresh the calendar.
        
        Args:
            members (Dict[int, Dict]): Updated member data
        """
        self.members = members
        self.populate_calendar()
    
    def get_selected_periods(self) -> List[str]:
        """
        Get list of period IDs that can be selected for lottery.
        
        Returns:
            List[str]: List of available period IDs
        """
        available_periods = []
        
        for period in self.periods:
            if period.can_be_reserved():
                available_periods.append(period.period_id)
        
        return available_periods
    
    def highlight_period(self, period_id: str, highlight: bool = True):
        """
        Highlight or unhighlight a specific period.
        
        Args:
            period_id (str): Period ID to highlight
            highlight (bool): Whether to highlight or remove highlight
        """
        # For Google Calendar style, we refresh the view
        # The highlighting is handled by the event styling
        self.populate_calendar()
    
    def refresh_all_periods(self):
        """Refresh all periods to reflect current data."""
        self.populate_calendar()
    
    def get_status_counts(self) -> Dict[str, int]:
        """
        Get count of periods by status.
        
        Returns:
            Dict[str, int]: Status counts
        """
        counts = {}
        
        for period in self.periods:
            status = period.status
            counts[status] = counts.get(status, 0) + 1
        
        return counts
    
    def filter_periods_by_status(self, status: str, highlight: bool = True):
        """
        Filter periods by status (Google Calendar style doesn't need special highlighting).
        
        Args:
            status (str): Status to filter by
            highlight (bool): Whether to highlight or remove highlights
        """
        # In Google Calendar style, filtering would be done through other UI elements
        # For now, we just refresh the view
        self.populate_calendar()

# Alias for backwards compatibility
CalendarWidget = GoogleCalendarWidget