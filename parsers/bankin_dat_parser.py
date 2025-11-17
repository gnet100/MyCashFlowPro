# -*- coding: utf-8 -*-
"""
bankin_dat_parser.py
מנתח קבצי DAT של מערכת Bankin (פורמט DOS cp862)
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class BankinDATParser:
    """מחלקה לניתוח קבצי DAT של Bankin"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions: List[Dict] = []
        self.account_number: Optional[str] = None
        self.metadata: Dict = {}
        self.encoding = 'cp862'  # DOS Hebrew encoding
        
    def parse(self) -> Tuple[bool, Optional[str], List[Dict]]:
        """
        ניתוח קובץ DAT
        Returns: (success, error_message, transactions_list)
        """
        try:
            with open(self.file_path, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            if not lines:
                return False, "הקובץ ריק", []
            
            # עיבוד כל שורה
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:
                    continue
                
                # ניתוח שורה
                transaction = self._parse_line(line, line_num)
                if transaction:
                    self.transactions.append(transaction)
            
            # שמירת מטא-דאטה
            if self.transactions:
                self.account_number = self.transactions[0].get('account_number')
                self.metadata = {
                    'total_transactions': len(self.transactions),
                    'account_number': self.account_number,
                    'date_range': self._get_date_range(),
                    'encoding': self.encoding
                }
            
            return True, None, self.transactions
            
        except UnicodeDecodeError as e:
            return False, f"שגיאת קידוד: {str(e)}", []
        except Exception as e:
            return False, f"שגיאה בעיבוד הקובץ: {str(e)}", []
    
    def _parse_line(self, line: str, line_num: int) -> Optional[Dict]:
        """
        ניתוח שורה בודדת מהקובץ
        
        פורמט: מספר_רשומה,תאריך,תיאור,סכום,יתרה,קוד,מספר_חשבון
        דוגמה: 0131598,170925,"   טנרטניא .עה",-000000800.00,+000013131.69,0005,94233029016626
        """
        try:
            # פיצול לפי פסיק (comma) אבל לא בתוך מרכאות
            parts = self._split_csv_line(line)
            
            if len(parts) < 7:
                print(f"⚠️ שורה {line_num}: מספר שדות לא תקין ({len(parts)} במקום 7)")
                return None
            
            # חילוץ שדות
            record_number = parts[0].strip()
            date_str = parts[1].strip()
            description = parts[2].strip().strip('"')
            amount_str = parts[3].strip()
            balance_str = parts[4].strip()
            code = parts[5].strip()
            account_number = parts[6].strip()
            
            # המרת תאריך (DDMMYY -> datetime)
            transaction_date = self._parse_date(date_str)
            if not transaction_date:
                print(f"⚠️ שורה {line_num}: תאריך לא תקין: {date_str}")
                return None
            
            # המרת סכום
            amount = self._parse_amount(amount_str)
            if amount is None:
                print(f"⚠️ שורה {line_num}: סכום לא תקין: {amount_str}")
                return None
            
            # המרת יתרה
            balance = self._parse_amount(balance_str)
            
            # תיקון טקסט עברי הפוך
            description_fixed = self._reverse_hebrew(description)
            
            # בניית אובייקט עסקה
            transaction = {
                'record_number': record_number,
                'date': transaction_date.strftime('%Y-%m-%d'),  # פורמט מחרוזת ל-DB
                'transaction_date': transaction_date,  # גם שמירה כ-datetime לצורכי ניתוח
                'description': description_fixed,
                'original_description': description,  # שמירה גם של המקור
                'amount': amount,
                'balance': balance,
                'code': code,
                'account_number': account_number,
                'line_number': line_num,
                'source': 'bankin_dat'  # הגדרת מקור
            }
            
            return transaction
            
        except Exception as e:
            print(f"⚠️ שורה {line_num}: שגיאה בעיבוד - {str(e)}")
            return None
    
    def _split_csv_line(self, line: str) -> List[str]:
        """פיצול שורה CSV כשיש מרכאות"""
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
        """
        המרת תאריך מפורמט DDMMYY
        דוגמה: 170925 -> 17/09/2025
        """
        try:
            if len(date_str) != 6:
                return None
            
            day = int(date_str[0:2])
            month = int(date_str[2:4])
            year = int(date_str[4:6])
            
            # המרת שנה דו-ספרתית לארבע ספרות
            # נניח שנים 00-49 הן 2000-2049, ו-50-99 הן 1950-1999
            if year < 50:
                year += 2000
            else:
                year += 1900
            
            return datetime(year, month, day)
            
        except (ValueError, IndexError):
            return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """
        המרת סכום מפורמט +/-000000123.45
        """
        try:
            # הסרת רווחים
            amount_str = amount_str.strip()
            
            # המרה למספר
            amount = float(amount_str)
            
            return amount
            
        except ValueError:
            return None
    
    def _reverse_hebrew(self, text: str) -> str:
        """
        תיקון טקסט עברי שמופיע הפוך בגלל cp862
        
        בקובץ: "טנרטניא .עה"
        אחרי תיקון: "הע. אינטרנט"
        """
        # הטקסט מגיע הפוך, אז פשוט נהפוך אותו חזרה
        # אבל נשמור רווחים בתחילה/סוף
        text = text.strip()
        
        # הפיכת הטקסט
        reversed_text = text[::-1]
        
        return reversed_text.strip()
    
    def _get_date_range(self) -> Dict[str, datetime]:
        """חישוב טווח תאריכים של העסקאות"""
        if not self.transactions:
            return {}
        
        dates = [t['transaction_date'] for t in self.transactions 
                 if t.get('transaction_date')]
        
        if not dates:
            return {}
        
        return {
            'from': min(dates),
            'to': max(dates)
        }
    
    def get_summary(self) -> Dict:
        """סיכום של העסקאות שנותחו"""
        if not self.transactions:
            return {'error': 'אין עסקאות'}
        
        total_debit = sum(t['amount'] for t in self.transactions if t['amount'] < 0)
        total_credit = sum(t['amount'] for t in self.transactions if t['amount'] > 0)
        
        return {
            'total_transactions': len(self.transactions),
            'account_number': self.account_number,
            'date_range': self.metadata.get('date_range', {}),
            'total_debit': total_debit,
            'total_credit': total_credit,
            'net_change': total_credit + total_debit
        }
    
    def get_transactions(self) -> List[Dict]:
        """החזרת רשימת כל העסקאות"""
        return self.transactions


# ====================
# דוגמת שימוש
# ====================
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("שימוש: python bankin_dat_parser.py <קובץ.dat>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print(f"📂 מעבד קובץ: {file_path}\n")
    
    # יצירת Parser
    parser = BankinDATParser(file_path)
    
    # ניתוח הקובץ
    success, error, transactions = parser.parse()
    
    if not success:
        print(f"❌ שגיאה: {error}")
        sys.exit(1)
    
    # הצגת סיכום
    summary = parser.get_summary()
    print("="*80)
    print("📊 סיכום")
    print("="*80)
    print(f"חשבון: {summary['account_number']}")
    print(f"סה\"כ עסקאות: {summary['total_transactions']}")
    
    if summary.get('date_range'):
        dr = summary['date_range']
        print(f"תקופה: {dr['from'].strftime('%d/%m/%Y')} - {dr['to'].strftime('%d/%m/%Y')}")
    
    print(f"זכות: ₪{summary['total_credit']:,.2f}")
    print(f"חובה: ₪{summary['total_debit']:,.2f}")
    print(f"שינוי נטו: ₪{summary['net_change']:,.2f}")
    
    # הצגת 5 עסקאות ראשונות
    print("\n" + "="*80)
    print("🔍 5 עסקאות ראשונות")
    print("="*80)
    
    for i, trans in enumerate(transactions[:5], 1):
        date_str = trans['transaction_date'].strftime('%d/%m/%Y')
        amount = trans['amount']
        desc = trans['description']
        balance = trans['balance']
        
        sign = "+" if amount >= 0 else ""
        print(f"{i}. {date_str} | {sign}₪{amount:,.2f} | {desc} | יתרה: ₪{balance:,.2f}")
    
    print(f"\n... ועוד {len(transactions) - 5} עסקאות")
