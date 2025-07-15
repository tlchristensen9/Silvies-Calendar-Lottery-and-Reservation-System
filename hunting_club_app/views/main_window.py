"""
Main Window Module

This module contains the main application window for the Hunting Club
Reservation System. It provides the primary user interface for managing
reservations and lotteries.
"""

import logging
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QGroupBox, QFrame, QSplitter,
    QMenuBar, QMenu, QAction, QStatusBar, QMessageBox, QToolBar,
    QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QKeySequence

from utils.constants import (
    APP_NAME, Colors, ReservationStatus, MAIN_WINDOW_MIN_WIDTH,
    MAIN_WINDOW_MIN_HEIGHT, MAIN_WINDOW_STYLE
)
from views.calendar_widget import CalendarWidget
from views.dialogs import (
    LotteryDialog, LotteryDrawDialog, MemberStatsDialog,
    ConfirmationDialog, AboutDialog
)

class MainWindow(QMainWindow):
    """
    Main application window for the Hunting Club Reservation System.
    
    This window provides the primary interface for viewing reservations,
    managing lotteries, and accessing system features.
    """
    
    # Signals
    member_changed = pyqtSignal(str)  # Emits member name when selection changes
    lottery_requested = pyqtSignal(list, list)  # Emits available periods and members
    period_selected = pyqtSignal(str)  # Emits period_id when period is selected
    refresh_requested = pyqtSignal()  # Emits when data refresh is needed
    
    def __init__(self, parent=None):
        """Initialize the MainWindow."""
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        self.current_member = None
        self.members_data = {}
        self.reservations_data = []
        self.lottery_history_data = []
        
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_status_bar()
        
        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_requested.emit)
        self.update_timer.start(30000)  # Refresh every 30 seconds
    
    def setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel (controls)
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(300)
        
        # Right panel (calendar)
        right_panel = self.create_right_panel()
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        main_layout.addWidget(splitter)
        
        # Apply main window style
        self.setStyleSheet(MAIN_WINDOW_STYLE)
    
    def create_left_panel(self) -> QWidget:
        """
        Create the left control panel.
        
        Returns:
            QWidget: Left panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Member selection
        member_group = self.create_member_selection()
        
        # System status
        status_group = self.create_status_display()
        
        # Actions
        actions_group = self.create_actions_panel()
        
        # Quick stats
        stats_group = self.create_quick_stats()
        
        layout.addWidget(member_group)
        layout.addWidget(status_group)
        layout.addWidget(actions_group)
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return panel
    
    def create_member_selection(self) -> QGroupBox:
        """
        Create the member selection group.
        
        Returns:
            QGroupBox: Member selection widget
        """
        group = QGroupBox("Member Selection")
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select a member to view as:")
        instructions.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; margin-bottom: 5px;")
        
        # Member dropdown
        self.member_combo = QComboBox()
        self.member_combo.currentTextChanged.connect(self.on_member_changed)
        self.member_combo.setStyleSheet("QComboBox { padding: 8px; }")
        
        # Member info display
        self.member_info = QLabel("No member selected")
        self.member_info.setWordWrap(True)
        self.member_info.setStyleSheet(f"""
            background-color: {Colors.CARD_BACKGROUND.name()};
            border: 1px solid {Colors.BORDER.name()};
            border-radius: 4px;
            padding: 10px;
            color: {Colors.TEXT_SECONDARY.name()};
        """)
        self.member_info.setMinimumHeight(60)
        
        layout.addWidget(instructions)
        layout.addWidget(self.member_combo)
        layout.addWidget(self.member_info)
        
        group.setLayout(layout)
        return group
    
    def create_status_display(self) -> QGroupBox:
        """
        Create the system status display.
        
        Returns:
            QGroupBox: Status display widget
        """
        group = QGroupBox("System Status")
        layout = QVBoxLayout()
        
        # Status items
        self.status_items = {}
        
        status_labels = [
            ("available", "Available Periods", Colors.AVAILABLE),
            ("reserved", "Reserved Periods", Colors.RESERVED),
            ("lottery", "In Lottery", Colors.IN_LOTTERY),
            ("pending", "Pending Confirmation", Colors.PENDING_CONFIRMATION),
            ("expired", "Expired", Colors.EXPIRED)
        ]
        
        for key, label, color in status_labels:
            item_layout = QHBoxLayout()
            
            # Color indicator
            color_box = QLabel()
            color_box.setFixedSize(20, 15)
            color_box.setStyleSheet(f"""
                background-color: {color.name()};
                border: 1px solid {Colors.BORDER.name()};
                border-radius: 3px;
            """)
            
            # Label
            text_label = QLabel(label)
            text_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY.name()};")
            
            # Count
            count_label = QLabel("0")
            count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; font-weight: bold;")
            count_label.setAlignment(Qt.AlignRight)
            
            self.status_items[key] = count_label
            
            item_layout.addWidget(color_box)
            item_layout.addWidget(text_label)
            item_layout.addStretch()
            item_layout.addWidget(count_label)
            
            layout.addLayout(item_layout)
        
        group.setLayout(layout)
        return group
    
    def create_actions_panel(self) -> QGroupBox:
        """
        Create the actions panel.
        
        Returns:
            QGroupBox: Actions panel widget
        """
        group = QGroupBox("Actions")
        layout = QVBoxLayout()
        
        # New lottery button
        self.new_lottery_btn = QPushButton("Create New Lottery")
        self.new_lottery_btn.clicked.connect(self.create_new_lottery)
        self.new_lottery_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_PRIMARY.name()};
                color: white;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.BUTTON_SECONDARY.name()};
            }}
        """)
        
        # View statistics button
        self.stats_btn = QPushButton("View Statistics")
        self.stats_btn.clicked.connect(self.show_statistics)
        
        # Refresh data button
        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)
        
        # Export data button
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        
        layout.addWidget(self.new_lottery_btn)
        layout.addWidget(self.stats_btn)
        layout.addWidget(self.refresh_btn)
        layout.addWidget(self.export_btn)
        
        group.setLayout(layout)
        return group
    
    def create_quick_stats(self) -> QGroupBox:
        """
        Create the quick statistics display.
        
        Returns:
            QGroupBox: Quick stats widget
        """
        group = QGroupBox("Quick Stats")
        layout = QVBoxLayout()
        
        # Stats labels
        self.total_lotteries_label = QLabel("Total Lotteries: 0")
        self.active_reservations_label = QLabel("Active Reservations: 0")
        self.participation_rate_label = QLabel("Participation Rate: 0%")
        
        stats_labels = [
            self.total_lotteries_label,
            self.active_reservations_label,
            self.participation_rate_label
        ]
        
        for label in stats_labels:
            label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY.name()}; margin: 2px;")
            layout.addWidget(label)
        
        group.setLayout(layout)
        return group
    
    def create_right_panel(self) -> QWidget:
        """
        Create the right panel with calendar.
        
        Returns:
            QWidget: Right panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Calendar widget
        self.calendar_widget = CalendarWidget()
        self.calendar_widget.period_clicked.connect(self.on_period_clicked)
        
        layout.addWidget(self.calendar_widget)
        
        return panel
    
    def setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Export action
        export_action = QAction("&Export Data...", self)
        export_action.setShortcut(QKeySequence.Save)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Lottery menu
        lottery_menu = menubar.addMenu("&Lottery")
        
        # New lottery action
        new_lottery_action = QAction("&New Lottery...", self)
        new_lottery_action.setShortcut(QKeySequence.New)
        new_lottery_action.triggered.connect(self.create_new_lottery)
        lottery_menu.addAction(new_lottery_action)
        
        # View statistics action
        stats_action = QAction("&Statistics...", self)
        stats_action.triggered.connect(self.show_statistics)
        lottery_menu.addAction(stats_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # Filter actions
        filter_menu = view_menu.addMenu("&Filter Periods")
        
        self.filter_actions = {}
        filter_items = [
            ("available", "Show &Available", ReservationStatus.AVAILABLE),
            ("reserved", "Show &Reserved", ReservationStatus.RESERVED),
            ("lottery", "Show &In Lottery", ReservationStatus.IN_LOTTERY),
            ("pending", "Show &Pending", ReservationStatus.PENDING_CONFIRMATION),
            ("expired", "Show &Expired", ReservationStatus.EXPIRED)
        ]
        
        for key, text, status in filter_items:
            action = QAction(text, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, s=status: self.filter_periods(s, checked))
            filter_menu.addAction(action)
            self.filter_actions[key] = action
        
        filter_menu.addSeparator()
        
        clear_filters_action = QAction("&Clear All Filters", self)
        clear_filters_action.triggered.connect(self.clear_filters)
        filter_menu.addAction(clear_filters_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About...", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # New lottery action
        new_lottery_action = toolbar.addAction("New Lottery")
        new_lottery_action.triggered.connect(self.create_new_lottery)
        
        # Statistics action
        stats_action = toolbar.addAction("Statistics")
        stats_action.triggered.connect(self.show_statistics)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = toolbar.addAction("Refresh")
        refresh_action.triggered.connect(self.refresh_requested.emit)
        
        # Export action
        export_action = toolbar.addAction("Export")
        export_action.triggered.connect(self.export_data)
    
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status labels
        self.status_message = QLabel("Ready")
        self.member_status = QLabel("No member selected")
        self.data_status = QLabel("Data loaded")
        
        self.status_bar.addWidget(self.status_message)
        self.status_bar.addPermanentWidget(self.member_status)
        self.status_bar.addPermanentWidget(self.data_status)
        
        # Update status bar style
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {Colors.CARD_BACKGROUND.name()};
                border-top: 1px solid {Colors.BORDER.name()};
                color: {Colors.TEXT_SECONDARY.name()};
            }}
        """)
    
    def load_members(self, members: List[Dict]):
        """
        Load members into the interface.
        
        Args:
            members (List[Dict]): List of member data
        """
        self.members_data = {m['id']: m for m in members}
        
        # Update member combo box
        self.member_combo.clear()
        self.member_combo.addItem("Select a member...", None)
        
        for member in sorted(members, key=lambda m: m['name']):
            display_text = f"{member['name']} (#{member['id']})"
            self.member_combo.addItem(display_text, member['id'])
        
        self.logger.info(f"Loaded {len(members)} members")
    
    def load_reservations(self, reservations: List[Dict]):
        """
        Load reservations data.
        
        Args:
            reservations (List[Dict]): List of reservation data
        """
        self.reservations_data = reservations
        
        # Update calendar
        self.calendar_widget.load_periods(reservations, self.members_data)
        
        # Update status display
        self.update_status_display()
        
        self.logger.info(f"Loaded {len(reservations)} reservations")
    
    def load_lottery_history(self, lottery_history: List[Dict]):
        """
        Load lottery history data.
        
        Args:
            lottery_history (List[Dict]): List of lottery records
        """
        self.lottery_history_data = lottery_history
        
        # Update quick stats
        self.update_quick_stats()
        
        self.logger.info(f"Loaded {len(lottery_history)} lottery records")
    
    def update_status_display(self):
        """Update the status display with current reservation counts."""
        from models.reservation import ReservationManager
        
        # Count reservations by status
        status_mapping = {
            'available': ReservationStatus.AVAILABLE,
            'reserved': ReservationStatus.RESERVED,
            'lottery': ReservationStatus.IN_LOTTERY,
            'pending': ReservationStatus.PENDING_CONFIRMATION,
            'expired': ReservationStatus.EXPIRED
        }
        
        for key, status in status_mapping.items():
            count = len(ReservationManager.get_reservations_by_status(
                self.reservations_data, status
            ))
            self.status_items[key].setText(str(count))
    
    def update_quick_stats(self):
        """Update the quick statistics display."""
        from models.lottery import LotteryManager
        from models.reservation import ReservationManager
        
        # Total lotteries
        total_lotteries = len(self.lottery_history_data)
        self.total_lotteries_label.setText(f"Total Lotteries: {total_lotteries}")
        
        # Active reservations (reserved + pending)
        reserved_count = len(ReservationManager.get_reservations_by_status(
            self.reservations_data, ReservationStatus.RESERVED
        ))
        pending_count = len(ReservationManager.get_reservations_by_status(
            self.reservations_data, ReservationStatus.PENDING_CONFIRMATION
        ))
        active_count = reserved_count + pending_count
        self.active_reservations_label.setText(f"Active Reservations: {active_count}")
        
        # Participation rate (members who have participated in lotteries)
        if self.members_data and self.lottery_history_data:
            member_ids = set(self.members_data.keys())
            participated_members = set()
            
            for lottery in self.lottery_history_data:
                participants = lottery.get('participants', [])
                participated_members.update(participants)
            
            participation_rate = (len(participated_members) / len(member_ids)) * 100
            self.participation_rate_label.setText(f"Participation Rate: {participation_rate:.1f}%")
        else:
            self.participation_rate_label.setText("Participation Rate: 0%")
    
    def on_member_changed(self, text: str):
        """
        Handle member selection change.
        
        Args:
            text (str): Selected member text
        """
        member_id = self.member_combo.currentData()
        
        if member_id and member_id in self.members_data:
            member = self.members_data[member_id]
            self.current_member = member
            
            # Update member info display
            info_text = f"Name: {member['name']}\n"
            info_text += f"Email: {member['email']}\n"
            info_text += f"Phone: {member['phone']}"
            self.member_info.setText(info_text)
            
            # Update status bar
            self.member_status.setText(f"Viewing as: {member['name']}")
            
            # Emit signal
            self.member_changed.emit(member['name'])
            
        else:
            self.current_member = None
            self.member_info.setText("No member selected")
            self.member_status.setText("No member selected")
    
    def on_period_clicked(self, period_id: str):
        """
        Handle period click from calendar.
        
        Args:
            period_id (str): ID of the clicked period
        """
        self.period_selected.emit(period_id)
        self.show_period_details(period_id)
    
    def show_period_details(self, period_id: str):
        """
        Show details for a specific period.
        
        Args:
            period_id (str): Period ID to show details for
        """
        # Find the period data
        period_data = None
        for reservation in self.reservations_data:
            if reservation.get('period_id') == period_id:
                period_data = reservation
                break
        
        if not period_data:
            return
        
        try:
            from models.reservation import ReservationPeriod
            period = ReservationPeriod.from_dict(period_data)
            
            # Build details message
            message = f"Period: {period.get_display_text()}\n"
            message += f"Status: {period.get_status_display()}\n"
            
            if period.member_id and period.member_id in self.members_data:
                member = self.members_data[period.member_id]
                message += f"Reserved by: {member['name']} (#{member['id']})\n"
            
            if period.confirmed_date:
                message += f"Confirmed: {period.confirmed_date.strftime('%Y-%m-%d %H:%M')}\n"
            
            if period.lottery_id:
                message += f"Lottery ID: {period.lottery_id}\n"
            
            # Show message box
            QMessageBox.information(self, "Period Details", message)
            
        except Exception as e:
            self.logger.error(f"Error showing period details: {e}")
    
    def create_new_lottery(self):
        """Create a new lottery."""
        from models.reservation import ReservationManager
        
        # Get available periods
        available_periods = ReservationManager.get_reservations_by_status(
            self.reservations_data, ReservationStatus.AVAILABLE
        )
        
        if not available_periods:
            QMessageBox.information(
                self, "No Available Periods",
                "There are no available periods for lottery."
            )
            return
        
        # Get all members
        members_list = list(self.members_data.values())
        
        # Show lottery dialog
        dialog = LotteryDialog(available_periods, members_list, self)
        dialog.lottery_created.connect(self.on_lottery_created)
        dialog.exec_()
    
    def on_lottery_created(self, lottery_data: Dict):
        """
        Handle lottery creation.
        
        Args:
            lottery_data (Dict): Created lottery data
        """
        # Emit signal to controller
        self.lottery_requested.emit([lottery_data], list(self.members_data.values()))
        
        # Show success message
        QMessageBox.information(
            self, "Lottery Created",
            f"Lottery for period {lottery_data['period_id']} has been created.\n"
            f"Participants: {len(lottery_data['participants'])}"
        )
    
    def show_statistics(self):
        """Show the statistics dialog."""
        dialog = MemberStatsDialog(
            list(self.members_data.values()),
            self.lottery_history_data,
            self.reservations_data,
            self
        )
        dialog.exec_()
    
    def export_data(self):
        """Export data to files."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            import os
            
            # Select export directory
            export_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory"
            )
            
            if not export_dir:
                return
            
            # Export files
            export_files = [
                ("members.json", list(self.members_data.values())),
                ("reservations.json", self.reservations_data),
                ("lottery_history.json", self.lottery_history_data)
            ]
            
            for filename, data in export_files:
                filepath = os.path.join(export_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, "Export Complete",
                f"Data exported successfully to:\n{export_dir}"
            )
            
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to export data:\n{e}"
            )
    
    def filter_periods(self, status: str, show: bool):
        """
        Filter periods by status.
        
        Args:
            status (str): Status to filter
            show (bool): Whether to show or hide the status
        """
        self.calendar_widget.filter_periods_by_status(status, show)
    
    def clear_filters(self):
        """Clear all period filters."""
        # Uncheck all filter actions
        for action in self.filter_actions.values():
            action.setChecked(False)
        
        # Reset calendar highlighting
        self.calendar_widget.refresh_all_periods()
    
    def show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def update_data(self, members: List[Dict], reservations: List[Dict], 
                   lottery_history: List[Dict]):
        """
        Update all data in the interface.
        
        Args:
            members (List[Dict]): Updated member data
            reservations (List[Dict]): Updated reservation data
            lottery_history (List[Dict]): Updated lottery history
        """
        self.load_members(members)
        self.load_reservations(reservations)
        self.load_lottery_history(lottery_history)
        
        # Update status message
        self.status_message.setText("Data updated")
        self.data_status.setText("Data current")
        
        # Clear status message after 3 seconds
        QTimer.singleShot(3000, lambda: self.status_message.setText("Ready"))
    
    def show_message(self, title: str, message: str, message_type: str = "info"):
        """
        Show a message to the user.
        
        Args:
            title (str): Message title
            message (str): Message text
            message_type (str): Type of message ('info', 'warning', 'error')
        """
        if message_type == "warning":
            QMessageBox.warning(self, title, message)
        elif message_type == "error":
            QMessageBox.critical(self, title, message)
        else:
            QMessageBox.information(self, title, message)
    
    def closeEvent(self, event):
        """Handle window close event."""
        reply = QMessageBox.question(
            self, "Confirm Exit",
            "Are you sure you want to exit the application?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop the update timer
            self.update_timer.stop()
            event.accept()
        else:
            event.ignore()