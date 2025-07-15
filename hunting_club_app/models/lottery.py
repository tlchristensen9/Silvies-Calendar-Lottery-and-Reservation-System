# Lottery system logic
"""
Lottery System Model

This module contains the Lottery class and related functionality for
managing the fair lottery system in the Hunting Club Reservation System.
"""

import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import logging

from utils.constants import CONFIRMATION_DAYS, format_date_range

@dataclass
class LotteryRound:
    """
    Represents a single lottery round for a reservation period.
    
    Attributes:
        lottery_id (str): Unique identifier for the lottery
        period_id (str): ID of the reservation period being drawn for
        participants (List[int]): List of member IDs participating in the lottery
        winner_id (Optional[int]): ID of the winning member
        draw_date (datetime): Date and time when the lottery was drawn
        confirmation_deadline (datetime): Deadline for winner to confirm reservation
        status (str): Current status of the lottery
        notes (str): Additional notes about the lottery
    """
    
    lottery_id: str
    period_id: str
    participants: List[int]
    winner_id: Optional[int] = None
    draw_date: Optional[datetime] = None
    confirmation_deadline: Optional[datetime] = None
    status: str = "pending"
    notes: str = ""
    
    def __post_init__(self):
        """Initialize lottery with generated ID if not provided."""
        if not self.lottery_id:
            self.lottery_id = self.generate_lottery_id()
        
        self.validate()
    
    @staticmethod
    def generate_lottery_id() -> str:
        """
        Generate a unique lottery ID.
        
        Returns:
            str: Unique lottery ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = str(uuid.uuid4())[:8]
        return f"lottery_{timestamp}_{random_suffix}"
    
    def validate(self) -> None:
        """
        Validate lottery data.
        
        Raises:
            ValueError: If any field is invalid
        """
        if not self.lottery_id:
            raise ValueError("Lottery ID cannot be empty")
        
        if not self.period_id:
            raise ValueError("Period ID cannot be empty")
        
        if not self.participants:
            raise ValueError("Lottery must have at least one participant")
        
        if len(self.participants) != len(set(self.participants)):
            raise ValueError("Duplicate participants not allowed")
        
        if self.winner_id is not None and self.winner_id not in self.participants:
            raise ValueError("Winner must be one of the participants")
        
        valid_statuses = ["pending", "drawn", "confirmed", "expired", "cancelled"]
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
    
    def add_participant(self, member_id: int) -> None:
        """
        Add a participant to the lottery.
        
        Args:
            member_id (int): ID of the member to add
            
        Raises:
            ValueError: If member is already participating or lottery is not pending
        """
        if self.status != "pending":
            raise ValueError("Cannot add participants to a lottery that is not pending")
        
        if member_id in self.participants:
            raise ValueError(f"Member {member_id} is already participating in this lottery")
        
        self.participants.append(member_id)
    
    def remove_participant(self, member_id: int) -> None:
        """
        Remove a participant from the lottery.
        
        Args:
            member_id (int): ID of the member to remove
            
        Raises:
            ValueError: If member is not participating or lottery is not pending
        """
        if self.status != "pending":
            raise ValueError("Cannot remove participants from a lottery that is not pending")
        
        if member_id not in self.participants:
            raise ValueError(f"Member {member_id} is not participating in this lottery")
        
        self.participants.remove(member_id)
        
        if not self.participants:
            raise ValueError("Lottery must have at least one participant")
    
    def draw_winner(self, random_seed: Optional[int] = None) -> int:
        """
        Draw a random winner from the participants.
        
        Args:
            random_seed (Optional[int]): Seed for random number generator (for testing)
            
        Returns:
            int: ID of the winning member
            
        Raises:
            ValueError: If lottery cannot be drawn
        """
        if self.status != "pending":
            raise ValueError("Lottery has already been drawn or is not ready")
        
        if not self.participants:
            raise ValueError("No participants in lottery")
        
        # Set random seed if provided (for testing)
        if random_seed is not None:
            random.seed(random_seed)
        
        # Draw random winner
        self.winner_id = random.choice(self.participants)
        self.draw_date = datetime.now()
        self.confirmation_deadline = self.draw_date + timedelta(days=CONFIRMATION_DAYS)
        self.status = "drawn"
        
        return self.winner_id
    
    def confirm_reservation(self) -> None:
        """
        Confirm the winner's reservation.
        
        Raises:
            ValueError: If lottery is not in drawn status
        """
        if self.status != "drawn":
            raise ValueError("Lottery must be drawn before confirming")
        
        if not self.winner_id:
            raise ValueError("No winner to confirm")
        
        self.status = "confirmed"
    
    def expire_confirmation(self) -> None:
        """Mark the confirmation as expired."""
        if self.status == "drawn":
            self.status = "expired"
    
    def cancel_lottery(self, reason: str = "") -> None:
        """
        Cancel the lottery.
        
        Args:
            reason (str): Reason for cancellation
        """
        self.status = "cancelled"
        if reason:
            self.notes = f"Cancelled: {reason}"
    
    def is_pending(self) -> bool:
        """Check if lottery is pending."""
        return self.status == "pending"
    
    def is_drawn(self) -> bool:
        """Check if lottery has been drawn."""
        return self.status == "drawn"
    
    def is_confirmed(self) -> bool:
        """Check if winner has confirmed."""
        return self.status == "confirmed"
    
    def is_expired(self) -> bool:
        """Check if confirmation has expired."""
        return self.status == "expired"
    
    def is_cancelled(self) -> bool:
        """Check if lottery was cancelled."""
        return self.status == "cancelled"
    
    def is_confirmation_expired(self) -> bool:
        """
        Check if the confirmation deadline has passed.
        
        Returns:
            bool: True if confirmation deadline has passed
        """
        if not self.confirmation_deadline or self.status != "drawn":
            return False
        
        return datetime.now() > self.confirmation_deadline
    
    def get_time_remaining(self) -> Optional[timedelta]:
        """
        Get time remaining for confirmation.
        
        Returns:
            Optional[timedelta]: Time remaining, or None if not applicable
        """
        if not self.confirmation_deadline or self.status != "drawn":
            return None
        
        remaining = self.confirmation_deadline - datetime.now()
        return remaining if remaining.total_seconds() > 0 else timedelta(0)
    
    def get_summary(self) -> str:
        """
        Get a summary of the lottery.
        
        Returns:
            str: Lottery summary
        """
        lines = [
            f"Lottery ID: {self.lottery_id}",
            f"Period: {self.period_id}",
            f"Participants: {len(self.participants)}",
            f"Status: {self.status.title()}"
        ]
        
        if self.winner_id:
            lines.append(f"Winner: Member #{self.winner_id}")
        
        if self.draw_date:
            lines.append(f"Draw Date: {self.draw_date.strftime('%Y-%m-%d %H:%M')}")
        
        if self.confirmation_deadline:
            lines.append(f"Confirmation Deadline: {self.confirmation_deadline.strftime('%Y-%m-%d %H:%M')}")
            
            if self.status == "drawn":
                remaining = self.get_time_remaining()
                if remaining and remaining.total_seconds() > 0:
                    hours = int(remaining.total_seconds() // 3600)
                    minutes = int((remaining.total_seconds() % 3600) // 60)
                    lines.append(f"Time Remaining: {hours}h {minutes}m")
        
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """
        Convert lottery to dictionary format.
        
        Returns:
            Dict: Lottery data as dictionary
        """
        return {
            'lottery_id': self.lottery_id,
            'period_id': self.period_id,
            'participants': self.participants.copy(),
            'winner_id': self.winner_id,
            'draw_date': self.draw_date.isoformat() if self.draw_date else None,
            'confirmation_deadline': self.confirmation_deadline.isoformat() if self.confirmation_deadline else None,
            'status': self.status,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LotteryRound':
        """
        Create LotteryRound instance from dictionary data.
        
        Args:
            data (Dict): Dictionary containing lottery data
            
        Returns:
            LotteryRound: New LotteryRound instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['lottery_id', 'period_id', 'participants']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse dates
        draw_date = None
        if data.get('draw_date'):
            try:
                draw_date = datetime.fromisoformat(data['draw_date'])
            except ValueError:
                pass
        
        confirmation_deadline = None
        if data.get('confirmation_deadline'):
            try:
                confirmation_deadline = datetime.fromisoformat(data['confirmation_deadline'])
            except ValueError:
                pass
        
        return cls(
            lottery_id=data['lottery_id'],
            period_id=data['period_id'],
            participants=data['participants'].copy(),
            winner_id=data.get('winner_id'),
            draw_date=draw_date,
            confirmation_deadline=confirmation_deadline,
            status=data.get('status', 'pending'),
            notes=data.get('notes', '')
        )
    
    def __str__(self) -> str:
        """Return string representation of lottery."""
        return f"LotteryRound({self.lottery_id}, {self.status})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of lottery."""
        return (f"LotteryRound(lottery_id='{self.lottery_id}', "
                f"period_id='{self.period_id}', "
                f"participants={len(self.participants)}, "
                f"status='{self.status}')")

