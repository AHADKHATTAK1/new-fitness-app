"""
Advanced Excel Import Validator
Validates imported data before committing to database
"""

import re
from datetime import datetime, date
from typing import Dict, List, Any


class ImportValidator:
    """Validates Excel import data with detailed error reporting"""
    
    def __init__(self, gym_manager):
        self.gym = gym_manager
        
    def validate_import_data(self, rows_data: List[Dict], existing_phones: set = None) -> Dict[str, Any]:
        """
        Validate all rows from Excel import
        
        Returns:
            {
                'total': int,
                'valid': int,
                'warnings': int,
                'errors': int,
                'rows': [
                    {
                        'row_num': int,
                        'data': dict,
                        'status': 'valid'|'warning'|'error',
                        'messages': [str],
                        'existing_member': dict or None
                    }
                ]
            }
        """
        if existing_phones is None:
            existing_phones = self._get_existing_phones()
            
        results = {
            'total': 0,
            'valid': 0,
            'warnings': 0,
            'errors': 0,
            'rows': []
        }
        
        for index, row in enumerate(rows_data):
            row_result = self._validate_row(row, index + 2, existing_phones)  # +2 for Excel row (1-indexed + header)
            results['rows'].append(row_result)
            results['total'] += 1
            
            if row_result['status'] == 'valid':
                results['valid'] += 1
            elif row_result['status'] == 'warning':
                results['warnings'] += 1
            elif row_result['status'] == 'error':
                results['errors'] += 1
        
        return results
    
    def _validate_row(self, row: Dict, row_num: int, existing_phones: set) -> Dict[str, Any]:
        """Validate a single row"""
        row_result = {
            'row_num': row_num,
            'data': {},
            'status': 'valid',
            'messages': [],
            'existing_member': None
        }
        
        # Extract and clean data
        name = str(row.get('Name') or row.get('name') or '').strip()
        phone = str(row.get('Phone') or row.get('phone') or row.get('Mobile') or '').strip()
        email = str(row.get('Email') or row.get('email') or '').strip()
        joined_date = row.get('Joined Date') or row.get('Join Date') or row.get('joined_date')
        status = str(row.get('Status') or row.get('Paid') or '').strip().lower()
        membership_type = str(row.get('Membership Type') or row.get('Type') or '').strip()
        
        # Validate Name (Required)
        if not name or len(name) < 2:
            row_result['status'] = 'error'
            row_result['messages'].append('Name is required (minimum 2 characters)')
        elif len(name) > 100:
            row_result['status'] = 'warning'
            row_result['messages'].append('Name is very long (max 100 chars recommended)')
        
        # Validate Phone (Required, Unique)
        if not phone:
            row_result['status'] = 'error'
            row_result['messages'].append('Phone number is required')
        else:
            # Clean phone number
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            if len(cleaned_phone) < 10 or len(cleaned_phone) > 15:
                row_result['status'] = 'warning'
                row_result['messages'].append(f'Phone format unusual ({len(cleaned_phone)} digits)')
            
            # Check for duplicates
            if cleaned_phone in existing_phones:
                from models import Member
                existing = self.gym.session.query(Member).filter_by(
                    gym_id=self.gym.gym.id,
                    phone=cleaned_phone
                ).first()
                
                if existing:
                    if row_result['status'] != 'error':  # Don't downgrade errors
                        row_result['status'] = 'warning'
                    row_result['messages'].append(f'Duplicate phone - Member exists: {existing.name}')
                    row_result['existing_member'] = {
                        'id': existing.id,
                        'name': existing.name,
                        'email': existing.email,
                        'joined_date': str(existing.joined_date)
                    }
            
            phone = cleaned_phone  # Use cleaned version
        
        # Validate Email (Optional, but must be valid if provided)
        if email:
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                if row_result['status'] == 'valid':
                    row_result['status'] = 'warning'
                row_result['messages'].append('Email format appears invalid')
        
        # Validate Joined Date
        if joined_date:
            try:
                if isinstance(joined_date, str):
                    joined_date = datetime.strptime(joined_date, '%Y-%m-%d').date()
                elif not isinstance(joined_date, date):
                    joined_date = datetime.now().date()
                    
                # Check if date is in the future
                if joined_date > datetime.now().date():
                    if row_result['status'] == 'valid':
                        row_result['status'] = 'warning'
                    row_result['messages'].append('Join date is in the future')
            except (ValueError, TypeError):
                if row_result['status'] == 'valid':
                    row_result['status'] = 'warning'
                row_result['messages'].append('Invalid date format, using today\'s date')
                joined_date = datetime.now().date()
        else:
            joined_date = datetime.now().date()
        
        # Validate Payment Status
        if status and status not in ['paid', 'unpaid', '']:
            if row_result['status'] == 'valid':
                row_result['status'] = 'warning'
            row_result['messages'].append(f'Status "{status}" unclear (use "Paid" or "Unpaid")')
        
        # Store validated data
        row_result['data'] = {
            'name': name,
            'phone': phone,
            'email': email,
            'joined_date': joined_date,
            'status': status,
            'membership_type': membership_type or 'Gym'
        }
        
        return row_result
    
    def _get_existing_phones(self) -> set:
        """Get all existing phone numbers for this gym"""
        from models import Member
        existing = self.gym.session.query(Member.phone).filter_by(
            gym_id=self.gym.gym.id
        ).all()
        return {phone[0] for phone in existing if phone[0]}
    
    def handle_duplicates(self, validated_rows: List[Dict], strategy: str = 'skip') -> List[Dict]:
        """
        Apply duplicate handling strategy to validated rows
        
        Strategies:
            - 'skip': Keep existing member, don't import
            - 'update': Replace all fields with new data
            - 'merge': Update only non-empty new fields + add payments
        """
        for row in validated_rows:
            if row.get('existing_member'):
                row['duplicate_action'] = strategy
                
                if strategy == 'skip':
                    row['will_import'] = False
                    row['action_description'] = 'Will skip (keep existing member)'
                    
                elif strategy == 'update':
                    row['will_import'] = True
                    row['action_description'] = 'Will update all fields'
                    
                elif strategy == 'merge':
                    row['will_import'] = True
                    row['action_description'] = 'Will merge non-empty fields + add payments'
            else:
                row['will_import'] = row['status'] != 'error'
                row['action_description'] = 'New member' if row['will_import'] else 'Error - will not import'
        
        return validated_rows
    
    def get_import_summary(self, validated_rows: List[Dict]) -> Dict[str, int]:
        """Get summary counts for import"""
        summary = {
            'total': len(validated_rows),
            'will_import': 0,
            'will_skip': 0,
            'new_members': 0,
            'updates': 0,
            'merges': 0,
            'errors': 0
        }
        
        for row in validated_rows:
            if row['status'] == 'error':
                summary['errors'] += 1
            elif row.get('will_import'):
                summary['will_import'] += 1
                if row.get('existing_member'):
                    if row.get('duplicate_action') == 'update':
                        summary['updates'] += 1
                    elif row.get('duplicate_action') == 'merge':
                        summary['merges'] += 1
                else:
                    summary['new_members'] += 1
            else:
                summary['will_skip'] += 1
        
        return summary
