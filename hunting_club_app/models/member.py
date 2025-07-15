# Member data model
"""
Member Data Model

This module contains the Member class and related functionality for
managing club member data in the Hunting Club Reservation System.
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

@dataclass
class Member:
    """
    Represents a hunting club member.
    
    Attributes:
        id (int): Unique member identifier
        name (str): Full name of the member
        email (str): Email address
        phone (str): Phone number
    """
    
    id: int
    name: str
    email: str
    phone: str
    
    def __post_init__(self):
        """Validate member data after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate member data fields.
        
        Raises:
            ValueError: If any field is invalid
        """
        if not isinstance(self.id, int) or self.id <= 0:
            raise ValueError("Member ID must be a positive integer")
        
        if not self.name or not self.name.strip():
            raise ValueError("Member name cannot be empty")
        
        if not self.is_valid_email(self.email):
            raise ValueError(f"Invalid email address: {self.email}")
        
        if not self.is_valid_phone(self.phone):
            raise ValueError(f"Invalid phone number: {self.phone}")
        
        # Normalize data
        self.name = self.name.strip()
        self.email = self.email.strip().lower()
        self.phone = self.normalize_phone(self.phone)
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email (str): Email address to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        if not email:
            return False
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            bool: True if phone is valid, False otherwise
        """
        if not phone:
            return False
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid US phone number (10 digits)
        return len(digits_only) == 10
    
    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize phone number to standard format.
        
        Args:
            phone (str): Phone number to normalize
            
        Returns:
            str: Normalized phone number in format XXX-XXX-XXXX
        """
        digits_only = re.sub(r'\D', '', phone)
        
        if len(digits_only) == 10:
            return f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
        
        return phone  # Return as-is if can't normalize
    
    def to_dict(self) -> Dict:
        """
        Convert member to dictionary format.
        
        Returns:
            Dict: Member data as dictionary
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Member':
        """
        Create Member instance from dictionary data.
        
        Args:
            data (Dict): Dictionary containing member data
            
        Returns:
            Member: New Member instance
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['id', 'name', 'email', 'phone']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return cls(
            id=data['id'],
            name=data['name'],
            email=data['email'],
            phone=data['phone']
        )
    
    def __str__(self) -> str:
        """Return string representation of member."""
        return f"Member(id={self.id}, name='{self.name}')"
    
    def __repr__(self) -> str:
        """Return detailed string representation of member."""
        return (f"Member(id={self.id}, name='{self.name}', "
                f"email='{self.email}', phone='{self.phone}')")
    
    def __eq__(self, other) -> bool:
        """Check equality based on member ID."""
        if not isinstance(other, Member):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Return hash based on member ID."""
        return hash(self.id)
    
    def get_display_name(self) -> str:
        """
        Get member name formatted for display in UI.
        
        Returns:
            str: Formatted display name
        """
        return f"{self.name} (#{self.id})"
    
    def get_contact_info(self) -> str:
        """
        Get formatted contact information.
        
        Returns:
            str: Formatted contact information
        """
        return f"Email: {self.email}\nPhone: {self.phone}"
    
    def matches_search(self, search_term: str) -> bool:
        """
        Check if member matches a search term.
        
        Args:
            search_term (str): Search term to match against
            
        Returns:
            bool: True if member matches search term
        """
        if not search_term:
            return True
        
        search_term = search_term.lower().strip()
        
        # Search in name, email, and phone
        searchable_fields = [
            self.name.lower(),
            self.email.lower(),
            self.phone,
            str(self.id)
        ]
        
        return any(search_term in field for field in searchable_fields)

