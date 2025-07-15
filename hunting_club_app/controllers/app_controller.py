# Main application controller
"""
Application Controller Module

This module contains the main application controller that coordinates
between the UI and business logic for the Hunting Club Reservation System.
"""

import logging
import sys
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from utils.data_manager import DataManager
from utils.constants import ReservationStatus
from views.main_window import MainWindow
from views.dialogs import LotteryDrawDialog, ConfirmationDialog
from controllers.lottery_controller import LotteryController

class AppController(QObject):
    """
    Main application controller.
    
    This controller manages the overall application flow, coordinates between
    different components, and handles the main business logic for the
    Hunting Club Reservation System.
    """
    
    def __init__(self, parent=None):
        """Initialize the AppController."""
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.data_manager = DataManager()
        self.lottery_controller = LotteryController(self.data_manager)
        self.main_window = MainWindow()
        
        self.setup_connections()
        self.load_initial_data()
        
        self.logger.info("AppController initialized")
    
    def setup_connections(self):
        """Set up signal-slot connections between components."""
        # Main window signals
        self.main_window.member_changed.connect(self.on_member_changed)
        self.main_window.lottery_requested.connect(self.on_lottery_requested)
        self.main_window.period_selected.connect(self.on_period_selected)
        self.main_window.refresh_requested.connect(self.refresh_data)
        
        # Lottery controller signals
        self.lottery_controller.lottery_created.connect(self.on_lottery_created)
        self.lottery_controller.lottery_drawn.connect(self.on_lottery_drawn)
        self.lottery_controller.reservation_confirmed.connect(self.on_reservation_confirmed)
        self.lottery_controller.confirmation_expired.connect(self.on_confirmation_expired)
        self.lottery_controller.data_updated.connect(self.refresh_data)
        self.lottery_controller.error_occurred.connect(self.on_error_occurred)
        
        self.logger.debug("Signal connections established")
    
    def load_initial_data(self):
        """Load initial data and populate the UI."""
        try:
            # Load members
            members = self.data_manager.get_all_members()
            self.main_window.load_members(members)
            
            # Load reservations
            reservations = self.data_manager.get_all_reservations()
            self.main_window.load_reservations(reservations)
            
            # Load lottery history
            lottery_history = self.data_manager.get_lottery_history()
            self.main_window.load_lottery_history(lottery_history)
            
            # Clean up any expired confirmations
            self.lottery_controller.cleanup_expired_lotteries()
            
            self.logger.info("Initial data loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Error loading initial data: {e}")
            self.show_error("Data Loading Error", f"Failed to load initial data: {e}")
    
    def refresh_data(self):
        """Refresh all data from storage."""
        try:
            # Load fresh data
            members = self.data_manager.get_all_members()
            reservations = self.data_manager.get_all_reservations()
            lottery_history = self.data_manager.get_lottery_history()
            
            # Update main window
            self.main_window.update_data(members, reservations, lottery_history)
            
            self.logger.debug("Data refreshed")
            
        except Exception as e:
            self.logger.error(f"Error refreshing data: {e}")
            self.show_error("Data Refresh Error", f"Failed to refresh data: {e}")
    
    def on_member_changed(self, member_name: str):
        """
        Handle member selection change.
        
        Args:
            member_name (str): Selected member name
        """
        self.logger.debug(f"Member changed to: {member_name}")
        # Additional logic for member-specific views could go here
    
    def on_lottery_requested(self, lottery_data_list: List[Dict], members: List[Dict]):
        """
        Handle lottery creation request.
        
        Args:
            lottery_data_list (List[Dict]): List of lottery data (usually one item)
            members (List[Dict]): List of member data
        """
        if not lottery_data_list:
            return
        
        lottery_data = lottery_data_list[0]
        period_id = lottery_data['period_id']
        participants = lottery_data['participants']
        
        # Create the lottery
        if self.lottery_controller.create_lottery(period_id, participants):
            # Show draw dialog
            self.show_lottery_draw(lottery_data['lottery_id'])
    
    def on_period_selected(self, period_id: str):
        """
        Handle period selection.
        
        Args:
            period_id (str): Selected period ID
        """
        self.logger.debug(f"Period selected: {period_id}")
        
        # Get period data
        reservation = self.data_manager.get_reservation_by_period_id(period_id)
        if not reservation:
            return
        
        # Handle different period statuses
        if reservation['status'] == ReservationStatus.PENDING_CONFIRMATION:
            self.handle_pending_confirmation(period_id, reservation)
        elif reservation['status'] == ReservationStatus.RESERVED:
            self.show_reservation_details(period_id, reservation)
        elif reservation['status'] == ReservationStatus.IN_LOTTERY:
            self.show_lottery_details(period_id, reservation)
    
    def handle_pending_confirmation(self, period_id: str, reservation: Dict):
        """
        Handle interaction with a period pending confirmation.
        
        Args:
            period_id (str): Period ID
            reservation (Dict): Reservation data
        """
        member_id = reservation.get('member_id')
        if not member_id:
            return
        
        # Get member info
        member = self.data_manager.get_member_by_id(member_id)
        if not member:
            return
        
        # Get time remaining
        time_remaining = self.lottery_controller.get_confirmation_time_remaining(period_id)
        
        # Build confirmation dialog message
        message = f"Period: {period_id}\n"
        message += f"Winner: {member['name']} (#{member['id']})\n"
        message += f"Status: Pending Confirmation\n"
        
        if time_remaining:
            hours = int(time_remaining.total_seconds() // 3600)
            minutes = int((time_remaining.total_seconds() % 3600) // 60)
            message += f"Time remaining: {hours}h {minutes}m\n"
        
        message += "\nWould you like to confirm this reservation?"
        
        # Show confirmation dialog
        dialog = ConfirmationDialog("Confirm Reservation", message, self.main_window)
        if dialog.exec_() == dialog.Accepted:
            self.lottery_controller.confirm_reservation(period_id, member_id)
    
    def show_reservation_details(self, period_id: str, reservation: Dict):
        """
        Show details for a reserved period.
        
        Args:
            period_id (str): Period ID
            reservation (Dict): Reservation data
        """
        member_id = reservation.get('member_id')
        if not member_id:
            return
        
        member = self.data_manager.get_member_by_id(member_id)
        if not member:
            return
        
        # Build message
        message = f"Period: {period_id}\n"
        message += f"Reserved by: {member['name']} (#{member['id']})\n"
        message += f"Email: {member['email']}\n"
        message += f"Phone: {member['phone']}\n"
        
        confirmed_date = reservation.get('confirmed_date')
        if confirmed_date:
            try:
                from datetime import datetime
                date_obj = datetime.fromisoformat(confirmed_date)
                message += f"Confirmed: {date_obj.strftime('%Y-%m-%d %H:%M')}\n"
            except ValueError:
                pass
        
        # Show details
        QMessageBox.information(self.main_window, "Reservation Details", message)
    
    def show_lottery_details(self, period_id: str, reservation: Dict):
        """
        Show details for a period in lottery.
        
        Args:
            period_id (str): Period ID
            reservation (Dict): Reservation data
        """
        lottery_id = reservation.get('lottery_id')
        if not lottery_id:
            return
        
        # Get lottery summary
        summary = self.lottery_controller.get_lottery_summary(lottery_id)
        if summary:
            QMessageBox.information(self.main_window, "Lottery Details", summary)
    
    def show_lottery_draw(self, lottery_id: str):
        """
        Show the lottery draw dialog.
        
        Args:
            lottery_id (str): Lottery ID to draw
        """
        try:
            # Get lottery data
            lottery_data = self.data_manager.get_lottery_by_id(lottery_id)
            if not lottery_data:
                self.show_error("Lottery Error", f"Lottery {lottery_id} not found")
                return
            
            # Get members data
            members = self.data_manager.get_all_members()
            members_dict = {m['id']: m for m in members}
            
            # Show draw dialog
            dialog = LotteryDrawDialog(lottery_data, members_dict, self.main_window)
            if dialog.exec_() == dialog.Accepted:
                winner_id = dialog.get_winner_id()
                if winner_id:
                    # Draw the lottery
                    self.lottery_controller.draw_lottery(lottery_id)
            
        except Exception as e:
            self.logger.error(f"Error showing lottery draw: {e}")
            self.show_error("Lottery Draw Error", str(e))
    
    def on_lottery_created(self, lottery_data: Dict):
        """
        Handle lottery creation completion.
        
        Args:
            lottery_data (Dict): Created lottery data
        """
        self.logger.info(f"Lottery created: {lottery_data['lottery_id']}")
        
        # Refresh data to show updated status
        self.refresh_data()
    
    def on_lottery_drawn(self, lottery_data: Dict):
        """
        Handle lottery draw completion.
        
        Args:
            lottery_data (Dict): Drawn lottery data
        """
        winner_id = lottery_data.get('winner_id')
        period_id = lottery_data.get('period_id')
        
        if winner_id and period_id:
            member = self.data_manager.get_member_by_id(winner_id)
            if member:
                message = f"Lottery drawn for period {period_id}!\n\n"
                message += f"Winner: {member['name']} (#{member['id']})\n"
                message += f"Email: {member['email']}\n"
                message += f"Phone: {member['phone']}\n\n"
                message += "The winner has 5 days to confirm their reservation."
                
                QMessageBox.information(self.main_window, "Lottery Winner", message)
        
        self.logger.info(f"Lottery drawn: {lottery_data['lottery_id']}, winner: {winner_id}")
        
        # Refresh data
        self.refresh_data()
    
    def on_reservation_confirmed(self, period_id: str, member_id: int):
        """
        Handle reservation confirmation.
        
        Args:
            period_id (str): Confirmed period ID
            member_id (int): Member ID who confirmed
        """
        member = self.data_manager.get_member_by_id(member_id)
        if member:
            message = f"Reservation confirmed!\n\n"
            message += f"Period: {period_id}\n"
            message += f"Member: {member['name']} (#{member['id']})"
            
            QMessageBox.information(self.main_window, "Reservation Confirmed", message)
        
        self.logger.info(f"Reservation confirmed: {period_id} by member {member_id}")
        
        # Refresh data
        self.refresh_data()
    
    def on_confirmation_expired(self, period_id: str):
        """
        Handle confirmation expiration.
        
        Args:
            period_id (str): Expired period ID
        """
        message = f"Confirmation period has expired for: {period_id}\n\n"
        message += "The period is now available for new lottery."
        
        QMessageBox.warning(self.main_window, "Confirmation Expired", message)
        
        self.logger.info(f"Confirmation expired: {period_id}")
        
        # Refresh data
        self.refresh_data()
    
    def on_error_occurred(self, title: str, message: str):
        """
        Handle error notifications.
        
        Args:
            title (str): Error title
            message (str): Error message
        """
        self.show_error(title, message)
    
    def show_error(self, title: str, message: str):
        """
        Show an error message to the user.
        
        Args:
            title (str): Error title
            message (str): Error message
        """
        self.main_window.show_message(title, message, "error")
        self.logger.error(f"{title}: {message}")
    
    def show_warning(self, title: str, message: str):
        """
        Show a warning message to the user.
        
        Args:
            title (str): Warning title
            message (str): Warning message
        """
        self.main_window.show_message(title, message, "warning")
        self.logger.warning(f"{title}: {message}")
    
    def show_info(self, title: str, message: str):
        """
        Show an information message to the user.
        
        Args:
            title (str): Info title
            message (str): Info message
        """
        self.main_window.show_message(title, message, "info")
        self.logger.info(f"{title}: {message}")
    
    def validate_system_integrity(self) -> bool:
        """
        Validate the integrity of the system data.
        
        Returns:
            bool: True if system is valid, False otherwise
        """
        try:
            issues = self.data_manager.validate_data_integrity()
            
            # Check for critical issues
            critical_issues = []
            for category, issue_list in issues.items():
                if issue_list:
                    critical_issues.extend(issue_list)
            
            if critical_issues:
                message = "System integrity issues found:\n\n"
                message += "\n".join(critical_issues[:10])  # Show first 10 issues
                
                if len(critical_issues) > 10:
                    message += f"\n... and {len(critical_issues) - 10} more issues"
                
                self.show_warning("System Integrity Warning", message)
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating system integrity: {e}")
            return False
    
    def backup_data(self) -> bool:
        """
        Create a backup of all system data.
        
        Returns:
            bool: True if backup was successful
        """
        try:
            backup_path = self.data_manager.backup_data()
            
            message = f"Data backup created successfully:\n{backup_path}"
            self.show_info("Backup Complete", message)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            self.show_error("Backup Error", f"Failed to create backup: {e}")
            return False
    
    def export_statistics(self) -> bool:
        """
        Export system statistics to a file.
        
        Returns:
            bool: True if export was successful
        """
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            from datetime import datetime
            
            # Get export file path
            default_filename = f"hunting_club_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Export Statistics",
                default_filename,
                "JSON Files (*.json);;All Files (*)"
            )
            
            if not filepath:
                return False
            
            # Generate statistics
            members = self.data_manager.get_all_members()
            member_ids = [m['id'] for m in members]
            
            fairness_report = self.lottery_controller.get_fairness_report(member_ids)
            
            # Add additional stats
            reservations = self.data_manager.get_all_reservations()
            stats = {
                'export_date': datetime.now().isoformat(),
                'fairness_report': fairness_report,
                'reservation_summary': {
                    'total_periods': len(reservations),
                    'available': len([r for r in reservations if r['status'] == ReservationStatus.AVAILABLE]),
                    'reserved': len([r for r in reservations if r['status'] == ReservationStatus.RESERVED]),
                    'in_lottery': len([r for r in reservations if r['status'] == ReservationStatus.IN_LOTTERY]),
                    'pending_confirmation': len([r for r in reservations if r['status'] == ReservationStatus.PENDING_CONFIRMATION]),
                    'expired': len([r for r in reservations if r['status'] == ReservationStatus.EXPIRED])
                }
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            self.show_info("Export Complete", f"Statistics exported to:\n{filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting statistics: {e}")
            self.show_error("Export Error", f"Failed to export statistics: {e}")
            return False
    
    def show(self):
        """Show the main window."""
        self.main_window.show()
        
        # Validate system integrity on startup
        self.validate_system_integrity()
    
    def close(self):
        """Close the application."""
        self.lottery_controller.stop()
        self.main_window.close()
        
        self.logger.info("Application closed")