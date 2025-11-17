# -*- coding: utf-8 -*-
"""
app.py
הקובץ הראשי של האפליקציה
מפעיל את שרת Flask ומגדיר את כל ה-routes
"""

from flask import Flask, render_template, jsonify, redirect, url_for, request
import database
import os

# יצירת אפליקצית Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = os.path.join('data', 'files')

# וודא שתיקיות קיימות
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# וודא שמסד הנתונים קיים - אם לא, צור אותו
if not os.path.exists(database.DB_PATH):
    print("⚙️  מסד הנתונים לא נמצא. יוצר מסד נתונים חדש...")
    database.init_database()
    print("✅ מסד הנתונים נוצר בהצלחה!")

# ייבוא blueprints
from routes.transactions import transactions_bp
from routes.categories import categories_bp
from routes.files import files_bp
from routes.flows import flows_bp
from routes.accounts import accounts_bp

# רישום blueprints
app.register_blueprint(transactions_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(files_bp)
app.register_blueprint(flows_bp)
app.register_blueprint(accounts_bp)

# ============================================
# Routes - נתיבים
# ============================================

@app.route('/')
def home():
    """דף הבית"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # סטטיסטיקות בסיסיות
        stats = {}
        
        # מספר תזרימים
        cursor.execute('SELECT COUNT(*) FROM flows WHERE is_active = 1')
        stats['flows'] = cursor.fetchone()[0]
        
        # מספר חשבונות
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE is_active = 1')
        stats['accounts'] = cursor.fetchone()[0]
        
        # מספר קטגוריות (ללא "לא מסווג" id=0)
        cursor.execute('SELECT COUNT(*) FROM categories WHERE id > 0')
        stats['categories'] = cursor.fetchone()[0]
        
        # מספר רשומות
        cursor.execute('SELECT COUNT(*) FROM transactions')
        stats['transactions'] = cursor.fetchone()[0]
        
        # מספר קבצים
        cursor.execute('SELECT COUNT(*) FROM files')
        stats['files'] = cursor.fetchone()[0]
        
        # רשומות לא מסווגות
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE category_id = 0 OR category_id IS NULL')
        stats['uncategorized'] = cursor.fetchone()[0]
        
        # רשימת תזרימים
        cursor.execute('''
            SELECT id, name, description, is_active, created_at
            FROM flows
            WHERE is_active = 1
            ORDER BY CASE WHEN id = 0 THEN 999 ELSE id END
        ''')
        flows_data = cursor.fetchall()
        
        flows = []
        active_flow_id = 1  # ברירת מחדל
        
        for flow in flows_data:
            flow_id, name, description, is_active, created_at = flow
            
            # סטטיסטיקות לכל תזרים
            cursor.execute('SELECT COUNT(*) FROM accounts WHERE flow_id = ? AND is_active = 1', (flow_id,))
            flow_accounts = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE flow_id = ?', (flow_id,))
            flow_transactions = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM files WHERE flow_id = ?', (flow_id,))
            flow_files = cursor.fetchone()[0]
            
            flows.append({
                'id': flow_id,
                'name': name,
                'description': description,
                'is_active': is_active,
                'created_at': created_at,
                'stats': {
                    'accounts': flow_accounts,
                    'transactions': flow_transactions,
                    'files': flow_files
                }
            })
        
        conn.close()
        
        return render_template('home.html', 
                             stats=stats, 
                             flows=flows,
                             active_flow_id=active_flow_id)
    
    except Exception as e:
        return render_template('home.html', stats={}, flows=[], error=str(e))

@app.route('/api/flows')
def api_flows():
    """API לשליפת רשימת תזרימים"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, description, is_active
            FROM flows
            WHERE is_active = 1
            ORDER BY id
        ''')
        
        flows = []
        for row in cursor.fetchall():
            flows.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'is_active': row['is_active']
            })
        
        conn.close()
        
        return jsonify({'success': True, 'flows': flows})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/database')
def database_tables():
    """דף טבלאות מסד הנתונים"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # קבלת רשימת כל הטבלאות
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            ORDER BY name
        """)
        table_names = [row[0] for row in cursor.fetchall()]
        
        # תיאורי טבלאות
        table_descriptions = {
            'flows': 'תזרימי כספים - הפרדה בין בית, עסק, השקעות',
            'categories': 'קטגוריות בהיררכיה של 3 רמות',
            'accounts': 'חשבונות בנק וכרטיסי אשראי',
            'files': 'קבצים שהועלו למערכת',
            'transactions': 'רשומות פיננסיות - הטבלה המרכזית',
            'bank_category_mappings': 'מיפוי בין קטגוריות בנק לקטגוריות משלך',
            'learning_rules': 'כללי למידה אוטומטית לסיווג רשומות',
            'reconciliations': 'התאמות בין חיובי כרטיס לבנק',
            'transaction_links': 'קישורים בין רשומות (העברות, תשלומים)',
            'audit_log': 'רישום היסטורי של כל השינויים',
            'settings': 'הגדרות מערכת גלובליות',
            'import_sessions': 'מעקב אחר סשני ייבוא קבצים',
            'custom_fields': 'הגדרות עמודות מותאמות אישית',
            'custom_field_values': 'ערכים של עמודות מותאמות'
        }
        
        # מידע מפורט על כל טבלה
        tables = {}
        total_records = 0
        
        for table_name in table_names:
            # קבלת מבנה הטבלה
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for col in cursor.fetchall():
                columns.append({
                    'name': col[1],
                    'type': col[2]
                })
            
            # ספירת רשומות (לטבלת categories - ללא "לא מסווג" id=0)
            if table_name == 'categories':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE id > 0")
            else:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            total_records += count
            
            # נתוני דוגמה (עד 5 שורות) - לטבלת categories ללא id=0
            if table_name == 'categories':
                cursor.execute(f"SELECT * FROM {table_name} WHERE id > 0 LIMIT 5")
            else:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            
            tables[table_name] = {
                'columns': columns,
                'count': count,
                'sample_data': sample_data,
                'description': table_descriptions.get(table_name, '')
            }
        
        # גודל DB
        db_path = database.DB_PATH
        db_size_kb = 0
        if os.path.exists(db_path):
            db_size_kb = round(os.path.getsize(db_path) / 1024, 2)
        
        conn.close()
        
        return render_template('database_tables.html',
                             tables=tables,
                             db_size_kb=db_size_kb,
                             total_records=total_records)
    
    except Exception as e:
        return render_template('database_tables.html',
                             tables={},
                             db_size_kb=0,
                             total_records=0,
                             error=str(e))

@app.route('/database/table/<table_name>')
def view_full_table(table_name):
    """צפייה בכל נתוני טבלה"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # קבלת מבנה הטבלה
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # קבלת כל הנתונים (לטבלת categories - ללא id=0)
        if table_name == 'categories':
            cursor.execute(f"SELECT * FROM {table_name} WHERE id > 0")
        else:
            cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        conn.close()
        
        # יצירת HTML פשוט לתצוגה
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>טבלה: {table_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 2rem;
                    background: #f5f5f5;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 1rem;
                }}
                .info {{
                    background: white;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-bottom: 1rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                th, td {{
                    padding: 0.75rem;
                    text-align: right;
                    border-bottom: 1px solid #e0e0e0;
                }}
                th {{
                    background: #4a90e2;
                    color: white;
                    font-weight: 600;
                    position: sticky;
                    top: 0;
                }}
                tr:hover {{
                    background: #f8f9fa;
                }}
                .close-btn {{
                    background: #4a90e2;
                    color: white;
                    padding: 0.5rem 1rem;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1rem;
                }}
                .close-btn:hover {{
                    background: #357abd;
                }}
            </style>
        </head>
        <body>
            <button class="close-btn" onclick="window.close()">✖ סגור</button>
            <h1>טבלה: {table_name}</h1>
            <div class="info">
                <strong>סה"כ רשומות:</strong> {len(rows)}
            </div>
            <table>
                <thead>
                    <tr>
                        {''.join(f'<th>{col}</th>' for col in columns)}
                    </tr>
                </thead>
                <tbody>
                    {''.join('<tr>' + ''.join(f'<td>{val if val is not None else "-"}</td>' for val in row) + '</tr>' for row in rows)}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html
    
    except Exception as e:
        return f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <title>שגיאה</title>
        </head>
        <body>
            <h1>שגיאה</h1>
            <p>{str(e)}</p>
            <button onclick="window.close()">סגור</button>
        </body>
        </html>
        """, 500

@app.route('/api/stats')
def api_stats():
    """API לסטטיסטיקות"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # מספר טבלאות
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        stats['tables'] = cursor.fetchone()[0]
        
        # גודל DB
        db_path = database.DB_PATH
        if os.path.exists(db_path):
            stats['db_size'] = os.path.getsize(db_path)
        else:
            stats['db_size'] = 0
        
        conn.close()
        
        return jsonify(stats)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """בדיקת בריאות המערכת"""
    try:
        conn = database.get_connection()
        conn.close()
        return jsonify({'status': 'ok', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/load-mock-data')
def load_mock_data():
    """טעינת נתוני Mock Data"""
    try:
        import mock_data
        mock_data.init_mock_data()
        return redirect(url_for('home'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# הפעלת האפליקציה
# ============================================

if __name__ == '__main__':
    import webbrowser
    from threading import Timer
    import os
    
    print("\n" + "="*60)
    print("🚀 מערכת ניהול כספים")
    print("="*60 + "\n")
    
    # בדיקה אם DB קיים, אם לא - יוצר אותו
    if not os.path.exists(database.DB_PATH):
        print("⚙️  מסד הנתונים לא נמצא. יוצר מסד נתונים חדש...\n")
        database.init_database()
    else:
        print("✅ מסד הנתונים קיים\n")
    
    print("="*60)
    print("🌐 השרת רץ ב:")
    print("   http://localhost:5000")
    print("   http://127.0.0.1:5000")
    print("\n💡 לעצירה: לחץ Ctrl+C")
    print("="*60 + "\n")
    
    # פתיחת דפדפן אוטומטית רק פעם אחת (לא בזמן reload)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        def open_browser():
            webbrowser.open('http://localhost:5000')
        
        Timer(1.5, open_browser).start()
    
    # הפעלת השרת
    app.run(debug=True, host='0.0.0.0', port=5000)
