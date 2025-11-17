# -*- coding: utf-8 -*-
"""
leumi_dat_parser.py
מנתח קבצי DAT של בנק לאומי
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class LeumiDATParser:
    """מחלקה לניתוח קבצי DAT של בנק לאומי"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions: List[Dict] = []
        self.encoding = 'cp862'  # DOS Hebrew encoding
        
    def validate_bank_file_structure(self) -> Tuple[bool, str, str]:
        """
        בדיקת תקינות הקובץ
        Returns: (is_valid, bank_name, account_type)
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                first_line = f.readline().strip()
            
            # בדיקה בסיסית של מבנה
            if first_line and ',' in first_line:
                return True, "בנק לאומי", "DAT"
            
            return False, "", ""
            
        except Exception:
            return False, "", ""
    
    def parse(self) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        ניתוח קובץ DAT
        Returns: (success, error_message, transactions_list)
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                transaction = self._parse_line(line, line_num)
                if transaction:
                    self.transactions.append(transaction)
            
            return True, None, self.transactions
            
        except Exception as e:
            return False, f"שגיאה: {str(e)}", []
    
    def _parse_line(self, line: str, line_num: int) -> Optional[Dict]:
        """ניתוח שורה בודדת"""
        try:
            parts = self._split_csv_line(line)
            
            if len(parts) < 7:
                return None
            
            # חילוץ שדות
            date_str = parts[1].strip()
            description = parts[2].strip().strip('"')
            amount_str = parts[3].strip()
            
            # המרת תאריך
            transaction_date = self._parse_date(date_str)
            if not transaction_date:
                return None
            
            # המרת סכום
            amount = float(amount_str)
            
            # תיקון עברית
            description = description[::-1].strip()
            
            return {
                'date': transaction_date,
                'description': description,
                'amount': amount
            }
            
        except Exception:
            return None
    
    def _split_csv_line(self, line: str) -> List[str]:
        """פיצול שורה CSV"""
        parts = []
        current = []
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current))
                current = []
            else:
                current.append(char)
        
        if current:
            parts.append(''.join(current))
        
        return parts
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """המרת תאריך DDMMYY"""
        try:
            if len(date_str) != 6:
                return None
            
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:6])
            
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            return datetime(year, month, day)
            
        except (ValueError, IndexError):
            return None
