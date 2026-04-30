# Lottery management
"""
Lottery Controller Module

This module contains the LotteryController class that manages all lottery
operations including creation, drawing, and confirmation handling.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox

from models.lottery import LotteryRound, LotteryManager
from models.reservation import ReservationPeriod, ReservationManager
from utils.constants import ReservationStatus, CONFIRMATION_DAYS
from utils.data_manager import DataManager

class LotteryController(QObject):
    """
    Controller for managing lottery operations.
    
    This controller handles lottery creation, drawing, winner selection,
    and confirmation period management. It coordinates between the UI
    and data models to ensure fair lottery operations.
    """
    
    # Signals
    lottery_created = pyqtSignal(dict)  # Emits lottery data when created
    lottery_drawn = pyqtSignal(dict)    # Emits lottery data when drawn
    reservation_confirmed = pyqtSignal(str, int)  # Emits period_id, member_id
    confirmation_expired = pyqtSignal(str)  # Emits period_id when expired
    data_updated = pyqtSignal()  # Emits when data is updated
    error_occurred = pyqtSignal(str, str)  # Emits title, message for errors
    
    def __init__(self, data_manager: DataManager, parent=None):
        """
        Initialize the LotteryController.
        
        Args:
            data_manager (DataManager): Data manager instance
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.logger = logging.getLogger(__name__)
        
        # Timer for checking expired confirmations
        self.expiration_timer = QTimer()
        self.expiration_timer.timeout.connect(self.check_expired_confirmations)
        self.expiration_timer.start(60000)  # Check every minute
        
        self.logger.info("LotteryController initialized")
    
    def create_lottery(self, period_id: str, participant_ids: List[int]) -> bool:
        """
        Create a new lottery for a reservation period.
        
        Args:
            period_id (str): ID of the period to create lottery for
            participant_ids (List[int]): List of participating member IDs
            
        Returns:
            bool: True if lottery was created successfully
        """
        try:
            # Validate inputs
            if not period_id:
                raise ValueError("Period ID cannot be empty")
            
            if not participant_ids:
                raise ValueError("At least one participant is required")
            
            # Check if period is available
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation:
                raise ValueError(f"Period {period_id} not found")
            
            if reservation['status'] != ReservationStatus.AVAILABLE:
                raise ValueError(f"Period {period_id} is not available for lottery")
            
            # Validate participants exist
            members = self.data_manager.get_all_members()
            member_ids = {m['id'] for m in members}
            
            invalid_participants = set(participant_ids) - member_ids
            if invalid_participants:
                raise ValueError(f"Invalid participant IDs: {invalid_participants}")
            
            # Create lottery round
            lottery = LotteryRound(
                lottery_id="",  # Will be auto-generated
                period_id=period_id,
                participants=participant_ids
            )
            
            # Update period status to IN_LOTTERY
            period_updates = {
                'status': ReservationStatus.IN_LOTTERY,
                'lottery_id': lottery.lottery_id
            }
            
            if not self.data_manager.update_reservation(period_id, period_updates):
                raise Exception("Failed to update reservation status")
            
            # Save lottery to history
            if not self.data_manager.add_lottery_record(lottery.to_dict()):
                # Rollback reservation update
                self.data_manager.update_reservation(period_id, {
                    'status': ReservationStatus.AVAILABLE,
                    'lottery_id': None
                })
                raise Exception("Failed to save lottery record")
            
            self.logger.info(f"Created lottery {lottery.lottery_id} for period {period_id}")
            
            # Emit signals
            self.lottery_created.emit(lottery.to_dict())
            self.data_updated.emit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating lottery: {e}")
            self.error_occurred.emit("Lottery Creation Error", str(e))
            return False
    
    def draw_lottery(self, lottery_id: str) -> Optional[int]:
        """
        Draw a winner for a lottery.
        
        Args:
            lottery_id (str): ID of the lottery to draw
            
        Returns:
            Optional[int]: Winner member ID, or None if draw failed
        """
        try:
            # Get lottery data
            lottery_data = self.data_manager.get_lottery_by_id(lottery_id)
            if not lottery_data:
                raise ValueError(f"Lottery {lottery_id} not found")
            
            # Create lottery object and draw winner
            lottery = LotteryRound.from_dict(lottery_data)
            
            if not lottery.is_pending():
                raise ValueError(f"Lottery {lottery_id} is not pending")
            
            winner_id = lottery.draw_winner()
            
            # Update lottery record
            lottery_updates = {
                'winner_id': winner_id,
                'draw_date': lottery.draw_date.isoformat(),
                'confirmation_deadline': lottery.confirmation_deadline.isoformat(),
                'status': 'drawn'
            }
            
            if not self.data_manager.update_lottery_record(lottery_id, lottery_updates):
                raise Exception("Failed to update lottery record")
            
            # Update reservation to pending confirmation
            reservation_updates = {
                'member_id': winner_id,
                'status': ReservationStatus.PENDING_CONFIRMATION
            }
            
            if not self.data_manager.update_reservation(lottery.period_id, reservation_updates):
                # Rollback lottery update
                self.data_manager.update_lottery_record(lottery_id, {
                    'winner_id': None,
                    'draw_date': None,
                    'confirmation_deadline': None,
                    'status': 'pending'
                })
                raise Exception("Failed to update reservation")
            
            self.logger.info(f"Drew lottery {lottery_id}, winner: {winner_id}")
            
            # Emit signals
            self.lottery_drawn.emit(lottery.to_dict())
            self.data_updated.emit()
            
            return winner_id
            
        except Exception as e:
            self.logger.error(f"Error drawing lottery: {e}")
            self.error_occurred.emit("Lottery Draw Error", str(e))
            return None
    
    def confirm_reservation(self, period_id: str, member_id: int) -> bool:
        """
        Confirm a reservation for a lottery winner.
        
        Args:
            period_id (str): Period ID to confirm
            member_id (int): Member ID confirming the reservation
            
        Returns:
            bool: True if confirmation was successful
        """
        try:
            # Get reservation data
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation:
                raise ValueError(f"Period {period_id} not found")
            
            # Validate reservation status and member
            if reservation['status'] != ReservationStatus.PENDING_CONFIRMATION:
                raise ValueError(f"Period {period_id} is not pending confirmation")
            
            if reservation['member_id'] != member_id:
                raise ValueError(f"Member {member_id} is not the winner for period {period_id}")
            
            # Update reservation to confirmed
            reservation_updates = {
                'status': ReservationStatus.RESERVED,
                'confirmed_date': datetime.now().isoformat()
            }
            
            if not self.data_manager.update_reservation(period_id, reservation_updates):
                raise Exception("Failed to update reservation")
            
            # Update lottery status to confirmed
            lottery_id = reservation.get('lottery_id')
            if lottery_id:
                lottery_updates = {'status': 'confirmed'}
                self.data_manager.update_lottery_record(lottery_id, lottery_updates)
            
            self.logger.info(f"Confirmed reservation for period {period_id} by member {member_id}")
            
            # Emit signals
            self.reservation_confirmed.emit(period_id, member_id)
            self.data_updated.emit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error confirming reservation: {e}")
            self.error_occurred.emit("Confirmation Error", str(e))
            return False
    
    def cancel_reservation(self, period_id: str, reason: str = "") -> bool:
        """
        Cancel a reservation and make the period available again.
        
        Args:
            period_id (str): Period ID to cancel
            reason (str): Reason for cancellation
            
        Returns:
            bool: True if cancellation was successful
        """
        try:
            # Get reservation data
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation:
                raise ValueError(f"Period {period_id} not found")
            
            # Reset reservation to available
            if not self.data_manager.reset_reservation(period_id):
                raise Exception("Failed to reset reservation")
            
            # Update lottery status if applicable
            lottery_id = reservation.get('lottery_id')
            if lottery_id:
                lottery_updates = {
                    'status': 'cancelled',
                    'notes': f"Cancelled: {reason}" if reason else "Cancelled"
                }
                self.data_manager.update_lottery_record(lottery_id, lottery_updates)
            
            self.logger.info(f"Cancelled reservation for period {period_id}: {reason}")
            
            # Emit signal
            self.data_updated.emit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling reservation: {e}")
            self.error_occurred.emit("Cancellation Error", str(e))
            return False
    
    def check_expired_confirmations(self):
        """Check for and handle expired confirmation periods."""
        try:
            reservations = self.data_manager.get_all_reservations()
            lottery_history = self.data_manager.get_lottery_history()
            
            # Find expired confirmations
            expired_reservations = ReservationManager.get_expired_confirmations(
                reservations, lottery_history
            )
            
            for reservation in expired_reservations:
                period_id = reservation['period_id']
                
                # Update reservation status to expired
                updates = {'status': ReservationStatus.EXPIRED}
                self.data_manager.update_reservation(period_id, updates)
                
                # Update lottery status to expired
                lottery_id = reservation.get('lottery_id')
                if lottery_id:
                    lottery_updates = {'status': 'expired'}
                    self.data_manager.update_lottery_record(lottery_id, lottery_updates)
                
                self.logger.info(f"Expired confirmation for period {period_id}")
                
                # Emit signal
                self.confirmation_expired.emit(period_id)
            
            if expired_reservations:
                self.data_updated.emit()
                
        except Exception as e:
            self.logger.error(f"Error checking expired confirmations: {e}")
    
    def get_pending_lotteries(self) -> List[Dict]:
        """
        Get all pending lotteries.
        
        Returns:
            List[Dict]: List of pending lottery data
        """
        try:
            lottery_history = self.data_manager.get_lottery_history()
            return LotteryManager.get_pending_lotteries(lottery_history)
            
        except Exception as e:
            self.logger.error(f"Error getting pending lotteries: {e}")
            return []
    
    def get_drawn_lotteries(self) -> List[Dict]:
        """
        Get all drawn lotteries awaiting confirmation.
        
        Returns:
            List[Dict]: List of drawn lottery data
        """
        try:
            lottery_history = self.data_manager.get_lottery_history()
            return LotteryManager.get_drawn_lotteries(lottery_history)
            
        except Exception as e:
            self.logger.error(f"Error getting drawn lotteries: {e}")
            return []
    
    def get_member_lottery_stats(self, member_id: int) -> Dict:
        """
        Get lottery statistics for a specific member.
        
        Args:
            member_id (int): Member ID
            
        Returns:
            Dict: Member lottery statistics
        """
        try:
            lottery_history = self.data_manager.get_lottery_history()
            return LotteryManager.calculate_member_stats(lottery_history, member_id)
            
        except Exception as e:
            self.logger.error(f"Error getting member lottery stats: {e}")
            return {
                'member_id': member_id,
                'participations': 0,
                'wins': 0,
                'confirmed_wins': 0,
                'win_rate': 0,
                'confirmation_rate': 0
            }
    
    def get_fairness_report(self, member_ids: List[int]) -> Dict:
        """
        Generate a fairness report for all members.
        
        Args:
            member_ids (List[int]): List of all member IDs
            
        Returns:
            Dict: Fairness report
        """
        try:
            lottery_history = self.data_manager.get_lottery_history()
            return LotteryManager.get_fairness_report(lottery_history, member_ids)
            
        except Exception as e:
            self.logger.error(f"Error generating fairness report: {e}")
            return {
                'total_lotteries': 0,
                'total_participations': 0,
                'total_wins': 0,
                'average_participation': 0,
                'member_stats': {},
                'highest_win_rate': None,
                'lowest_win_rate': None,
                'active_members': 0
            }
    
    def validate_lottery_eligibility(self, member_id: int, period_id: str) -> Tuple[bool, str]:
        """
        Validate if a member is eligible to participate in a lottery.
        
        Args:
            member_id (int): Member ID to validate
            period_id (str): Period ID for the lottery
            
        Returns:
            Tuple[bool, str]: (is_eligible, reason_if_not)
        """
        try:
            # Check if member exists
            member = self.data_manager.get_member_by_id(member_id)
            if not member:
                return False, f"Member {member_id} not found"
            
            # Check if period exists and is available
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation:
                return False, f"Period {period_id} not found"
            
            if reservation['status'] != ReservationStatus.AVAILABLE:
                return False, f"Period {period_id} is not available for lottery"
            
            # Check if member already has a reservation for this season
            reservations = self.data_manager.get_all_reservations()
            member_reservations = ReservationManager.get_reservations_by_member(
                reservations, member_id
            )
            
            # Count confirmed and pending reservations
            active_reservations = [
                r for r in member_reservations 
                if r['status'] in [ReservationStatus.RESERVED, ReservationStatus.PENDING_CONFIRMATION]
            ]
            
            if active_reservations:
                return False, f"Member {member_id} already has an active reservation"
            
            # Check if member is already in a pending lottery
            lottery_history = self.data_manager.get_lottery_history()
            pending_lotteries = LotteryManager.get_pending_lotteries(lottery_history)
            
            for lottery in pending_lotteries:
                if member_id in lottery.get('participants', []):
                    return False, f"Member {member_id} is already in a pending lottery"
            
            return True, "Eligible"
            
        except Exception as e:
            self.logger.error(f"Error validating lottery eligibility: {e}")
            return False, f"Validation error: {e}"
    
    def get_lottery_summary(self, lottery_id: str) -> Optional[str]:
        """
        Get a formatted summary of a lottery.
        
        Args:
            lottery_id (str): Lottery ID
            
        Returns:
            Optional[str]: Formatted lottery summary or None if not found
        """
        try:
            lottery_data = self.data_manager.get_lottery_by_id(lottery_id)
            if not lottery_data:
                return None
            
            lottery = LotteryRound.from_dict(lottery_data)
            return lottery.get_summary()
            
        except Exception as e:
            self.logger.error(f"Error getting lottery summary: {e}")
            return None
    
    def cleanup_expired_lotteries(self) -> int:
        """
        Clean up expired lottery confirmations and reset periods to available.
        
        Returns:
            int: Number of periods cleaned up
        """
        try:
            cleaned_count = 0
            reservations = self.data_manager.get_all_reservations()
            lottery_history = self.data_manager.get_lottery_history()
            
            # Find expired confirmations
            expired_reservations = ReservationManager.get_expired_confirmations(
                reservations, lottery_history
            )
            
            for reservation in expired_reservations:
                period_id = reservation['period_id']
                
                # Reset reservation to available
                if self.data_manager.reset_reservation(period_id):
                    cleaned_count += 1
                    
                    # Update lottery status
                    lottery_id = reservation.get('lottery_id')
                    if lottery_id:
                        lottery_updates = {
                            'status': 'expired',
                            'notes': 'Confirmation period expired'
                        }
                        self.data_manager.update_lottery_record(lottery_id, lottery_updates)
                    
                    self.logger.info(f"Cleaned up expired period {period_id}")
            
            if cleaned_count > 0:
                self.data_updated.emit()
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired lotteries: {e}")
            return 0
    
    def get_confirmation_time_remaining(self, period_id: str) -> Optional[timedelta]:
        """
        Get the time remaining for confirmation of a pending reservation.
        
        Args:
            period_id (str): Period ID to check
            
        Returns:
            Optional[timedelta]: Time remaining, or None if not applicable
        """
        try:
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation or reservation['status'] != ReservationStatus.PENDING_CONFIRMATION:
                return None
            
            lottery_id = reservation.get('lottery_id')
            if not lottery_id:
                return None
            
            lottery_data = self.data_manager.get_lottery_by_id(lottery_id)
            if not lottery_data:
                return None
            
            lottery = LotteryRound.from_dict(lottery_data)
            return lottery.get_time_remaining()
            
        except Exception as e:
            self.logger.error(f"Error getting confirmation time remaining: {e}")
            return None
    
    def force_expire_confirmation(self, period_id: str) -> bool:
        """
        Force expire a pending confirmation (admin function).
        
        Args:
            period_id (str): Period ID to expire
            
        Returns:
            bool: True if expiration was successful
        """
        try:
            reservation = self.data_manager.get_reservation_by_period_id(period_id)
            if not reservation:
                raise ValueError(f"Period {period_id} not found")
            
            if reservation['status'] != ReservationStatus.PENDING_CONFIRMATION:
                raise ValueError(f"Period {period_id} is not pending confirmation")
            
            # Update reservation to expired
            updates = {'status': ReservationStatus.EXPIRED}
            if not self.data_manager.update_reservation(period_id, updates):
                raise Exception("Failed to update reservation")
            
            # Update lottery status
            lottery_id = reservation.get('lottery_id')
            if lottery_id:
                lottery_updates = {
                    'status': 'expired',
                    'notes': 'Manually expired by admin'
                }
                self.data_manager.update_lottery_record(lottery_id, lottery_updates)
            
            self.logger.info(f"Force expired confirmation for period {period_id}")
            
            # Emit signals
            self.confirmation_expired.emit(period_id)
            self.data_updated.emit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error force expiring confirmation: {e}")
            self.error_occurred.emit("Force Expiration Error", str(e))
            return False
    
    def get_lottery_participants_summary(self, lottery_id: str) -> Optional[str]:
        """
        Get a formatted summary of lottery participants.
        
        Args:
            lottery_id (str): Lottery ID
            
        Returns:
            Optional[str]: Formatted participants summary
        """
        try:
            lottery_data = self.data_manager.get_lottery_by_id(lottery_id)
            if not lottery_data:
                return None
            
            members = self.data_manager.get_all_members()
            member_dict = {m['id']: m for m in members}
            
            participants = lottery_data.get('participants', [])
            if not participants:
                return "No participants"
            
            participant_names = []
            for member_id in participants:
                if member_id in member_dict:
                    member = member_dict[member_id]
                    participant_names.append(f"{member['name']} (#{member['id']})")
                else:
                    participant_names.append(f"Unknown Member #{member_id}")
            
            return "\n".join(participant_names)
            
        except Exception as e:
            self.logger.error(f"Error getting participants summary: {e}")
            return None
    
    def stop(self):
        """Stop the lottery controller and clean up resources."""
        if self.expiration_timer.isActive():
            self.expiration_timer.stop()
        
        self.logger.info("LotteryController stopped")