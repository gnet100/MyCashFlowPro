# -*- coding: utf-8 -*-
"""
leumi_xlsx_parser.py
מנתח קבצי לאומי XLSX - תנועות בחשבון
"""

import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class LeumiXLSXParser:
    """Parser לקבצי לאומי XLSX"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.transactions = []
    
    def parse(self) -> Tuple[bool, Optional[str]]:
        """ניתוח קובץ לאומי XLSX"""
        try:
            # קריאת הקובץ ללא headers
            df = pd.read_excel(self.file_path, header=None)
            
            # חיפוש שורת הכותרת (תאריך, תיאור, בחובה, בזכות)
            header_row = None
            for i in range(min(15, len(df))):
                if len(df.iloc[i]) > 3:
                    row_text = str(df.iloc[i, 0]).lower()
                    if 'תאריך' in row_text:
                        # בדיקה שיש גם עמודות חובה/זכות
                        row_2 = str(df.iloc[i, 2]).lower() if not pd.isna(df.iloc[i, 2]) else ''
                        row_3 = str(df.iloc[i, 3]).lower() if not pd.isna(df.iloc[i, 3]) else ''
                        if 'חובה' in row_2 or 'זכות' in row_3:
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
                    
                    # בחובה - עמודה 2, בזכות - עמודה 3
                    debit = row.iloc[2] if len(row) > 2 and not pd.isna(row.iloc[2]) else 0
                    credit = row.iloc[3] if len(row) > 3 and not pd.isna(row.iloc[3]) else 0
                    
                    # המרה למספרים
                    try:
                        debit = float(debit)
                    except:
                        debit = 0
                    
                    try:
                        credit = float(credit)
                    except:
                        credit = 0
                    
                    # חישוב סכום (זכות חיובי, חובה שלילי)
                    amount = credit - debit
                    
                    if amount == 0:
                        continue
                    
                    self.transactions.append({
                        'date': trans_date,
                        'description': desc,
                        'amount': amount,
                        'source': 'leumi_xlsx'
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