class LotteryManager:
    """
    Manages lottery operations and history.
    
    This class provides utility methods for managing multiple lotteries,
    tracking history, and ensuring fair distribution.
    """
    
    def __init__(self):
        """Initialize the LotteryManager."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def validate_lottery_list(lotteries: List[Dict]) -> List[str]:
        """
        Validate a list of lottery dictionaries.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        seen_lottery_ids = set()
        
        for i, lottery_data in enumerate(lotteries):
            try:
                # Try to create lottery to validate data
                lottery = LotteryRound.from_dict(lottery_data)
                
                # Check for duplicate lottery IDs
                if lottery.lottery_id in seen_lottery_ids:
                    errors.append(f"Duplicate lottery ID {lottery.lottery_id} at position {i}")
                seen_lottery_ids.add(lottery.lottery_id)
                
            except ValueError as e:
                errors.append(f"Invalid lottery data at position {i}: {e}")
            except KeyError as e:
                errors.append(f"Missing field at position {i}: {e}")
        
        return errors
    
    @staticmethod
    def get_lotteries_by_status(lotteries: List[Dict], status: str) -> List[Dict]:
        """
        Filter lotteries by status.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            status (str): Status to filter by
            
        Returns:
            List[Dict]: Filtered lotteries
        """
        return [l for l in lotteries if l.get('status') == status]
    
    @staticmethod
    def get_pending_lotteries(lotteries: List[Dict]) -> List[Dict]:
        """
        Get all pending lotteries.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            
        Returns:
            List[Dict]: Pending lotteries
        """
        return LotteryManager.get_lotteries_by_status(lotteries, "pending")
    
    @staticmethod
    def get_drawn_lotteries(lotteries: List[Dict]) -> List[Dict]:
        """
        Get all drawn lotteries awaiting confirmation.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            
        Returns:
            List[Dict]: Drawn lotteries
        """
        return LotteryManager.get_lotteries_by_status(lotteries, "drawn")
    
    @staticmethod
    def get_member_lottery_history(lotteries: List[Dict], member_id: int) -> List[Dict]:
        """
        Get lottery history for a specific member.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            member_id (int): Member ID
            
        Returns:
            List[Dict]: Lotteries the member participated in
        """
        member_lotteries = []
        
        for lottery in lotteries:
            participants = lottery.get('participants', [])
            if member_id in participants:
                member_lotteries.append(lottery)
        
        return member_lotteries
    
    @staticmethod
    def get_member_wins(lotteries: List[Dict], member_id: int) -> List[Dict]:
        """
        Get lotteries won by a specific member.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            member_id (int): Member ID
            
        Returns:
            List[Dict]: Lotteries won by the member
        """
        return [l for l in lotteries if l.get('winner_id') == member_id]
    
    @staticmethod
    def calculate_member_stats(lotteries: List[Dict], member_id: int) -> Dict:
        """
        Calculate lottery statistics for a member.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            member_id (int): Member ID
            
        Returns:
            Dict: Member lottery statistics
        """
        participated = LotteryManager.get_member_lottery_history(lotteries, member_id)
        wins = LotteryManager.get_member_wins(lotteries, member_id)
        confirmed_wins = [w for w in wins if w.get('status') == 'confirmed']
        
        participation_count = len(participated)
        win_count = len(wins)
        confirmed_count = len(confirmed_wins)
        
        win_rate = (win_count / participation_count * 100) if participation_count > 0 else 0
        confirmation_rate = (confirmed_count / win_count * 100) if win_count > 0 else 0
        
        return {
            'member_id': member_id,
            'participations': participation_count,
            'wins': win_count,
            'confirmed_wins': confirmed_count,
            'win_rate': round(win_rate, 1),
            'confirmation_rate': round(confirmation_rate, 1)
        }
    
    @staticmethod
    def get_fairness_report(lotteries: List[Dict], member_ids: List[int]) -> Dict:
        """
        Generate a fairness report showing lottery distribution.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            member_ids (List[int]): List of all member IDs
            
        Returns:
            Dict: Fairness report
        """
        member_stats = {}
        
        for member_id in member_ids:
            member_stats[member_id] = LotteryManager.calculate_member_stats(lotteries, member_id)
        
        # Calculate overall statistics
        total_lotteries = len([l for l in lotteries if l.get('status') in ['drawn', 'confirmed', 'expired']])
        total_participations = sum(stats['participations'] for stats in member_stats.values())
        total_wins = sum(stats['wins'] for stats in member_stats.values())
        
        # Find members with highest and lowest win rates
        active_members = [stats for stats in member_stats.values() if stats['participations'] > 0]
        
        if active_members:
            highest_win_rate = max(active_members, key=lambda x: x['win_rate'])
            lowest_win_rate = min(active_members, key=lambda x: x['win_rate'])
        else:
            highest_win_rate = None
            lowest_win_rate = None
        
        return {
            'total_lotteries': total_lotteries,
            'total_participations': total_participations,
            'total_wins': total_wins,
            'average_participation': round(total_participations / len(member_ids), 1) if member_ids else 0,
            'member_stats': member_stats,
            'highest_win_rate': highest_win_rate,
            'lowest_win_rate': lowest_win_rate,
            'active_members': len(active_members)
        }
    
    @staticmethod
    def find_expired_confirmations(lotteries: List[Dict]) -> List[Dict]:
        """
        Find lotteries with expired confirmation deadlines.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            
        Returns:
            List[Dict]: Lotteries with expired confirmations
        """
        expired = []
        drawn_lotteries = LotteryManager.get_drawn_lotteries(lotteries)
        
        for lottery in drawn_lotteries:
            deadline_str = lottery.get('confirmation_deadline')
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str)
                    if datetime.now() > deadline:
                        expired.append(lottery)
                except ValueError:
                    continue
        
        return expired
    
    @staticmethod
    def sort_lotteries_by_date(lotteries: List[Dict], reverse: bool = True) -> List[Dict]:
        """
        Sort lotteries by draw date.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            reverse (bool): Whether to sort in reverse order (newest first)
            
        Returns:
            List[Dict]: Sorted lotteries
        """
        def get_sort_date(lottery):
            draw_date_str = lottery.get('draw_date')
            if draw_date_str:
                try:
                    return datetime.fromisoformat(draw_date_str)
                except ValueError:
                    pass
            # Use a very old date for lotteries without draw dates
            return datetime.min
        
        return sorted(lotteries, key=get_sort_date, reverse=reverse)
    
    @staticmethod
    def format_lottery_summary(lotteries: List[Dict]) -> str:
        """
        Format a summary of lotteries.
        
        Args:
            lotteries (List[Dict]): List of lottery dictionaries
            
        Returns:
            str: Formatted summary
        """
        if not lotteries:
            return "No lotteries"
        
        # Count by status
        status_counts = {}
        for lottery in lotteries:
            status = lottery.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        summary_lines = [f"Total lotteries: {len(lotteries)}"]
        
        status_order = ['pending', 'drawn', 'confirmed', 'expired', 'cancelled']
        for status in status_order:
            if status in status_counts:
                count = status_counts[status]
                summary_lines.append(f"  {status.title()}: {count}")
        
        # Add any other statuses not in the ordered list
        for status, count in status_counts.items():
            if status not in status_order:
                summary_lines.append(f"  {status.title()}: {count}")
        
        return "\n".join(summary_lines)