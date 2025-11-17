#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
start.py
קובץ הפעלה מהיר למערכת ניהול כספים
מפעיל את השרת ופותח את הדפדפן אוטומטית
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path

def clear_screen():
    """ניקוי מסך"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """הדפסת באנר פתיחה"""
    print("\n" + "="*60)
    print("🚀 מערכת ניהול כספים - הפעלה מהירה")
    print("="*60 + "\n")

def check_requirements():
    """בדיקת דרישות מקדימות"""
    print("🔍 בודק דרישות מקדימות...\n")
    
    # בדיקת Python
    python_version = sys.version_info
    print(f"  ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # בדיקת Flask
    try:
        import flask
        try:
            # ניסיון להשתמש ב-importlib.metadata (Python 3.8+)
            from importlib.metadata import version
            flask_version = version('flask')
        except:
            # fallback לגרסה ישנה
            flask_version = flask.__version__
        print(f"  ✅ Flask {flask_version}")
    except ImportError:
        print("  ❌ Flask לא מותקן!")
        print("\n💡 התקן עם: pip install -r requirements.txt")
        return False
    
    # בדיקת database.py
    if not Path('database.py').exists():
        print("  ❌ database.py לא נמצא!")
        return False
    print("  ✅ database.py")
    
    # בדיקת app.py
    if not Path('app.py').exists():
        print("  ❌ app.py לא נמצא!")
        return False
    print("  ✅ app.py")
    
    print("\n✅ כל הדרישות מתקיימות!\n")
    return True

def start_server():
    """הפעלת שרת Flask"""
    print("="*60)
    print("🌐 מפעיל שרת...")
    print("="*60 + "\n")
    
    # ייבוא מוקדם
    import database
    
    # בדיקה אם DB קיים
    if not os.path.exists(database.DB_PATH):
        print("⚙️  מסד הנתונים לא נמצא. יוצר מסד נתונים חדש...\n")
        database.init_database()
    else:
        print("✅ מסד הנתונים קיים\n")
    
    # פתיחת דפדפן אחרי 3 שניות ברקע (רק פעם אחת, לא בזמן reload)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def open_browser():
            time.sleep(3)
            webbrowser.open('http://localhost:5000')
        
        import threading
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        print("⏳ פותח דפדפן בעוד 3 שניות...\n")
    
    print("="*60)
    print("📊 המערכת רצה ב: http://localhost:5000")
    print("💡 לעצירה: לחץ Ctrl+C")
    print("="*60 + "\n")
    
    # הפעלת השרת
    try:
        import app
        app.app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("👋 השרת נעצר")
        print("="*60)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ שגיאה בהפעלת השרת: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """פונקציה ראשית"""
    try:
        # ניקוי מסך
        clear_screen()
        
        # באנר
        print_banner()
        
        # בדיקת דרישות
        if not check_requirements():
            print("\n❌ לא ניתן להפעיל את המערכת")
            print("💡 תקן את השגיאות ונסה שוב\n")
            input("לחץ Enter לסגירה...")
            sys.exit(1)
        
        # הפעלת שרת
        start_server()
        
    except KeyboardInterrupt:
        print("\n\n👋 ביי!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ שגיאה כללית: {e}")
        input("\nלחץ Enter לסגירה...")
        sys.exit(1)

if __name__ == '__main__':
    main()
