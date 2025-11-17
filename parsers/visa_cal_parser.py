# -*- coding: utf-8 -*-
"""
visa_cal_parser.py
מנתח קבצי ויזה כאל (לאומי) - פורמט Excel
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class VisaCALParser:
    """Parser לקבצי ויזה כאל"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions = []
    
    def parse(self) -> Tuple[bool, Optional[str]]:
        """ניתוח קובץ ויזה כאל"""
        try:
            # קריאת הקובץ ללא headers
            df = pd.read_excel(self.file_path, header=None)
            
            # חיפוש שורת הכותרת
            header_row = None
            for i in range(min(10, len(df))):
                if len(df.iloc[i]) > 0:
                    row_text = str(df.iloc[i, 0]).lower()
                    if 'תאריך' in row_text and 'עסקה' in row_text:
                        header_row = i
                        break
            
            if header_row is None:
                return False, "לא נמצאה שורת כותרת"
            
            # קביעת headers
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            
            # עיבוד עסקאות
            self.transactions = []
            for idx, row in df.iterrows():
                try:
                    # תאריך - עמודה 0
                    date_val = row.iloc[0]
                    if pd.isna(date_val):
                        continue
                    
                    if isinstance(date_val, datetime):
                        trans_date = date_val.strftime('%Y-%m-%d')
                    else:
                        continue
                    
                    # תיאור - עמודה 1
                    desc = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ''
                    if not desc or desc == 'nan':
                        continue
                    
                    # סכום חיוב - עמודה 3
                    amount_val = row.iloc[3]
                    if pd.isna(amount_val):
                        continue
                    
                    amount = -float(amount_val)  # הוצאה
                    
                    # ענף - עמודה 5
                    category = str(row.iloc[5]) if len(row) > 5 and not pd.isna(row.iloc[5]) else ''
                    
                    self.transactions.append({
                        'date': trans_date,
                        'description': desc,
                        'amount': amount,
                        'category': category,
                        'source': 'visa_cal'
                    })
                    
                except Exception as e:
                    continue
            
            if not self.transactions:
                return False, "לא נמצאו עסקאות"
            
            return True, None
            
        except Exception as e:
            return False, f"שגיאה: {str(e)}"
    
    def get_transactions(self) -> List[Dict]:
        return self.transactions
