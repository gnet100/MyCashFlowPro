# -*- coding: utf-8 -*-
"""
file_service.py
שירות לניהול קבצים - שמירה, זיהוי כפילויות, עיבוד
"""

import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import database
from parsers.file_parser import FileParser
from parsers.discount_parser import DiscountParser
from parsers.visa_cal_parser import VisaCALParser
from parsers.leumi_pdf_parser import LeumiPDFParser
from parsers.leumi_xlsx_parser import LeumiXLSXParser
from parsers.leumi_dat_parser import LeumiDATParser
from parsers.bankin_dat_parser import BankinDATParser


class FileService:
    """שירות לניהול קבצים"""
    
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv', '.tsv', '.pdf', '.dat'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    def __init__(self, upload_folder: str):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """בדיקה האם סוג הקובץ מותר"""
        return os.path.splitext(filename)[1].lower() in FileService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """חישוב hash של קובץ לזיהוי כפילויות"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check_duplicate(self, file_hash: str, extension: str = '') -> Optional[Dict]:
        """
        בדיקת קובץ כפול לפי hash בכל התזרימים
        Returns: מידע על הקובץ הכפול אם קיים, אחרת None
        """
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            # יצירת שם הקובץ המאוחסן (hash + extension)
            stored_filename = f"{file_hash}{extension}"
            
            # חיפוש לפי stored_filename בכל התזרימים
            cursor.execute('''
                SELECT 
                    f.id, f.original_filename, f.upload_date, 
                    f.processed, f.num_transactions, f.status,
                    flow.name as flow_name
                FROM files f
                LEFT JOIN flows flow ON f.flow_id = flow.id
                WHERE f.stored_filename = ?
            ''', (stored_filename,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'filename': row[1],
                    'upload_date': row[2],
                    'processed': bool(row[3]),
                    'num_transactions': row[4],
                    'status': row[5],
                    'flow_name': row[6]
                }
            return None
            
        except Exception as e:
            print(f"❌ שגיאה בבדיקת כפילות: {e}")
            return None
    
    def save_upload(
        self, 
        file: FileStorage, 
        flow_id: int, 
        account_id: Optional[int] = None
    ) -> Tuple[bool, Optional[int], Optional[str], Optional[Dict]]:
        """
        שמירת קובץ שהועלה
        Returns: (success, file_id, error_message, duplicate_info)
        """
        try:
            # בדיקה בסיסית
            if not file or file.filename == '':
                return False, None, "לא נבחר קובץ", None
            
            if not self.allowed_file(file.filename):
                return False, None, "סוג קובץ לא נתמך. יש להעלות קבצי Excel או CSV", None
            
            # שמירה זמנית
            original_filename = secure_filename(file.filename)
            temp_path = os.path.join(self.upload_folder, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_filename}")
            
            file.save(temp_path)
            
            # בדיקת גודל
            file_size = os.path.getsize(temp_path)
            if file_size > self.MAX_FILE_SIZE:
                os.remove(temp_path)
                return False, None, f"הקובץ גדול מדי ({file_size / 1024 / 1024:.1f}MB). מקסימום: 50MB", None
            
            # חישוב hash
            file_hash = self.calculate_file_hash(temp_path)
            
            # זיהוי סיומת הקובץ
            extension = os.path.splitext(original_filename)[1]
            
            # בדיקת כפילות בכל התזרימים
            duplicate = self.check_duplicate(file_hash, extension)
            if duplicate:
                os.remove(temp_path)
                return False, None, None, duplicate
            
            # שינוי שם לקובץ קבוע (hash)
            stored_filename = f"{file_hash}{extension}"
            final_path = os.path.join(self.upload_folder, stored_filename)
            
            os.rename(temp_path, final_path)
            
            # שמירה במסד נתונים - זיהוי סוג הקובץ לפי סיומת
            file_type = extension[1:].upper() if extension else 'UNKNOWN'
            
            conn = database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO files (
                    flow_id, account_id, original_filename, stored_filename,
                    file_path, file_type, source_name, file_size, encoding,
                    upload_date, processed, num_transactions, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                flow_id,
                account_id,
                original_filename,
                stored_filename,
                final_path,
                file_type,
                None,  # source_name - יזוהה בעיבוד
                file_size,
                None,  # encoding - יזוהה בעיבוד
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                0,  # לא מעובד עדיין
                0,  # 0 עסקאות
                'uploaded'
            ))
            
            file_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            print(f"✅ קובץ נשמר: ID={file_id}, שם={original_filename}")
            return True, file_id, None, None
            
        except Exception as e:
            print(f"💥 שגיאה ב-save_upload: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # ניקוי במקרה של שגיאה
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
            
            # תרגום הודעות שגיאה נפוצות
            error_msg = str(e)
            if "already exists" in error_msg.lower() or "winerror 183" in error_msg.lower():
                return False, None, "הקובץ כבר קיים במערכת", None
            
            if "html5lib" in error_msg.lower():
                return False, None, "בעיה בניתוח קובץ HTML. השתמש בקבצי Excel או CSV", None
            
            return False, None, f"שגיאה: {error_msg}", None
    
    def delete_file(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        מחיקת קובץ + CASCADE למחיקת כל העסקאות המקושרות
        Returns: (success, error_message)
        """
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            # קבלת נתיב הקובץ
            cursor.execute('SELECT file_path, num_transactions FROM files WHERE id = ?', (file_id,))
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return False, "הקובץ לא נמצא במסד הנתונים"
            
            file_path, num_transactions = row
            
            # מחיקת הרשומה מהמסד - CASCADE ידאג לעסקאות
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            conn.commit()
            conn.close()
            
            # מחיקת הקובץ הפיזי
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return True, None
            
        except Exception as e:
            return False, f"שגיאה במחיקת הקובץ: {str(e)}"
    
    def clean_orphaned_records(self) -> Tuple[int, int]:
        """
        ניקוי רשומות ישנות ללא קובץ פיזי
        Returns: (num_cleaned, num_transactions_deleted)
        """
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            # מציאת כל הרשומות
            cursor.execute('SELECT id, stored_filename, file_path FROM files')
            all_records = cursor.fetchall()
            
            orphaned_ids = []
            total_transactions = 0
            
            # בדיקה לכל רשומה אם הקובץ קיים פיזית
            for file_id, stored_filename, file_path in all_records:
                # בדיקה ראשונה - לפי file_path
                if file_path and os.path.exists(file_path):
                    continue
                
                # בדיקה שנייה - לפי stored_filename ב-upload_folder
                physical_path = os.path.join(self.upload_folder, stored_filename)
                if os.path.exists(physical_path):
                    continue
                
                # הקובץ לא קיים - מסמנים למחיקה
                orphaned_ids.append(file_id)
                
                # ספירת עסקאות שיימחקו
                cursor.execute('SELECT COUNT(*) FROM transactions WHERE file_id = ?', (file_id,))
                total_transactions += cursor.fetchone()[0]
            
            # מחיקת רשומות ללא קובץ
            if orphaned_ids:
                placeholders = ','.join('?' * len(orphaned_ids))
                cursor.execute(f'DELETE FROM files WHERE id IN ({placeholders})', orphaned_ids)
                conn.commit()
            
            conn.close()
            
            return len(orphaned_ids), total_transactions
            
        except Exception as e:
            print(f"❌ שגיאה בניקוי רשומות: {e}")
            return 0, 0
    
    def get_all_files(self, flow_id: Optional[int] = None) -> List[Dict]:
        """
        שליפת כל הקבצים (אופציונלי: לפי תזרים)
        """
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            if flow_id is not None:
                cursor.execute('''
                    SELECT 
                        f.id, f.original_filename, f.stored_filename, f.file_type, f.source_name,
                        f.file_size, f.upload_date, f.processed, f.num_transactions,
                        f.status, flow.name as flow_name
                    FROM files f
                    LEFT JOIN flows flow ON f.flow_id = flow.id
                    WHERE f.flow_id = ?
                    ORDER BY f.upload_date DESC
                ''', (flow_id,))
            else:
                cursor.execute('''
                    SELECT 
                        f.id, f.original_filename, f.stored_filename, f.file_type, f.source_name,
                        f.file_size, f.upload_date, f.processed, f.num_transactions,
                        f.status, flow.name as flow_name
                    FROM files f
                    LEFT JOIN flows flow ON f.flow_id = flow.id
                    ORDER BY f.upload_date DESC
                ''')
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    'id': row[0],
                    'original_filename': row[1],
                    'stored_filename': row[2],
                    'file_type': row[3],
                    'source_name': row[4],
                    'file_size': row[5],
                    'upload_date': row[6],
                    'processed': bool(row[7]),
                    'num_transactions': row[8],
                    'status': row[9],
                    'flow_name': row[10]
                })
            
            conn.close()
            return files
            
        except Exception as e:
            print(f"❌ שגיאה בשליפת קבצים: {e}")
            return []
    
    def get_file_details(self, file_id: int) -> Optional[Dict]:
        """קבלת פרטי קובץ"""
        try:
            conn = database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    f.*,
                    flow.name as flow_name,
                    acc.account_name
                FROM files f
                LEFT JOIN flows flow ON f.flow_id = flow.id
                LEFT JOIN accounts acc ON f.account_id = acc.id
                WHERE f.id = ?
            ''', (file_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                'id': row['id'],
                'flow_id': row['flow_id'],
                'account_id': row['account_id'],
                'original_filename': row['original_filename'],
                'stored_filename': row['stored_filename'],
                'file_path': row['file_path'],
                'file_type': row['file_type'],
                'source_name': row['source_name'],
                'file_size': row['file_size'],
                'encoding': row['encoding'],
                'upload_date': row['upload_date'],
                'processed': bool(row['processed']),
                'processed_date': row['processed_date'],
                'num_transactions': row['num_transactions'],
                'status': row['status'],
                'error_message': row['error_message'],
                'flow_name': row['flow_name'],
                'account_name': row['account_name']
            }
            
        except Exception as e:
            print(f"❌ שגיאה בשליפת פרטי קובץ: {e}")
            return None
    
    def process_file_to_transactions(self, file_id: int) -> Tuple[bool, Optional[str], int]:
        """
        עיבוד קובץ לעסקאות במסד הנתונים
        Returns: (success, error_message, num_transactions_created)
        """
        try:
            # 1. שליפת פרטי הקובץ
            conn = database.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, file_path, source_name, flow_id, account_id, processed, original_filename
                FROM files
                WHERE id = ?
            ''', (file_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return False, "הקובץ לא נמצא במסד הנתונים", 0
            
            file_id, file_path, source_name, flow_id, account_id, processed, original_filename = row
            
            # בדיקה: אם כבר עובד - אל תעבד שוב
            if processed:
                conn.close()
                return False, "הקובץ כבר עובד", 0
            
            # 2. זיהוי סוג הקובץ והפעלת Parser המתאים
            parser = None
            transactions = []
            parser_type = None  # לדיבאג
            
            # זיהוי חכם לפי שם מקורי, source_name, ובדיקת תוכן
            original_lower = original_filename.lower() if original_filename else ''
            source_lower = source_name.lower() if source_name else ''
            
            # בדיקה 1: דיסקונט
            if ('דיסקונט' in source_lower or 
                'discount' in source_lower or
                'transaction-details' in original_lower or
                'details_export' in original_lower):
                parser_type = 'discount'
                parser = DiscountParser(file_path)
                success, error = parser.parse()
                if not success:
                    conn.close()
                    return False, f"שגיאה בניתוח קובץ דיסקונט: {error}", 0
                transactions = parser.get_transactions()
                
            # בדיקה 2: ויזה כאל / לאומי
            elif ('ויזה' in original_lower or 
                  'visa' in original_lower or
                  'לאומי' in source_lower or
                  'leumi' in source_lower or
                  'פירוט_חיובים' in original_lower):
                parser_type = 'visa_cal'
                parser = VisaCALParser(file_path)
                success, error = parser.parse()
                if not success:
                    conn.close()
                    return False, f"שגיאה בניתוח קובץ ויזה: {error}", 0
                transactions = parser.get_transactions()
            
            # בדיקה 3: PDF לאומי - תנועות בחשבון
            elif file_path.lower().endswith('.pdf') and ('לאומי' in source_lower or 'תנועות' in original_lower):
                parser_type = 'leumi_pdf'
                parser = LeumiPDFParser(file_path)
                success, error = parser.parse()
                if not success:
                    conn.close()
                    return False, f"שגיאה בניתוח PDF לאומי: {error}", 0
                transactions = parser.get_transactions()
            
            # בדיקה 4: XLSX לאומי - תנועות בחשבון
            elif file_path.lower().endswith('.xlsx') and ('עו_ש' in original_lower or 'תנועות' in original_lower or 'לאומי' in original_lower):
                parser_type = 'leumi_xlsx'
                parser = LeumiXLSXParser(file_path)
                success, error = parser.parse()
                if not success:
                    conn.close()
                    return False, f"שגיאה בניתוח XLSX לאומי: {error}", 0
                transactions = parser.get_transactions()
            
            # בדיקה 5: DAT - Bankin או לאומי
            elif file_path.lower().endswith('.dat'):
                if 'bankin' in original_lower:
                    parser_type = 'bankin_dat'
                    parser = BankinDATParser(file_path)
                    success, error, trans_list = parser.parse()
                    if not success:
                        conn.close()
                        return False, f"שגיאה בניתוח Bankin DAT: {error}", 0
                    transactions = trans_list
                elif 'לאומי' in original_lower or 'leumi' in original_lower:
                    parser_type = 'leumi_dat'
                    parser = LeumiDATParser(file_path)
                    success, error, trans_list = parser.parse()
                    if not success:
                        conn.close()
                        return False, f"שגיאה בניתוח DAT לאומי: {error}", 0
                    transactions = trans_list
                else:
                    # ברירת מחדל - ננסה Bankin
                    parser_type = 'bankin_dat'
                    parser = BankinDATParser(file_path)
                    success, error, trans_list = parser.parse()
                    if not success:
                        conn.close()
                        return False, f"שגיאה בניתוח DAT: {error}", 0
                    transactions = trans_list
                
            # בדיקה 6: זיהוי אוטומטי לפי תוכן הקובץ (fallback)
            else:
                # ננסה לזהות לפי העמודות בקובץ - נסה את כל ה-parsers
                try:
                    # רק עבור קבצי Excel
                    if file_path.lower().endswith(('.xlsx', '.xls')):
                        import pandas as pd
                        
                        # רשימת parsers לנסות
                        parsers_to_try = [
                            ('ויזה כאל', VisaCALParser),
                            ('דיסקונט', DiscountParser),
                            ('לאומי XLSX', LeumiXLSXParser)
                        ]
                        
                        success = False
                        last_error = None
                        
                        for parser_name, ParserClass in parsers_to_try:
                            try:
                                parser = ParserClass(file_path)
                                parse_success, parse_error = parser.parse()
                                if parse_success:
                                    transactions = parser.get_transactions()
                                    if transactions and len(transactions) > 0:
                                        parser_type = f'{parser_name} (זיהוי אוטומטי)'
                                        success = True
                                        break
                                    else:
                                        last_error = f"{parser_name}: לא נמצאו עסקאות"
                                else:
                                    last_error = f"{parser_name}: {parse_error}"
                            except Exception as e:
                                last_error = f"{parser_name}: {str(e)}"
                                continue
                        
                        if not success:
                            conn.close()
                            error_msg = "לא הצלחנו לזהות את פורמט הקובץ.\n\n"
                            error_msg += "נסינו: דיסקונט, ויזה כאל, לאומי\n"
                            error_msg += f"קובץ: {original_filename}\n"
                            if last_error:
                                error_msg += f"\nשגיאה אחרונה: {last_error}"
                            return False, error_msg, 0
                    
                    # עבור קבצי DAT
                    elif file_path.lower().endswith('.dat'):
                        # נסה Bankin קודם
                        parser = BankinDATParser(file_path)
                        success, error, trans_list = parser.parse()
                        if success and trans_list:
                            transactions = trans_list
                            parser_type = 'Bankin DAT (אוטומטי)'
                        else:
                            # נסה לאומי DAT
                            parser = LeumiDATParser(file_path)
                            success, error, trans_list = parser.parse()
                            if success and trans_list:
                                transactions = trans_list
                                parser_type = 'לאומי DAT (אוטומטי)'
                            else:
                                conn.close()
                                return False, f"שגיאה בניתוח קובץ DAT: {error}", 0
                    
                    # עבור קבצי PDF - נסה לאומי PDF
                    elif file_path.lower().endswith('.pdf'):
                        parser_type = 'leumi_pdf (אוטומטי)'
                        parser = LeumiPDFParser(file_path)
                        success, error = parser.parse()
                        if not success:
                            conn.close()
                            return False, f"שגיאה בניתוח PDF: {error}", 0
                        transactions = parser.get_transactions()
                        if not transactions:
                            conn.close()
                            return False, "PDF לא מכיל עסקאות או בפורמט לא נתמך", 0
                    
                    else:
                        conn.close()
                        return False, f"סוג קובץ לא נתמך: {os.path.splitext(file_path)[1]}", 0
                        
                except Exception as e:
                    conn.close()
                    error_msg = f"שגיאה בניתוח הקובץ.\n"
                    error_msg += f"קובץ: {original_filename}\n"
                    error_msg += f"שגיאה: {str(e)}"
                    import traceback
                    error_msg += f"\n\n{traceback.format_exc()}"
                    return False, error_msg, 0
            
            if not transactions:
                conn.close()
                return False, "לא נמצאו עסקאות בקובץ", 0
            
            # 3. הכנסת עסקאות למסד הנתונים
            num_created = 0
            for trans in transactions:
                try:
                    # הסכום מגיע עם הסימן הנכון מה-parser
                    # (שלילי = הוצאה, חיובי = הכנסה)
                    amount = trans['amount']
                    
                    cursor.execute('''
                        INSERT INTO transactions (
                            flow_id, category_id, account_id, file_id,
                            transaction_date, description, amount, 
                            transaction_type, source_type, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        flow_id,
                        0,  # לא מקוטלג עדיין
                        account_id,
                        file_id,
                        trans['date'],
                        trans['description'],
                        amount,
                        'expense' if amount < 0 else 'income',  # סוג העסקה לפי סימן
                        trans.get('source', 'file_import'),  # מקור
                        trans.get('notes')
                    ))
                    num_created += 1
                    
                except Exception as e:
                    print(f"⚠️  שגיאה בהוספת עסקה: {e}")
                    continue
            
            # 4. עדכון סטטוס הקובץ
            cursor.execute('''
                UPDATE files
                SET processed = 1,
                    processed_date = ?,
                    num_transactions = ?,
                    status = 'processed'
                WHERE id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), num_created, file_id))
            
            conn.commit()
            conn.close()
            
            return True, None, num_created
            
        except Exception as e:
            return False, f"שגיאה כללית בעיבוד: {str(e)}", 0
