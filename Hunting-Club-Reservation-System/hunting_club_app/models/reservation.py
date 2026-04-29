"""
Reservation Data Model

This module contains the Reservation and ReservationPeriod classes
for managing cabin reservations in the Hunting Club Reservation System.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

from utils.constants import ReservationStatus, CONFIRMATION_DAYS, format_date_range

@dataclass
class ReservationPeriod:
    """
    Represents a single reservation period (Friday to Thursday).
    
    Attributes:
        period_id (str): Unique identifier for the period
        start_date (datetime): Start date of the period (Friday)
        end_date (datetime): End date of the period (Thursday)
        member_id (Optional[int]): ID of the member who reserved this period
        status (str): Current status of the reservation
        confirmed_date (Optional[datetime]): Date when reservation was confirmed
        lottery_id (Optional[str]): ID of the lottery that assigned this period
    """
    
    period_id: str
    start_date: datetime
    end_date: datetime
    member_id: Optional[int] = None
    status: str = ReservationStatus.AVAILABLE
    confirmed_date: Optional[datetime] = None
    lottery_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate reservation period data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate reservation period data.
        
        Raises:
            ValueError: If any field is invalid
        """
        if not self.period_id:
            raise ValueError("Period ID cannot be empty")
        
        if not isinstance(self.start_date, datetime):
            raise ValueError("Start date must be a datetime object")
        
        if not isinstance(self.end_date, datetime):
            raise ValueError("End date must be a datetime object")
        
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
        
        # Check if period is exactly 7 days
        expected_end = self.start_date + timedelta(days=6)
        if self.end_date.date() != expected_end.date():
            raise ValueError("Reservation period must be exactly 7 days")
        
        # Validate status
        valid_statuses = [
            ReservationStatus.AVAILABLE,
            ReservationStatus.RESERVED,
            ReservationStatus.IN_LOTTERY,
            ReservationStatus.PENDING_CONFIRMATION,
            ReservationStatus.EXPIRED
        ]
        
        if self.status not in valid_statuses:
            raise ValueError(f"Invalid status: {self.status}")
        
        # Validate member_id if provided
        if self.member_id is not None and (not isinstance(self.member_id, int) or self.member_id <= 0):
            raise ValueError("Member ID must be a positive integer")
    
    def is_available(self) -> bool:
        """
        Check if the period is available for reservation.
        
        Returns:
            bool: True if period is available
        """
        return self.status == ReservationStatus.AVAILABLE
    
    def is_reserved(self) -> bool:
        """
        Check if the period is reserved.
        
        Returns:
            bool: True if period is reserved
        """
        return self.status == ReservationStatus.RESERVED
    
    def is_in_lottery(self) -> bool:
        """
        Check if the period is currently in a lottery.
        
        Returns:
            bool: True if period is in lottery
        """
        return self.status == ReservationStatus.IN_LOTTERY
    
    def is_pending_confirmation(self) -> bool:
        """
        Check if the period is pending confirmation.
        
        Returns:
            bool: True if period is pending confirmation
        """
        return self.status == ReservationStatus.PENDING_CONFIRMATION
    
    def is_expired(self) -> bool:
        """
        Check if the period has expired.
        
        Returns:
            bool: True if period is expired
        """
        return self.status == ReservationStatus.EXPIRED
    
    def can_be_reserved(self) -> bool:
        """
        Check if the period can be reserved (available or expired).
        
        Returns:
            bool: True if period can be reserved
        """
        return self.status in [ReservationStatus.AVAILABLE, ReservationStatus.EXPIRED]
    
    def reserve_for_member(self, member_id: int, lottery_id: Optional[str] = None) -> None:
        """
        Reserve the period for a specific member.
        
        Args:
            member_id (int): ID of the member
            lottery_id (Optional[str]): ID of the lottery (if applicable)
            
        Raises:
            ValueError: If period cannot be reserved
        """
        if not self.can_be_reserved():
            raise ValueError(f"Period {self.period_id} cannot be reserved (status: {self.status})")
        
        self.member_id = member_id
        self.status = ReservationStatus.RESERVED
        self.confirmed_date = datetime.now()
        self.lottery_id = lottery_id
    
    def set_pending_confirmation(self, member_id: int, lottery_id: str) -> None:
        """
        Set the period as pending confirmation for a member.
        
        Args:
            member_id (int): ID of the member
            lottery_id (str): ID of the lottery
            
        Raises:
            ValueError: If period cannot be set to pending
        """
        if not self.can_be_reserved():
            raise ValueError(f"Period {self.period_id} cannot be set to pending (status: {self.status})")
        
        self.member_id = member_id
        self.status = ReservationStatus.PENDING_CONFIRMATION
        self.lottery_id = lottery_id
        self.confirmed_date = None
    
    def confirm_reservation(self) -> None:
        """
        Confirm a pending reservation.
        
        Raises:
            ValueError: If reservation is not pending confirmation
        """
        if not self.is_pending_confirmation():
            raise ValueError(f"Period {self.period_id} is not pending confirmation")
        
        self.status = ReservationStatus.RESERVED
        self.confirmed_date = datetime.now()
    
    def cancel_reservation(self) -> None:
        """Cancel the reservation and make the period available."""
        self.member_id = None
        self.status = ReservationStatus.AVAILABLE
        self.confirmed_date = None
        self.lottery_id = None
    
    def expire_confirmation(self) -> None:
        """Mark the confirmation as expired."""
        if self.is_pending_confirmation():
            self.status = ReservationStatus.EXPIRED
    
    def reset_to_available(self) -> None:
        """Reset the period to available status."""
        self.member_id = None
        self.status = ReservationStatus.AVAILABLE
        self.confirmed_date = None
        self.lottery_id = None
    
    def get_display_text(self) -> str:
        """
        Get formatted text for displaying the period.
        
        Returns:
            str: Formatted period text
        """
        date_range = format_date_range(self.start_date, self.end_date)
        return f"{date_range}"
    
    def get_status_display(self) -> str:
        """
        Get user-friendly status text.
        
        Returns:
            str: User-friendly status
        """
        status_map = {
            ReservationStatus.AVAILABLE: "Available",
            ReservationStatus.RESERVED: "Reserved",
            ReservationStatus.IN_LOTTERY: "In Lottery",
            ReservationStatus.PENDING_CONFIRMATION: "Pending Confirmation",
            ReservationStatus.EXPIRED: "Expired"
        }
        return status_map.get(self.status, self.status)
    
    def get_tooltip_text(self, member_name: Optional[str] = None) -> str:
        """
        Get tooltip text for the period.
        
        Args:
            member_name (Optional[str]): Name of the member (if reserved)
            
        Returns:
            str: Tooltip text
        """
        lines = [
            f"Period: {self.get_display_text()}",
            f"Status: {self.get_status_display()}"
        ]
        
        if self.member_id and member_name:
            lines.append(f"Member: {member_name}")
        
        if self.confirmed_date:
            lines.append(f"Confirmed: {self.confirmed_date.strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict:
        """
        Convert reservation period to dictionary format.
        
        Returns:
            Dict: Period data as dictionary
        """
        return {
            'period_id': self.period_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'member_id': self.member_id,
            'status': self.status,
            'confirmed_date': self.confirmed_date.isoformat() if self.confirmed_date else None,
            'lottery_id': self.lottery_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReservationPeriod':
        """
        Create ReservationPeriod instance from dictionary data.
        
        Args:
            data (Dict): Dictionary containing period data
            
        Returns:
            ReservationPeriod: New ReservationPeriod instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = ['period_id', 'start_date', 'end_date']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(data['start_date'])
            end_date = datetime.fromisoformat(data['end_date'])
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        
        # Parse confirmed_date if present
        confirmed_date = None
        if data.get('confirmed_date'):
            try:
                confirmed_date = datetime.fromisoformat(data['confirmed_date'])
            except ValueError:
                pass  # Ignore invalid confirmed_date
        
        return cls(
            period_id=data['period_id'],
            start_date=start_date,
            end_date=end_date,
            member_id=data.get('member_id'),
            status=data.get('status', ReservationStatus.AVAILABLE),
            confirmed_date=confirmed_date,
            lottery_id=data.get('lottery_id')
        )
    
    def __str__(self) -> str:
        """Return string representation of reservation period."""
        return f"ReservationPeriod({self.period_id}, {self.status})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of reservation period."""
        return (f"ReservationPeriod(period_id='{self.period_id}', "
                f"start_date={self.start_date.date()}, "
                f"end_date={self.end_date.date()}, "
                f"status='{self.status}', "
                f"member_id={self.member_id})")

class ReservationManager:
    """
    Manages operations on reservation collections.
    
    This class provides utility methods for working with groups of reservations,
    such as filtering, searching, and validation.
    """
    
    def __init__(self):
        """Initialize the ReservationManager."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def validate_reservation_list(reservations: List[Dict]) -> List[str]:
        """
        Validate a list of reservation dictionaries.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        seen_period_ids = set()
        
        for i, reservation_data in enumerate(reservations):
            try:
                # Try to create reservation to validate data
                reservation = ReservationPeriod.from_dict(reservation_data)
                
                # Check for duplicate period IDs
                if reservation.period_id in seen_period_ids:
                    errors.append(f"Duplicate period ID {reservation.period_id} at position {i}")
                seen_period_ids.add(reservation.period_id)
                
            except ValueError as e:
                errors.append(f"Invalid reservation data at position {i}: {e}")
            except KeyError as e:
                errors.append(f"Missing field at position {i}: {e}")
        
        return errors
    
    @staticmethod
    def get_reservations_by_status(reservations: List[Dict], status: str) -> List[Dict]:
        """
        Filter reservations by status.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            status (str): Status to filter by
            
        Returns:
            List[Dict]: Filtered reservations
        """
        return [r for r in reservations if r.get('status') == status]
    
    @staticmethod
    def get_reservations_by_member(reservations: List[Dict], member_id: int) -> List[Dict]:
        """
        Filter reservations by member ID.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            member_id (int): Member ID to filter by
            
        Returns:
            List[Dict]: Filtered reservations
        """
        return [r for r in reservations if r.get('member_id') == member_id]
    
    @staticmethod
    def get_available_periods(reservations: List[Dict]) -> List[Dict]:
        """
        Get all available reservation periods.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            List[Dict]: Available reservations
        """
        return ReservationManager.get_reservations_by_status(reservations, ReservationStatus.AVAILABLE)
    
    @staticmethod
    def get_reserved_periods(reservations: List[Dict]) -> List[Dict]:
        """
        Get all reserved periods.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            List[Dict]: Reserved periods
        """
        return ReservationManager.get_reservations_by_status(reservations, ReservationStatus.RESERVED)
    
    @staticmethod
    def sort_reservations_by_date(reservations: List[Dict], reverse: bool = False) -> List[Dict]:
        """
        Sort reservations by start date.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            reverse (bool): Whether to sort in reverse order
            
        Returns:
            List[Dict]: Sorted reservations
        """
        try:
            return sorted(
                reservations,
                key=lambda r: datetime.fromisoformat(r['start_date']),
                reverse=reverse
            )
        except (KeyError, ValueError):
            # Return original list if sorting fails
            return reservations
    
    @staticmethod
    def find_conflicts(reservations: List[Dict]) -> List[str]:
        """
        Find scheduling conflicts in reservations.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            List[str]: List of conflict descriptions
        """
        conflicts = []
        
        # Check for overlapping periods
        sorted_reservations = ReservationManager.sort_reservations_by_date(reservations)
        
        for i in range(len(sorted_reservations) - 1):
            current = sorted_reservations[i]
            next_reservation = sorted_reservations[i + 1]
            
            try:
                current_end = datetime.fromisoformat(current['end_date'])
                next_start = datetime.fromisoformat(next_reservation['start_date'])
                
                if current_end >= next_start:
                    conflicts.append(
                        f"Overlapping periods: {current['period_id']} and {next_reservation['period_id']}"
                    )
            except (KeyError, ValueError):
                continue
        
        return conflicts
    
    @staticmethod
    def get_member_reservation_count(reservations: List[Dict], member_id: int) -> int:
        """
        Count reservations for a specific member.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            member_id (int): Member ID
            
        Returns:
            int: Number of reservations for the member
        """
        return len(ReservationManager.get_reservations_by_member(reservations, member_id))
    
    @staticmethod
    def check_member_eligibility(reservations: List[Dict], member_id: int, max_reservations: int = 1) -> bool:
        """
        Check if a member is eligible for additional reservations.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            member_id (int): Member ID to check
            max_reservations (int): Maximum allowed reservations per member
            
        Returns:
            bool: True if member is eligible for more reservations
        """
        current_count = ReservationManager.get_member_reservation_count(reservations, member_id)
        return current_count < max_reservations
    
    @staticmethod
    def get_expired_confirmations(reservations: List[Dict], lottery_history: List[Dict]) -> List[Dict]:
        """
        Get reservations with expired confirmation periods.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            lottery_history (List[Dict]): List of lottery records
            
        Returns:
            List[Dict]: Reservations with expired confirmations
        """
        expired = []
        pending_reservations = ReservationManager.get_reservations_by_status(
            reservations, ReservationStatus.PENDING_CONFIRMATION
        )
        
        for reservation in pending_reservations:
            lottery_id = reservation.get('lottery_id')
            if not lottery_id:
                continue
            
            # Find the corresponding lottery record
            lottery_record = next(
                (l for l in lottery_history if l.get('lottery_id') == lottery_id),
                None
            )
            
            if lottery_record and lottery_record.get('confirmation_deadline'):
                try:
                    deadline = datetime.fromisoformat(lottery_record['confirmation_deadline'])
                    if datetime.now() > deadline:
                        expired.append(reservation)
                except ValueError:
                    continue
        
        return expired
    
    @staticmethod
    def get_reservations_by_date_range(reservations: List[Dict], start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get reservations within a specific date range.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            start_date (datetime): Range start date
            end_date (datetime): Range end date
            
        Returns:
            List[Dict]: Reservations within the date range
        """
        filtered = []
        
        for reservation in reservations:
            try:
                res_start = datetime.fromisoformat(reservation['start_date'])
                res_end = datetime.fromisoformat(reservation['end_date'])
                
                # Check if reservation overlaps with the date range
                if res_start <= end_date and res_end >= start_date:
                    filtered.append(reservation)
            except (KeyError, ValueError):
                continue
        
        return filtered
    
    @staticmethod
    def get_reservation_statistics(reservations: List[Dict]) -> Dict:
        """
        Generate statistics for reservations.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            Dict: Statistics dictionary
        """
        stats = {
            'total_periods': len(reservations),
            'available': 0,
            'reserved': 0,
            'in_lottery': 0,
            'pending_confirmation': 0,
            'expired': 0,
            'utilization_rate': 0,
            'members_with_reservations': set()
        }
        
        for reservation in reservations:
            status = reservation.get('status', 'unknown')
            
            if status == ReservationStatus.AVAILABLE:
                stats['available'] += 1
            elif status == ReservationStatus.RESERVED:
                stats['reserved'] += 1
                member_id = reservation.get('member_id')
                if member_id:
                    stats['members_with_reservations'].add(member_id)
            elif status == ReservationStatus.IN_LOTTERY:
                stats['in_lottery'] += 1
            elif status == ReservationStatus.PENDING_CONFIRMATION:
                stats['pending_confirmation'] += 1
            elif status == ReservationStatus.EXPIRED:
                stats['expired'] += 1
        
        # Calculate utilization rate (reserved + pending / total)
        if stats['total_periods'] > 0:
            utilized = stats['reserved'] + stats['pending_confirmation']
            stats['utilization_rate'] = (utilized / stats['total_periods']) * 100
        
        # Convert set to count
        stats['members_with_reservations'] = len(stats['members_with_reservations'])
        
        return stats
    
    @staticmethod
    def find_next_available_period(reservations: List[Dict], after_date: Optional[datetime] = None) -> Optional[Dict]:
        """
        Find the next available reservation period.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            after_date (Optional[datetime]): Find periods after this date
            
        Returns:
            Optional[Dict]: Next available period or None
        """
        if after_date is None:
            after_date = datetime.now()
        
        available_periods = ReservationManager.get_available_periods(reservations)
        future_periods = []
        
        for period in available_periods:
            try:
                start_date = datetime.fromisoformat(period['start_date'])
                if start_date >= after_date:
                    future_periods.append(period)
            except (KeyError, ValueError):
                continue
        
        if future_periods:
            # Sort by start date and return the earliest
            sorted_periods = ReservationManager.sort_reservations_by_date(future_periods)
            return sorted_periods[0]
        
        return None
    
    @staticmethod
    def get_member_reservation_history(reservations: List[Dict], member_id: int) -> Dict:
        """
        Get detailed reservation history for a member.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            member_id (int): Member ID
            
        Returns:
            Dict: Member reservation history
        """
        member_reservations = ReservationManager.get_reservations_by_member(reservations, member_id)
        
        history = {
            'member_id': member_id,
            'total_reservations': len(member_reservations),
            'confirmed_reservations': 0,
            'pending_reservations': 0,
            'expired_reservations': 0,
            'reservations': []
        }
        
        for reservation in member_reservations:
            status = reservation.get('status')
            
            if status == ReservationStatus.RESERVED:
                history['confirmed_reservations'] += 1
            elif status == ReservationStatus.PENDING_CONFIRMATION:
                history['pending_reservations'] += 1
            elif status == ReservationStatus.EXPIRED:
                history['expired_reservations'] += 1
            
            # Add to detailed list
            try:
                start_date = datetime.fromisoformat(reservation['start_date'])
                history['reservations'].append({
                    'period_id': reservation['period_id'],
                    'start_date': start_date,
                    'status': status,
                    'confirmed_date': reservation.get('confirmed_date'),
                    'lottery_id': reservation.get('lottery_id')
                })
            except (KeyError, ValueError):
                continue
        
        # Sort by start date
        history['reservations'].sort(key=lambda x: x['start_date'])
        
        return history
    
    @staticmethod
    def validate_period_transition(current_status: str, new_status: str) -> bool:
        """
        Validate if a status transition is allowed.
        
        Args:
            current_status (str): Current period status
            new_status (str): Desired new status
            
        Returns:
            bool: True if transition is valid
        """
        # Define valid transitions
        valid_transitions = {
            ReservationStatus.AVAILABLE: [
                ReservationStatus.IN_LOTTERY,
                ReservationStatus.RESERVED,
                ReservationStatus.PENDING_CONFIRMATION
            ],
            ReservationStatus.IN_LOTTERY: [
                ReservationStatus.AVAILABLE,
                ReservationStatus.PENDING_CONFIRMATION
            ],
            ReservationStatus.PENDING_CONFIRMATION: [
                ReservationStatus.RESERVED,
                ReservationStatus.EXPIRED,
                ReservationStatus.AVAILABLE
            ],
            ReservationStatus.EXPIRED: [
                ReservationStatus.AVAILABLE
            ],
            ReservationStatus.RESERVED: [
                ReservationStatus.AVAILABLE  # For cancellations
            ]
        }
        
        allowed_transitions = valid_transitions.get(current_status, [])
        return new_status in allowed_transitions
    
    @staticmethod
    def format_reservation_summary(reservations: List[Dict]) -> str:
        """
        Format a summary of reservations.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            
        Returns:
            str: Formatted summary
        """
        if not reservations:
            return "No reservations"
        
        stats = ReservationManager.get_reservation_statistics(reservations)
        
        summary_lines = [f"Total periods: {stats['total_periods']}"]
        summary_lines.append(f"Available: {stats['available']}")
        summary_lines.append(f"Reserved: {stats['reserved']}")
        summary_lines.append(f"In Lottery: {stats['in_lottery']}")
        summary_lines.append(f"Pending Confirmation: {stats['pending_confirmation']}")
        summary_lines.append(f"Expired: {stats['expired']}")
        summary_lines.append(f"Utilization Rate: {stats['utilization_rate']:.1f}%")
        summary_lines.append(f"Members with Reservations: {stats['members_with_reservations']}")
        
        return "\n".join(summary_lines)
    
    @staticmethod
    def export_reservations_csv(reservations: List[Dict], filename: str) -> bool:
        """
        Export reservations to CSV format.
        
        Args:
            reservations (List[Dict]): List of reservation dictionaries
            filename (str): Output filename
            
        Returns:
            bool: True if export was successful
        """
        try:
            import csv
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'period_id', 'start_date', 'end_date', 'member_id',
                    'status', 'confirmed_date', 'lottery_id'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for reservation in reservations:
                    row = {}
                    for field in fieldnames:
                        row[field] = reservation.get(field, '')
                    writer.writerow(row)
            
            return True
            
        except Exception:
            return False