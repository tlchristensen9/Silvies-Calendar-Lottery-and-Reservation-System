# JSON file operations
"""
Data Manager Module

This module handles all data persistence operations for the Hunting Club
Reservation System. It manages JSON files for members, reservations, and
lottery history.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from utils.constants import (
    DATA_DIR, MEMBERS_FILE, RESERVATIONS_FILE, LOTTERY_HISTORY_FILE,
    DEFAULT_MEMBERS, get_season_periods, get_period_id, ReservationStatus
)

class DataManager:
    """
    Manages all data persistence operations for the application.
    
    This class handles reading and writing JSON files for members,
    reservations, and lottery history. It also provides methods for
    initializing default data and managing data integrity.
    """
    
    def __init__(self):
        """Initialize the DataManager with file paths."""
        self.data_dir = DATA_DIR
        self.members_file = os.path.join(self.data_dir, MEMBERS_FILE)
        self.reservations_file = os.path.join(self.data_dir, RESERVATIONS_FILE)
        self.lottery_history_file = os.path.join(self.data_dir, LOTTERY_HISTORY_FILE)
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    def _read_json_file(self, filepath: str, default_data: Any = None) -> Any:
        """
        Read and parse a JSON file.
        
        Args:
            filepath (str): Path to the JSON file
            default_data (Any): Default data to return if file doesn't exist
            
        Returns:
            Any: Parsed JSON data or default_data
            
        Raises:
            Exception: If file exists but cannot be read or parsed
        """
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    self.logger.debug(f"Successfully read {filepath}")
                    return data
            else:
                self.logger.info(f"File {filepath} does not exist, returning default data")
                return default_data or {}
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {filepath}: {e}")
            raise Exception(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            self.logger.error(f"Error reading {filepath}: {e}")
            raise Exception(f"Could not read {filepath}: {e}")
    
    def _write_json_file(self, filepath: str, data: Any) -> None:
        """
        Write data to a JSON file.
        
        Args:
            filepath (str): Path to the JSON file
            data (Any): Data to write
            
        Raises:
            Exception: If file cannot be written
        """
        try:
            # Create backup if file exists
            if os.path.exists(filepath):
                backup_path = f"{filepath}.backup"
                os.rename(filepath, backup_path)
            
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Successfully wrote {filepath}")
            
            # Remove backup on successful write
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            self.logger.error(f"Error writing {filepath}: {e}")
            
            # Restore backup if it exists
            backup_path = f"{filepath}.backup"
            if os.path.exists(backup_path):
                os.rename(backup_path, filepath)
                
            raise Exception(f"Could not write {filepath}: {e}")
    
    def initialize_data_files(self) -> None:
        """
        Initialize all data files with default data if they don't exist.
        """
        try:
            # Initialize members file
            if not os.path.exists(self.members_file):
                self._write_json_file(self.members_file, DEFAULT_MEMBERS)
                self.logger.info("Created default members file")
            
            # Initialize reservations file
            if not os.path.exists(self.reservations_file):
                default_reservations = self._generate_default_reservations()
                self._write_json_file(self.reservations_file, default_reservations)
                self.logger.info("Created default reservations file")
            
            # Initialize lottery history file
            if not os.path.exists(self.lottery_history_file):
                self._write_json_file(self.lottery_history_file, [])
                self.logger.info("Created default lottery history file")
                
        except Exception as e:
            self.logger.error(f"Error initializing data files: {e}")
            raise
    
    def _generate_default_reservations(self) -> List[Dict]:
        """
        Generate default reservation periods for the season.
        
        Returns:
            List[Dict]: List of default reservation periods
        """
        reservations = []
        periods = get_season_periods()
        
        for start_date, end_date in periods:
            period_id = get_period_id(start_date, end_date)
            reservation = {
                "period_id": period_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "member_id": None,
                "status": ReservationStatus.AVAILABLE,
                "confirmed_date": None,
                "lottery_id": None
            }
            reservations.append(reservation)
        
        return reservations
    
    # Member Management Methods
    def get_all_members(self) -> List[Dict]:
        """
        Get all club members.
        
        Returns:
            List[Dict]: List of all members
        """
        return self._read_json_file(self.members_file, [])
    
    def get_member_by_id(self, member_id: int) -> Optional[Dict]:
        """
        Get a specific member by ID.
        
        Args:
            member_id (int): Member ID
            
        Returns:
            Optional[Dict]: Member data or None if not found
        """
        members = self.get_all_members()
        return next((m for m in members if m['id'] == member_id), None)
    
    def get_member_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a specific member by name.
        
        Args:
            name (str): Member name
            
        Returns:
            Optional[Dict]: Member data or None if not found
        """
        members = self.get_all_members()
        return next((m for m in members if m['name'] == name), None)
    
    # Reservation Management Methods
    def get_all_reservations(self) -> List[Dict]:
        """
        Get all reservations.
        
        Returns:
            List[Dict]: List of all reservations
        """
        return self._read_json_file(self.reservations_file, [])
    
    def get_reservation_by_period_id(self, period_id: str) -> Optional[Dict]:
        """
        Get a specific reservation by period ID.
        
        Args:
            period_id (str): Period ID
            
        Returns:
            Optional[Dict]: Reservation data or None if not found
        """
        reservations = self.get_all_reservations()
        return next((r for r in reservations if r['period_id'] == period_id), None)
    
    def get_reservations_by_member_id(self, member_id: int) -> List[Dict]:
        """
        Get all reservations for a specific member.
        
        Args:
            member_id (int): Member ID
            
        Returns:
            List[Dict]: List of reservations for the member
        """
        reservations = self.get_all_reservations()
        return [r for r in reservations if r['member_id'] == member_id]
    
    def get_reservations_by_status(self, status: str) -> List[Dict]:
        """
        Get all reservations with a specific status.
        
        Args:
            status (str): Reservation status
            
        Returns:
            List[Dict]: List of reservations with the specified status
        """
        reservations = self.get_all_reservations()
        return [r for r in reservations if r['status'] == status]
    
    def update_reservation(self, period_id: str, updates: Dict) -> bool:
        """
        Update a reservation with new data.
        
        Args:
            period_id (str): Period ID of the reservation to update
            updates (Dict): Dictionary of fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            reservations = self.get_all_reservations()
            
            for reservation in reservations:
                if reservation['period_id'] == period_id:
                    reservation.update(updates)
                    self._write_json_file(self.reservations_file, reservations)
                    self.logger.info(f"Updated reservation {period_id}")
                    return True
            
            self.logger.warning(f"Reservation {period_id} not found for update")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating reservation {period_id}: {e}")
            return False
    
    def reset_reservation(self, period_id: str) -> bool:
        """
        Reset a reservation to available status.
        
        Args:
            period_id (str): Period ID of the reservation to reset
            
        Returns:
            bool: True if reset was successful, False otherwise
        """
        return self.update_reservation(period_id, {
            'member_id': None,
            'status': ReservationStatus.AVAILABLE,
            'confirmed_date': None,
            'lottery_id': None
        })
    
    # Lottery Management Methods
    def get_lottery_history(self) -> List[Dict]:
        """
        Get all lottery history records.
        
        Returns:
            List[Dict]: List of lottery history records
        """
        return self._read_json_file(self.lottery_history_file, [])
    
    def add_lottery_record(self, lottery_data: Dict) -> bool:
        """
        Add a new lottery record to the history.
        
        Args:
            lottery_data (Dict): Lottery record data
            
        Returns:
            bool: True if record was added successfully, False otherwise
        """
        try:
            history = self.get_lottery_history()
            history.append(lottery_data)
            self._write_json_file(self.lottery_history_file, history)
            self.logger.info(f"Added lottery record {lottery_data.get('lottery_id', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding lottery record: {e}")
            return False
    
    def get_lottery_by_id(self, lottery_id: str) -> Optional[Dict]:
        """
        Get a specific lottery record by ID.
        
        Args:
            lottery_id (str): Lottery ID
            
        Returns:
            Optional[Dict]: Lottery record or None if not found
        """
        history = self.get_lottery_history()
        return next((l for l in history if l['lottery_id'] == lottery_id), None)
    
    def update_lottery_record(self, lottery_id: str, updates: Dict) -> bool:
        """
        Update a lottery record with new data.
        
        Args:
            lottery_id (str): Lottery ID
            updates (Dict): Dictionary of fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            history = self.get_lottery_history()
            
            for lottery in history:
                if lottery['lottery_id'] == lottery_id:
                    lottery.update(updates)
                    self._write_json_file(self.lottery_history_file, history)
                    self.logger.info(f"Updated lottery record {lottery_id}")
                    return True
            
            self.logger.warning(f"Lottery record {lottery_id} not found for update")
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating lottery record {lottery_id}: {e}")
            return False
    
    # Data Integrity Methods
    def cleanup_expired_confirmations(self) -> int:
        """
        Clean up expired confirmation periods.
        
        Returns:
            int: Number of expired confirmations cleaned up
        """
        try:
            reservations = self.get_all_reservations()
            cleaned_count = 0
            
            for reservation in reservations:
                if reservation['status'] == ReservationStatus.PENDING_CONFIRMATION:
                    # Check if confirmation period has expired
                    lottery_history = self.get_lottery_history()
                    lottery_record = next(
                        (l for l in lottery_history if l['lottery_id'] == reservation.get('lottery_id')),
                        None
                    )
                    
                    if lottery_record:
                        deadline = datetime.fromisoformat(lottery_record['confirmation_deadline'])
                        if datetime.now() > deadline:
                            reservation['status'] = ReservationStatus.EXPIRED
                            cleaned_count += 1
            
            if cleaned_count > 0:
                self._write_json_file(self.reservations_file, reservations)
                self.logger.info(f"Cleaned up {cleaned_count} expired confirmations")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired confirmations: {e}")
            return 0
    
    def validate_data_integrity(self) -> Dict[str, List[str]]:
        """
        Validate data integrity across all files.
        
        Returns:
            Dict[str, List[str]]: Dictionary of validation issues by category
        """
        issues = {
            'members': [],
            'reservations': [],
            'lottery_history': []
        }
        
        try:
            # Validate members
            members = self.get_all_members()
            member_ids = set()
            
            for member in members:
                if member['id'] in member_ids:
                    issues['members'].append(f"Duplicate member ID: {member['id']}")
                member_ids.add(member['id'])
                
                required_fields = ['id', 'name', 'email', 'phone']
                for field in required_fields:
                    if field not in member or not member[field]:
                        issues['members'].append(f"Missing {field} for member {member.get('id', 'unknown')}")
            
            # Validate reservations
            reservations = self.get_all_reservations()
            period_ids = set()
            
            for reservation in reservations:
                if reservation['period_id'] in period_ids:
                    issues['reservations'].append(f"Duplicate period ID: {reservation['period_id']}")
                period_ids.add(reservation['period_id'])
                
                if reservation['member_id'] and reservation['member_id'] not in member_ids:
                    issues['reservations'].append(f"Invalid member ID {reservation['member_id']} in reservation {reservation['period_id']}")
            
            # Validate lottery history
            lottery_history = self.get_lottery_history()
            lottery_ids = set()
            
            for lottery in lottery_history:
                if lottery['lottery_id'] in lottery_ids:
                    issues['lottery_history'].append(f"Duplicate lottery ID: {lottery['lottery_id']}")
                lottery_ids.add(lottery['lottery_id'])
                
                if lottery['period_id'] not in period_ids:
                    issues['lottery_history'].append(f"Invalid period ID {lottery['period_id']} in lottery {lottery['lottery_id']}")
        
        except Exception as e:
            self.logger.error(f"Error validating data integrity: {e}")
            issues['general'] = [f"Validation error: {e}"]
        
        return issues
    
    def backup_data(self) -> str:
        """
        Create a backup of all data files.
        
        Returns:
            str: Path to the backup directory
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = os.path.join(self.data_dir, f"backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy all data files to backup directory
            files_to_backup = [
                (self.members_file, MEMBERS_FILE),
                (self.reservations_file, RESERVATIONS_FILE),
                (self.lottery_history_file, LOTTERY_HISTORY_FILE)
            ]
            
            for source_file, filename in files_to_backup:
                if os.path.exists(source_file):
                    backup_file = os.path.join(backup_dir, filename)
                    with open(source_file, 'r', encoding='utf-8') as src:
                        with open(backup_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
            
            self.logger.info(f"Created data backup at {backup_dir}")
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"Error creating data backup: {e}")
            raise Exception(f"Could not create backup: {e}")
    
    def restore_from_backup(self, backup_dir: str) -> bool:
        """
        Restore data from a backup directory.
        
        Args:
            backup_dir (str): Path to the backup directory
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        try:
            files_to_restore = [
                (MEMBERS_FILE, self.members_file),
                (RESERVATIONS_FILE, self.reservations_file),
                (LOTTERY_HISTORY_FILE, self.lottery_history_file)
            ]
            
            for filename, target_file in files_to_restore:
                backup_file = os.path.join(backup_dir, filename)
                if os.path.exists(backup_file):
                    with open(backup_file, 'r', encoding='utf-8') as src:
                        with open(target_file, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
            
            self.logger.info(f"Restored data from backup {backup_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring from backup: {e}")
            return False