class MemberManager:
    """
    Manages operations on member collections.
    
    This class provides utility methods for working with groups of members,
    such as searching, sorting, and validation.
    """
    
    def __init__(self):
        """Initialize the MemberManager."""
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def validate_member_list(members: List[Dict]) -> List[str]:
        """
        Validate a list of member dictionaries.
        
        Args:
            members (List[Dict]): List of member dictionaries
            
        Returns:
            List[str]: List of validation errors
        """
        errors = []
        seen_ids = set()
        seen_emails = set()
        
        for i, member_data in enumerate(members):
            try:
                # Try to create member to validate data
                member = Member.from_dict(member_data)
                
                # Check for duplicate IDs
                if member.id in seen_ids:
                    errors.append(f"Duplicate member ID {member.id} at position {i}")
                seen_ids.add(member.id)
                
                # Check for duplicate emails
                if member.email in seen_emails:
                    errors.append(f"Duplicate email {member.email} for member {member.id}")
                seen_emails.add(member.email)
                
            except ValueError as e:
                errors.append(f"Invalid member data at position {i}: {e}")
            except KeyError as e:
                errors.append(f"Missing field at position {i}: {e}")
        
        return errors
    
    @staticmethod
    def search_members(members: List[Dict], search_term: str) -> List[Dict]:
        """
        Search for members matching a search term.
        
        Args:
            members (List[Dict]): List of member dictionaries
            search_term (str): Search term
            
        Returns:
            List[Dict]: Filtered list of members
        """
        if not search_term:
            return members
        
        matching_members = []
        
        for member_data in members:
            try:
                member = Member.from_dict(member_data)
                if member.matches_search(search_term):
                    matching_members.append(member_data)
            except (ValueError, KeyError):
                # Skip invalid member data
                continue
        
        return matching_members
    
    @staticmethod
    def sort_members(members: List[Dict], sort_by: str = 'name', reverse: bool = False) -> List[Dict]:
        """
        Sort members by specified field.
        
        Args:
            members (List[Dict]): List of member dictionaries
            sort_by (str): Field to sort by ('name', 'id', 'email')
            reverse (bool): Whether to sort in reverse order
            
        Returns:
            List[Dict]: Sorted list of members
        """
        valid_sort_fields = ['name', 'id', 'email', 'phone']
        
        if sort_by not in valid_sort_fields:
            sort_by = 'name'
        
        try:
            if sort_by == 'id':
                return sorted(members, key=lambda m: m.get('id', 0), reverse=reverse)
            else:
                return sorted(members, key=lambda m: m.get(sort_by, '').lower(), reverse=reverse)
        except (KeyError, TypeError):
            # Return original list if sorting fails
            return members
    
    @staticmethod
    def get_member_by_id(members: List[Dict], member_id: int) -> Optional[Dict]:
        """
        Find a member by ID.
        
        Args:
            members (List[Dict]): List of member dictionaries
            member_id (int): Member ID to find
            
        Returns:
            Optional[Dict]: Member dictionary or None if not found
        """
        return next((m for m in members if m.get('id') == member_id), None)
    
    @staticmethod
    def get_member_by_name(members: List[Dict], name: str) -> Optional[Dict]:
        """
        Find a member by name (case-insensitive).
        
        Args:
            members (List[Dict]): List of member dictionaries
            name (str): Member name to find
            
        Returns:
            Optional[Dict]: Member dictionary or None if not found
        """
        name_lower = name.lower().strip()
        return next((m for m in members if m.get('name', '').lower().strip() == name_lower), None)
    
    @staticmethod
    def get_available_id(members: List[Dict]) -> int:
        """
        Get the next available member ID.
        
        Args:
            members (List[Dict]): List of member dictionaries
            
        Returns:
            int: Next available ID
        """
        if not members:
            return 1
        
        existing_ids = {m.get('id', 0) for m in members}
        next_id = 1
        
        while next_id in existing_ids:
            next_id += 1
        
        return next_id
    
    @staticmethod
    def format_member_list(members: List[Dict]) -> str:
        """
        Format a list of members for display.
        
        Args:
            members (List[Dict]): List of member dictionaries
            
        Returns:
            str: Formatted member list
        """
        if not members:
            return "No members"
        
        formatted_lines = []
        for member_data in members:
            try:
                member = Member.from_dict(member_data)
                formatted_lines.append(f"{member.id:2d}. {member.name}")
            except (ValueError, KeyError):
                formatted_lines.append(f"    Invalid member data: {member_data}")
        
        return "\n".join(formatted_lines)