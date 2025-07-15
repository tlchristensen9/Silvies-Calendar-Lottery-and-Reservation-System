# Various dialog windows
"""
Dialog Windows Module

This module contains various dialog windows for the Hunting Club
Reservation System, including lottery management and member selection.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QTextEdit, QCheckBox, QGroupBox, QScrollArea, QFrame,
    QMessageBox, QProgressBar, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon

from utils.constants import (
    Colors, ReservationStatus, DIALOG_MIN_WIDTH, DIALOG_MIN_HEIGHT,
    format_date_range
)
from models.lottery import LotteryRound
from models.reservation import ReservationPeriod

class LotteryDialog(QDialog):
    """
    Dialog for managing lottery rounds.
    
    This dialog allows administrators to create new lottery rounds,
    add participants, and run the lottery draw.
    """
    
    lottery_created = pyqtSignal(dict)  # Emits lottery data when created
    
    def __init__(self, available_periods: List[Dict], members: List[Dict], parent=None):
        """
        Initialize the LotteryDialog.
        
        Args:
            available_periods (List[Dict]): List of available periods
            members (List[Dict]): List of all members
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.available_periods = available_periods
        self.members = members
        self.selected_participants = set()
        self.selected_period = None
        
        self.logger = logging.getLogger(__name__)
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Create New Lottery")
        self.setMinimumSize(DIALOG_MIN_WIDTH + 200, DIALOG_MIN_HEIGHT + 200)
        self.resize(700, 600)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Create New Lottery Round")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_GREEN.name()}; margin-bottom: 15px;")
        
        # Period selection
        period_group = self.create_period_selection()
        
        # Participant selection
        participant_group = self.create_participant_selection()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.create_button = QPushButton("Create Lottery")
        self.create_button.clicked.connect(self.create_lottery)
        self.create_button.setEnabled(False)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.create_button)
        
        # Add to main layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(period_group)
        main_layout.addWidget(participant_group)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Apply styles
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND.name()};
            }}
            QPushButton {{
                min-width: 100px;
                padding: 8px;
            }}
            QGroupBox {{
                font-weight: bold;
                padding-top: 15px;
            }}
        """)
    
    def create_period_selection(self) -> QGroupBox:
        """
        Create the period selection group.
        
        Returns:
            QGroupBox: Period selection widget
        """
        group = QGroupBox("Select Reservation Period")
        layout = QVBoxLayout()
        
        if not self.available_periods:
            no_periods_label = QLabel("No available periods for lottery")
            no_periods_label.setStyleSheet("color: red; font-style: italic;")
            layout.addWidget(no_periods_label)
        else:
            self.period_combo = QComboBox()
            self.period_combo.currentTextChanged.connect(self.on_period_changed)
            layout.addWidget(self.period_combo)
            
            # Period details
            self.period_details = QLabel()
            self.period_details.setWordWrap(True)
            self.period_details.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; margin-top: 10px;")
            layout.addWidget(self.period_details)
        
        group.setLayout(layout)
        return group
    
    def create_participant_selection(self) -> QGroupBox:
        """
        Create the participant selection group.
        
        Returns:
            QGroupBox: Participant selection widget
        """
        group = QGroupBox("Select Participants")
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select members to participate in this lottery:")
        instructions.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Member selection area
        selection_layout = QHBoxLayout()
        
        # Available members list
        available_layout = QVBoxLayout()
        available_label = QLabel("Available Members:")
        available_label.setStyleSheet("font-weight: bold;")
        
        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        
        available_layout.addWidget(available_label)
        available_layout.addWidget(self.available_list)
        
        # Control buttons
        control_layout = QVBoxLayout()
        control_layout.addStretch()
        
        self.add_button = QPushButton("Add →")
        self.add_button.clicked.connect(self.add_participants)
        
        self.remove_button = QPushButton("← Remove")
        self.remove_button.clicked.connect(self.remove_participants)
        
        self.add_all_button = QPushButton("Add All →")
        self.add_all_button.clicked.connect(self.add_all_participants)
        
        self.remove_all_button = QPushButton("← Remove All")
        self.remove_all_button.clicked.connect(self.remove_all_participants)
        
        control_layout.addWidget(self.add_button)
        control_layout.addWidget(self.remove_button)
        control_layout.addWidget(self.add_all_button)
        control_layout.addWidget(self.remove_all_button)
        control_layout.addStretch()
        
        # Selected participants list
        selected_layout = QVBoxLayout()
        selected_label = QLabel("Selected Participants:")
        selected_label.setStyleSheet("font-weight: bold;")
        
        self.selected_list = QListWidget()
        
        selected_layout.addWidget(selected_label)
        selected_layout.addWidget(self.selected_list)
        
        # Add to selection layout
        selection_layout.addLayout(available_layout)
        selection_layout.addLayout(control_layout)
        selection_layout.addLayout(selected_layout)
        
        layout.addWidget(instructions)
        layout.addLayout(selection_layout)
        
        # Participant count
        self.participant_count_label = QLabel("Participants selected: 0")
        self.participant_count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; margin-top: 10px;")
        layout.addWidget(self.participant_count_label)
        
        group.setLayout(layout)
        return group
    
    def load_data(self):
        """Load data into the dialog controls."""
        # Load periods
        if hasattr(self, 'period_combo') and self.available_periods:
            for period_data in self.available_periods:
                try:
                    period = ReservationPeriod.from_dict(period_data)
                    display_text = period.get_display_text()
                    self.period_combo.addItem(display_text, period_data)
                except ValueError:
                    continue
        
        # Load members
        for member in self.members:
            item = QListWidgetItem(f"{member['name']} (#{member['id']})")
            item.setData(Qt.UserRole, member['id'])
            self.available_list.addItem(item)
    
    def on_period_changed(self):
        """Handle period selection change."""
        current_index = self.period_combo.currentIndex()
        if current_index >= 0:
            period_data = self.period_combo.itemData(current_index)
            if period_data:
                try:
                    period = ReservationPeriod.from_dict(period_data)
                    self.selected_period = period_data
                    
                    details = f"Period: {period.get_display_text()}\n"
                    details += f"Status: {period.get_status_display()}"
                    
                    self.period_details.setText(details)
                    self.update_create_button()
                    
                except ValueError as e:
                    self.period_details.setText(f"Error: {e}")
    
    def add_participants(self):
        """Add selected participants to the lottery."""
        selected_items = self.available_list.selectedItems()
        
        for item in selected_items:
            member_id = item.data(Qt.UserRole)
            if member_id not in self.selected_participants:
                self.selected_participants.add(member_id)
                
                # Add to selected list
                new_item = QListWidgetItem(item.text())
                new_item.setData(Qt.UserRole, member_id)
                self.selected_list.addItem(new_item)
                
                # Remove from available list
                row = self.available_list.row(item)
                self.available_list.takeItem(row)
        
        self.update_participant_count()
        self.update_create_button()
    
    def remove_participants(self):
        """Remove selected participants from the lottery."""
        selected_items = self.selected_list.selectedItems()
        
        for item in selected_items:
            member_id = item.data(Qt.UserRole)
            if member_id in self.selected_participants:
                self.selected_participants.remove(member_id)
                
                # Add back to available list
                new_item = QListWidgetItem(item.text())
                new_item.setData(Qt.UserRole, member_id)
                self.available_list.addItem(new_item)
                
                # Remove from selected list
                row = self.selected_list.row(item)
                self.selected_list.takeItem(row)
        
        self.update_participant_count()
        self.update_create_button()
    
    def add_all_participants(self):
        """Add all available participants to the lottery."""
        while self.available_list.count() > 0:
            item = self.available_list.item(0)
            member_id = item.data(Qt.UserRole)
            
            self.selected_participants.add(member_id)
            
            # Move to selected list
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.UserRole, member_id)
            self.selected_list.addItem(new_item)
            
            # Remove from available list
            self.available_list.takeItem(0)
        
        self.update_participant_count()
        self.update_create_button()
    
    def remove_all_participants(self):
        """Remove all participants from the lottery."""
        while self.selected_list.count() > 0:
            item = self.selected_list.item(0)
            member_id = item.data(Qt.UserRole)
            
            self.selected_participants.remove(member_id)
            
            # Move back to available list
            new_item = QListWidgetItem(item.text())
            new_item.setData(Qt.UserRole, member_id)
            self.available_list.addItem(new_item)
            
            # Remove from selected list
            self.selected_list.takeItem(0)
        
        self.update_participant_count()
        self.update_create_button()
    
    def update_participant_count(self):
        """Update the participant count label."""
        count = len(self.selected_participants)
        self.participant_count_label.setText(f"Participants selected: {count}")
    
    def update_create_button(self):
        """Update the create button enabled state."""
        enabled = (self.selected_period is not None and 
                  len(self.selected_participants) > 0)
        self.create_button.setEnabled(enabled)
    
    def create_lottery(self):
        """Create the lottery and emit the data."""
        if not self.selected_period or not self.selected_participants:
            QMessageBox.warning(self, "Invalid Selection", 
                              "Please select a period and at least one participant.")
            return
        
        try:
            # Create lottery round
            lottery = LotteryRound(
                lottery_id="",  # Will be auto-generated
                period_id=self.selected_period['period_id'],
                participants=list(self.selected_participants)
            )
            
            # Emit the lottery data
            self.lottery_created.emit(lottery.to_dict())
            
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error creating lottery: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create lottery:\n{e}")

class LotteryDrawDialog(QDialog):
    """
    Dialog for running a lottery draw.
    
    This dialog shows the lottery participants and runs an animated
    draw to select the winner.
    """
    
    def __init__(self, lottery_data: Dict, members: Dict[int, Dict], parent=None):
        """
        Initialize the LotteryDrawDialog.
        
        Args:
            lottery_data (Dict): Lottery data
            members (Dict[int, Dict]): Member data by ID
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.lottery_data = lottery_data
        self.members = members
        self.winner_id = None
        
        self.setup_ui()
        self.load_lottery_info()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Lottery Draw")
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Lottery Draw")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_GREEN.name()}; margin-bottom: 20px;")
        
        # Lottery info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY.name()}; margin-bottom: 15px;")
        
        # Participants list
        participants_group = QGroupBox("Participants")
        participants_layout = QVBoxLayout()
        
        self.participants_list = QListWidget()
        self.participants_list.setMaximumHeight(150)
        participants_layout.addWidget(self.participants_list)
        
        participants_group.setLayout(participants_layout)
        
        # Draw area
        draw_group = QGroupBox("Draw Results")
        draw_layout = QVBoxLayout()
        
        self.draw_display = QLabel("Click 'Draw Winner' to start the lottery")
        self.draw_display.setAlignment(Qt.AlignCenter)
        self.draw_display.setStyleSheet(f"""
            background-color: {Colors.CARD_BACKGROUND.name()};
            border: 2px solid {Colors.BORDER.name()};
            border-radius: 8px;
            padding: 20px;
            font-size: 14pt;
            font-weight: bold;
            color: {Colors.TEXT_PRIMARY.name()};
        """)
        self.draw_display.setMinimumHeight(100)
        
        # Progress bar for animation
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        draw_layout.addWidget(self.draw_display)
        draw_layout.addWidget(self.progress_bar)
        
        draw_group.setLayout(draw_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.draw_button = QPushButton("Draw Winner")
        self.draw_button.clicked.connect(self.start_draw)
        self.draw_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BUTTON_PRIMARY.name()};
                color: white;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.BUTTON_SECONDARY.name()};
            }}
        """)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        self.close_button.setEnabled(False)
        
        button_layout.addStretch()
        button_layout.addWidget(self.draw_button)
        button_layout.addWidget(self.close_button)
        
        # Add to main layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.info_label)
        main_layout.addWidget(participants_group)
        main_layout.addWidget(draw_group)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Timer for animation
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_draw)
        self.animation_step = 0
        self.animation_duration = 30  # Number of animation steps
    
    def load_lottery_info(self):
        """Load lottery information into the dialog."""
        try:
            lottery = LotteryRound.from_dict(self.lottery_data)
            
            # Set lottery info
            info_text = f"Lottery for: {lottery.period_id}\n"
            info_text += f"Participants: {len(lottery.participants)}"
            self.info_label.setText(info_text)
            
            # Load participants
            for member_id in lottery.participants:
                if member_id in self.members:
                    member = self.members[member_id]
                    item_text = f"{member['name']} (#{member['id']})"
                    item = QListWidgetItem(item_text)
                    item.setData(Qt.UserRole, member_id)
                    self.participants_list.addItem(item)
            
        except Exception as e:
            self.info_label.setText(f"Error loading lottery: {e}")
    
    def start_draw(self):
        """Start the animated lottery draw."""
        self.draw_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.animation_duration)
        self.progress_bar.setValue(0)
        
        self.animation_step = 0
        self.animation_timer.start(100)  # 100ms intervals
    
    def animate_draw(self):
        """Animate the lottery draw process."""
        participants = self.lottery_data['participants']
        
        if self.animation_step < self.animation_duration:
            # Show random participant during animation
            import random
            random_member_id = random.choice(participants)
            
            if random_member_id in self.members:
                member = self.members[random_member_id]
                self.draw_display.setText(f"Drawing...\n{member['name']}")
            
            self.animation_step += 1
            self.progress_bar.setValue(self.animation_step)
        else:
            # Animation complete - show winner
            self.animation_timer.stop()
            self.show_winner()
    
    def show_winner(self):
        """Show the lottery winner."""
        try:
            lottery = LotteryRound.from_dict(self.lottery_data)
            self.winner_id = lottery.draw_winner()
            
            if self.winner_id in self.members:
                winner = self.members[self.winner_id]
                self.draw_display.setText(f"🎉 WINNER! 🎉\n{winner['name']}\n(#{winner['id']})")
                self.draw_display.setStyleSheet(self.draw_display.styleSheet().replace(
                    Colors.TEXT_PRIMARY.name(), Colors.PRIMARY_GREEN.name()
                ))
            
            self.progress_bar.setVisible(False)
            self.close_button.setEnabled(True)
            
        except Exception as e:
            self.draw_display.setText(f"Error drawing winner: {e}")
            self.close_button.setEnabled(True)
    
    def get_winner_id(self) -> Optional[int]:
        """Get the winner ID."""
        return self.winner_id

class MemberStatsDialog(QDialog):
    """
    Dialog for displaying member statistics and lottery history.
    """
    
    def __init__(self, members: List[Dict], lottery_history: List[Dict], 
                 reservations: List[Dict], parent=None):
        """
        Initialize the MemberStatsDialog.
        
        Args:
            members (List[Dict]): List of all members
            lottery_history (List[Dict]): List of lottery records
            reservations (List[Dict]): List of reservations
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.members = {m['id']: m for m in members}
        self.lottery_history = lottery_history
        self.reservations = reservations
        
        self.setup_ui()
        self.load_statistics()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Member Statistics")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Member Statistics & Lottery History")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_GREEN.name()}; margin-bottom: 15px;")
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Statistics tab
        stats_tab = self.create_statistics_tab()
        self.tab_widget.addTab(stats_tab, "Statistics")
        
        # Lottery history tab
        history_tab = self.create_history_tab()
        self.tab_widget.addTab(history_tab, "Lottery History")
        
        # Reservations tab
        reservations_tab = self.create_reservations_tab()
        self.tab_widget.addTab(reservations_tab, "Current Reservations")
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        # Add to main layout
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def create_statistics_tab(self) -> QWidget:
        """Create the statistics tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Stats table
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(6)
        self.stats_table.setHorizontalHeaderLabels([
            "Member", "Participations", "Wins", "Confirmed", "Win Rate %", "Confirmation Rate %"
        ])
        
        # Resize columns
        header = self.stats_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.stats_table)
        tab.setLayout(layout)
        return tab
    
    def create_history_tab(self) -> QWidget:
        """Create the lottery history tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Period", "Participants", "Winner", "Status", "Notes"
        ])
        
        # Resize columns
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        
        layout.addWidget(self.history_table)
        tab.setLayout(layout)
        return tab
    
    def create_reservations_tab(self) -> QWidget:
        """Create the current reservations tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Reservations table
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(4)
        self.reservations_table.setHorizontalHeaderLabels([
            "Period", "Member", "Status", "Confirmed Date"
        ])
        
        # Resize columns
        header = self.reservations_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.reservations_table)
        tab.setLayout(layout)
        return tab
    
    def load_statistics(self):
        """Load statistics into the tables."""
        from models.lottery import LotteryManager
        from models.reservation import ReservationManager
        
        # Load member statistics
        member_ids = list(self.members.keys())
        fairness_report = LotteryManager.get_fairness_report(self.lottery_history, member_ids)
        
        self.stats_table.setRowCount(len(self.members))
        
        for row, (member_id, member) in enumerate(self.members.items()):
            stats = fairness_report['member_stats'].get(member_id, {
                'participations': 0, 'wins': 0, 'confirmed_wins': 0,
                'win_rate': 0, 'confirmation_rate': 0
            })
            
            self.stats_table.setItem(row, 0, QTableWidgetItem(f"{member['name']} (#{member['id']})"))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(stats['participations'])))
            self.stats_table.setItem(row, 2, QTableWidgetItem(str(stats['wins'])))
            self.stats_table.setItem(row, 3, QTableWidgetItem(str(stats['confirmed_wins'])))
            self.stats_table.setItem(row, 4, QTableWidgetItem(f"{stats['win_rate']:.1f}"))
            self.stats_table.setItem(row, 5, QTableWidgetItem(f"{stats['confirmation_rate']:.1f}"))
        
        # Load lottery history
        sorted_history = LotteryManager.sort_lotteries_by_date(self.lottery_history)
        self.history_table.setRowCount(len(sorted_history))
        
        for row, lottery in enumerate(sorted_history):
            draw_date = lottery.get('draw_date', '')
            if draw_date:
                try:
                    date_obj = datetime.fromisoformat(draw_date)
                    draw_date = date_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    pass
            
            period_id = lottery.get('period_id', '')
            participants_count = len(lottery.get('participants', []))
            
            winner_name = ""
            winner_id = lottery.get('winner_id')
            if winner_id and winner_id in self.members:
                winner_name = f"{self.members[winner_id]['name']} (#{winner_id})"
            
            status = lottery.get('status', 'unknown').title()
            notes = lottery.get('notes', '')
            
            self.history_table.setItem(row, 0, QTableWidgetItem(draw_date))
            self.history_table.setItem(row, 1, QTableWidgetItem(period_id))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(participants_count)))
            self.history_table.setItem(row, 3, QTableWidgetItem(winner_name))
            self.history_table.setItem(row, 4, QTableWidgetItem(status))
            self.history_table.setItem(row, 5, QTableWidgetItem(notes))
        
        # Load current reservations
        reserved_periods = ReservationManager.get_reservations_by_status(
            self.reservations, ReservationStatus.RESERVED
        )
        pending_periods = ReservationManager.get_reservations_by_status(
            self.reservations, ReservationStatus.PENDING_CONFIRMATION
        )
        
        all_active = reserved_periods + pending_periods
        sorted_reservations = ReservationManager.sort_reservations_by_date(all_active)
        
        self.reservations_table.setRowCount(len(sorted_reservations))
        
        for row, reservation in enumerate(sorted_reservations):
            period_id = reservation.get('period_id', '')
            
            member_name = ""
            member_id = reservation.get('member_id')
            if member_id and member_id in self.members:
                member_name = f"{self.members[member_id]['name']} (#{member_id})"
            
            status = reservation.get('status', 'unknown')
            status_display = {
                ReservationStatus.RESERVED: "Reserved",
                ReservationStatus.PENDING_CONFIRMATION: "Pending Confirmation"
            }.get(status, status)
            
            confirmed_date = reservation.get('confirmed_date', '')
            if confirmed_date:
                try:
                    date_obj = datetime.fromisoformat(confirmed_date)
                    confirmed_date = date_obj.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    pass
            
            self.reservations_table.setItem(row, 0, QTableWidgetItem(period_id))
            self.reservations_table.setItem(row, 1, QTableWidgetItem(member_name))
            self.reservations_table.setItem(row, 2, QTableWidgetItem(status_display))
            self.reservations_table.setItem(row, 3, QTableWidgetItem(confirmed_date))

class ConfirmationDialog(QDialog):
    """
    Simple confirmation dialog with custom message.
    """
    
    def __init__(self, title: str, message: str, parent=None):
        """
        Initialize the ConfirmationDialog.
        
        Args:
            title (str): Dialog title
            message (str): Confirmation message
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.setWindowTitle(title)
        self.setMinimumSize(400, 200)
        
        # Layout
        layout = QVBoxLayout()
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY.name()}; margin: 20px;")
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Yes | QDialogButtonBox.No,
            Qt.Horizontal
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(message_label)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

class AboutDialog(QDialog):
    """
    About dialog showing application information.
    """
    
    def __init__(self, parent=None):
        """Initialize the AboutDialog."""
        super().__init__(parent)
        
        self.setWindowTitle("About Hunting Club Reservation System")
        self.setFixedSize(400, 300)
        
        # Layout
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Hunting Club Reservation System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.PRIMARY_GREEN.name()}; margin-bottom: 10px;")
        
        # Version
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY.name()}; margin-bottom: 20px;")
        
        # Description
        description = QLabel(
            "A fair lottery system for managing cabin reservations "
            "during the May-July hunting season.\n\n"
            "Features:\n"
            "• 21 member management\n"
            "• Fair lottery system\n"
            "• 7-day reservation periods\n"
            "• 5-day confirmation window\n"
            "• Comprehensive statistics\n\n"
            "Built with PyQt5 and Python"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet(f"color: {Colors.TEXT_PRIMARY.name()}; margin: 20px;")
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addWidget(description)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)