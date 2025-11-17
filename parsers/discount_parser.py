# -*- coding: utf-8 -*-
"""
discount_parser.py
מנתח קבצי דיסקונט - פורמט Excel export
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class DiscountParser:
    """Parser לקבצי דיסקונט"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions = []
    
    def parse(self) -> Tuple[bool, Optional[str]]:
        """ניתוח קובץ דיסקונט"""
        try:
            # קריאת הקובץ ללא headers
            df = pd.read_excel(self.file_path, header=None)
            
            # חיפוש שורת הכותרת
            header_row = None
            for i in range(min(10, len(df))):
                row_text = str(df.iloc[i, 0]).lower()
                if 'תאריך עסקה' in row_text:
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
                    # תאריך
                    date_val = row.iloc[0]  # עמודה 0
                    if pd.isna(date_val):
                        continue
                    
                    # המרת תאריך
                    if isinstance(date_val, str):
                        parts = date_val.split('-')
                        if len(parts) == 3:
                            trans_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                        else:
                            continue
                    elif isinstance(date_val, datetime):
                        trans_date = date_val.strftime('%Y-%m-%d')
                    else:
                        continue
                    
                    # תיאור - עמודה 1
                    desc = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else ''
                    
                    # קטגוריה - עמודה 2
                    category = str(row.iloc[2]) if not pd.isna(row.iloc[2]) else ''
                    
                    # סכום - עמודה 5
                    amount_val = row.iloc[5]
                    if pd.isna(amount_val):
                        continue
                    
                    amount = -float(amount_val)  # הוצאה
                    
                    # הערות - עמודה 10
                    notes = str(row.iloc[10]) if len(row) > 10 and not pd.isna(row.iloc[10]) else ''
                    
                    self.transactions.append({
                        'date': trans_date,
                        'description': desc,
                        'amount': amount,
                        'category': category,
                        'notes': notes,
                        'source': 'discount'
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
