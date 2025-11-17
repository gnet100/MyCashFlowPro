# -*- coding: utf-8 -*-
"""
leumi_pdf_parser.py
מנתח קבצי PDF של בנק לאומי - תנועות בחשבון
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# ייבוא ספריות PDF בסדר עדיפות
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except:
    HAS_PYPDF2 = False


class LeumiPDFParser:
    """Parser לקבצי PDF של לאומי - עם תמיכה ב-PDF פגומים"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions = []
    
    def parse(self) -> Tuple[bool, Optional[str]]:
        """ניתוח קובץ PDF של לאומי - ניסיון עם מספר כלים"""
        
        # ניסיון 1: pdfplumber (הכי חזק)
        if HAS_PDFPLUMBER:
            success, error = self._parse_with_pdfplumber()
            if success:
                return True, None
        
        # ניסיון 2: PyPDF2
        if HAS_PYPDF2:
            success, error = self._parse_with_pypdf2()
            if success:
                return True, None
        
        # אם הכל נכשל
        if not HAS_PDFPLUMBER and not HAS_PYPDF2:
            return False, "לא מותקן כלי קריאת PDF. הרץ: pip install pdfplumber PyPDF2"
        
        return False, "לא הצלחנו לקרוא את ה-PDF. הקובץ עלול להיות פגום.\n\nפתרונות:\n1. הורד מחדש את הקובץ מהבנק\n2. המר את הקובץ ל-Excel\n3. צור קשר עם תמיכת הבנק"
    
    def _parse_with_pdfplumber(self) -> Tuple[bool, Optional[str]]:
        """ניתוח עם pdfplumber"""
        try:
            import pdfplumber
            
            with pdfplumber.open(self.file_path) as pdf:
                for page in pdf.pages:
                    # ניסיון 1: חילוץ טבלה
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            self._extract_from_table(table)
                    
                    # ניסיון 2: חילוץ טקסט
                    if not self.transactions:
                        text = page.extract_text()
                        if text:
                            self._extract_from_text(text)
            
            if self.transactions:
                return True, None
            return False, "לא נמצאו עסקאות ב-PDF"
            
        except Exception as e:
            return False, str(e)
    
    def _parse_with_pypdf2(self) -> Tuple[bool, Optional[str]]:
        """ניתוח עם PyPDF2"""
        try:
            import PyPDF2
            
            with open(self.file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            if text:
                self._extract_from_text(text)
            
            if self.transactions:
                return True, None
            return False, "לא נמצאו עסקאות ב-PDF"
            
        except Exception as e:
            return False, str(e)
    
    def _extract_from_table(self, table: List[List[str]]):
        """חילוץ עסקאות מטבלה"""
        try:
            for row in table:
                if not row or len(row) < 4:
                    continue
                
                # תאריך בעמודה הראשונה
                date_str = str(row[0]).strip() if row[0] else None
                if not date_str or not re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                    continue
                
                # המרת תאריך
                parts = date_str.split('/')
                trans_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                
                # תיאור
                description = str(row[1]).strip() if len(row) > 1 and row[1] else 'תנועה'
                
                # סכומים
                debit = 0.0
                credit = 0.0
                
                for cell in row[2:]:
                    if cell and str(cell).strip():
                        try:
                            amount_str = str(cell).replace(',', '').strip()
                            amount = float(amount_str)
                            if amount < 0:
                                debit = abs(amount)
                            else:
                                credit = amount
                        except:
                            continue
                
                # חישוב סכום סופי
                amount = credit - debit
                
                if amount != 0 and description:
                    self.transactions.append({
                        'date': trans_date,
                        'description': description,
                        'amount': amount,
                        'source': 'leumi_pdf'
                    })
        
        except Exception as e:
            pass
    
    def _extract_from_text(self, text: str):
        """חילוץ עסקאות מטקסט"""
        try:
            lines = text.split('\n')
            
            for line in lines:
                # חיפוש תבנית תאריך
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)
                if not date_match:
                    continue
                
                date_str = date_match.group(1)
                parts = date_str.split('/')
                trans_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                
                # חיפוש סכומים (מספרים עם/בלי פסיקים)
                amounts = re.findall(r'[\d,]+\.?\d*', line.replace(date_str, ''))
                if len(amounts) < 2:
                    continue
                
                # תיאור - הטקסט בין התאריך לסכומים
                desc_part = line.split(date_str)[1] if date_str in line else ''
                desc = re.sub(r'[\d,]+\.?\d*', '', desc_part).strip()
                
                if not desc:
                    continue
                
                # סכום
                try:
                    debit_str = amounts[0].replace(',', '')
                    credit_str = amounts[1].replace(',', '') if len(amounts) > 1 else '0'
                    
                    debit = float(debit_str) if debit_str else 0
                    credit = float(credit_str) if credit_str else 0
                    
                    amount = credit - debit
                    
                    if amount == 0:
                        continue
                    
                    self.transactions.append({
                        'date': trans_date,
                        'description': desc,
                        'amount': amount,
                        'source': 'leumi_pdf'
                    })
                    
                except:
                    continue
                    
        except Exception as e:
            pass
    
    def get_transactions(self) -> List[Dict]:
        return self.transactions
