#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
clean_orphaned_files.py
סקריפט לניקוי רשומות ישנות ב-DB ללא קובץ פיזי
"""

import os
import sys
from services.file_service import FileService

def main():
    """ניקוי רשומות ישנות"""
    print("=" * 60)
    print("🧹 ניקוי רשומות ישנות - Clean Orphaned Records")
    print("=" * 60)
    print()
    
    # יצירת FileService
    upload_folder = os.path.join(os.path.dirname(__file__), 'data', 'files')
    file_service = FileService(upload_folder)
    
    print("🔍 מחפש רשומות ללא קובץ פיזי...")
    print()
    
    # ניקוי
    num_cleaned, num_transactions = file_service.clean_orphaned_records()
    
    print()
    print("=" * 60)
    print("📊 תוצאות:")
    print("=" * 60)
    
    if num_cleaned > 0:
        print(f"✅ נוקו {num_cleaned} רשומות ישנות")
        print(f"🗑️  נמחקו {num_transactions} עסקאות מקושרות")
        print()
        print("⚠️  שים לב: העסקאות נמחקו לצמיתות!")
    else:
        print("✨ לא נמצאו רשומות ישנות - הכל נקי!")
    
    print()
    print("=" * 60)
    print("✅ הסתיים בהצלחה!")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ הופסק על ידי המשתמש")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 שגיאה: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
