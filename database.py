# -*- coding: utf-8 -*-
"""
database.py
מנהל את מסד הנתונים SQLite
יוצר את כל הטבלאות ומספק פונקציות חיבור
"""

import sqlite3
import os
import time
from datetime import datetime
from functools import wraps

# נתיב למסד הנתונים
DB_PATH = os.path.join('data', 'financial.db')

def retry_on_locked(max_retries=3, delay=0.5):
    """דקורטור לניסיון חוזר במקרה של database locked"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if 'database is locked' in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(delay * (attempt + 1))  # המתנה מעריכית
                        continue
                    raise
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_connection():
    """יוצר חיבור למסד הנתונים עם טיפול בנעילות"""
    # וודא שתיקיית data קיימת
    os.makedirs('data', exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH, timeout=30.0)  # המתנה עד 30 שניות לנעילה
    conn.row_factory = sqlite3.Row  # מאפשר גישה לעמודות לפי שם
    conn.execute('PRAGMA foreign_keys = ON')  # אכיפת foreign keys
    conn.execute('PRAGMA journal_mode=WAL')  # מצב Write-Ahead Logging לביצועים טובים יותר
    return conn

def init_database():
    """יוצר את כל הטבלאות במסד הנתונים"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🗄️  יוצר טבלאות...")
    
    # ============================================
    # 1. טבלת flows - תזרימים
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT,
        color TEXT DEFAULT '#4A90E2',
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_flows_active ON flows(is_active)')
    print("  ✅ flows")
    
    # ============================================
    # 2. טבלת categories - קטגוריות (3 רמות)
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        parent_id INTEGER,
        level INTEGER NOT NULL CHECK(level IN (1,2,3)),
        full_path TEXT NOT NULL,
        flow_id INTEGER,
        description TEXT,
        icon TEXT,
        color TEXT,
        is_system BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE SET NULL
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_level ON categories(level)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_flow ON categories(flow_id)')
    cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_categories_path ON categories(full_path)')
    
    # בדיקה והוספת עמודת flow_id אם לא קיימת (למקרה של DB ישן)
    cursor.execute("PRAGMA table_info(categories)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'flow_id' not in columns:
        print("  ⚠️  מוסיף עמודת flow_id לטבלת categories...")
        cursor.execute('ALTER TABLE categories ADD COLUMN flow_id INTEGER')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categories_flow ON categories(flow_id)')
        print("  ✅ flow_id נוסף")
    
    print("  ✅ categories")
    
    # ============================================
    # 3. טבלת accounts - חשבונות וכרטיסים
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER NOT NULL,
        account_type TEXT NOT NULL,
        account_name TEXT NOT NULL,
        institution_name TEXT,
        account_number TEXT,
        last4_digits TEXT,
        currency TEXT DEFAULT 'ILS',
        is_active BOOLEAN DEFAULT 1,
        current_balance DECIMAL(10,2),
        last_balance_update TIMESTAMP,
        auto_import BOOLEAN DEFAULT 0,
        import_path TEXT,
        icon TEXT,
        color TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_flow ON accounts(flow_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_active ON accounts(is_active)')
    print("  ✅ accounts")
    
    # ============================================
    # 4. טבלת files - קבצים שהועלו
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER NOT NULL,
        account_id INTEGER,
        original_filename TEXT NOT NULL,
        stored_filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_type TEXT NOT NULL,
        source_name TEXT,
        file_size INTEGER,
        encoding TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT 0,
        processed_date TIMESTAMP,
        num_transactions INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_flow ON files(flow_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_account ON files(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)')
    print("  ✅ files")
    
    # ============================================
    # 5. טבלת reconciliations - התאמות
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reconciliations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER NOT NULL,
        reconciliation_date DATE NOT NULL,
        credit_card_total DECIMAL(10,2),
        bank_payment_total DECIMAL(10,2),
        difference DECIMAL(10,2) DEFAULT 0,
        status TEXT DEFAULT 'pending',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_recon_flow ON reconciliations(flow_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_recon_date ON reconciliations(reconciliation_date)')
    print("  ✅ reconciliations")
    
    # ============================================
    # 6. טבלת transactions - הטבלה המרכזית!
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flow_id INTEGER NOT NULL,
        account_id INTEGER,
        file_id INTEGER,
        
        transaction_date DATE NOT NULL,
        description TEXT NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        
        monthly_amount DECIMAL(10,2),
        total_amount DECIMAL(10,2),
        is_installment BOOLEAN DEFAULT 0,
        installment_number INTEGER,
        total_installments INTEGER,
        
        transaction_type TEXT NOT NULL,
        source_type TEXT NOT NULL,
        
        category_id INTEGER,
        bank_category TEXT,
        category_status TEXT DEFAULT 'auto',
        
        card_last4 TEXT,
        charge_date DATE,
        balance DECIMAL(10,2),
        debit DECIMAL(10,2),
        credit DECIMAL(10,2),
        
        is_reconciled BOOLEAN DEFAULT 0,
        reconciliation_id INTEGER,
        
        is_excluded BOOLEAN DEFAULT 0,
        is_duplicate BOOLEAN DEFAULT 0,
        notes TEXT,
        tags TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT DEFAULT 'system',
        
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE,
        FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
        FOREIGN KEY (reconciliation_id) REFERENCES reconciliations(id) ON DELETE SET NULL
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_flow ON transactions(flow_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_account ON transactions(account_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(transaction_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_type ON transactions(transaction_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_trans_file ON transactions(file_id)')
    print("  ✅ transactions")
    
    # ============================================
    # 7. טבלת bank_category_mappings
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bank_category_mappings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bank_category TEXT NOT NULL UNIQUE,
        user_category_id INTEGER NOT NULL,
        source_type TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_category_id) REFERENCES categories(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_mapping_bank ON bank_category_mappings(bank_category)')
    print("  ✅ bank_category_mappings")
    
    # ============================================
    # 8. טבלת learning_rules - למידה אוטומטית!
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS learning_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_type TEXT NOT NULL,
        pattern TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        flow_id INTEGER,
        source_type TEXT,
        
        usage_count INTEGER DEFAULT 0,
        success_count INTEGER DEFAULT 0,
        confidence REAL DEFAULT 1.0,
        
        priority INTEGER DEFAULT 10,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_used TIMESTAMP,
        
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_pattern ON learning_rules(pattern)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_rules(rule_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_active ON learning_rules(is_active)')
    print("  ✅ learning_rules")
    
    # ============================================
    # 9. טבלת transaction_links
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS transaction_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id_1 INTEGER NOT NULL,
        transaction_id_2 INTEGER NOT NULL,
        link_type TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id_1) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY (transaction_id_2) REFERENCES transactions(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_t1 ON transaction_links(transaction_id_1)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_links_t2 ON transaction_links(transaction_id_2)')
    print("  ✅ transaction_links")
    
    # ============================================
    # 10. טבלת audit_log
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        table_name TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user TEXT DEFAULT 'user',
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        notes TEXT
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp)')
    print("  ✅ audit_log")
    
    # ============================================
    # 11. טבלת settings
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        value_type TEXT,
        description TEXT,
        category TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  ✅ settings")
    
    # ============================================
    # 12. טבלת import_sessions
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS import_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        flow_id INTEGER NOT NULL,
        status TEXT DEFAULT 'in_progress',
        
        total_records INTEGER DEFAULT 0,
        imported_records INTEGER DEFAULT 0,
        skipped_records INTEGER DEFAULT 0,
        error_records INTEGER DEFAULT 0,
        
        auto_categorized INTEGER DEFAULT 0,
        pending_categorization INTEGER DEFAULT 0,
        
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
        FOREIGN KEY (flow_id) REFERENCES flows(id) ON DELETE CASCADE
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_import_file ON import_sessions(file_id)')
    print("  ✅ import_sessions")
    
    # ============================================
    # 13. טבלת custom_fields
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        field_name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        field_type TEXT NOT NULL,
        options TEXT,
        is_visible BOOLEAN DEFAULT 1,
        display_order INTEGER DEFAULT 100,
        column_width INTEGER DEFAULT 150,
        is_required BOOLEAN DEFAULT 0,
        validation_regex TEXT,
        min_value DECIMAL(10,2),
        max_value DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  ✅ custom_fields")
    
    # ============================================
    # 14. טבלת custom_field_values
    # ============================================
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS custom_field_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        field_id INTEGER NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
        FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
        UNIQUE(transaction_id, field_id)
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cfv_transaction ON custom_field_values(transaction_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cfv_field ON custom_field_values(field_id)')
    print("  ✅ custom_field_values")
    
    conn.commit()
    print("\n✅ כל 14 הטבלאות נוצרו בהצלחה!\n")
    
    # הוספת נתוני ברירת מחדל
    init_default_data(conn)
    
    conn.close()

def init_default_data(conn):
    """מכניס נתוני ברירת מחדל"""
    cursor = conn.cursor()
    
    print("📊 מכניס נתוני ברירת מחדל...")
    
    # תזרימים ברירת מחדל - חייב להיות לפני קטגוריות!
    cursor.execute('''
    INSERT OR IGNORE INTO flows (id, name, description, icon, color)
    VALUES (0, 'בלתי מסווג', 'קטגוריות ללא תזרים', '⚪', '#9E9E9E')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO flows (id, name, description, icon, color)
    VALUES (1, 'בית', 'תזרים הוצאות והכנסות של הבית', '🏠', '#4A90E2')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO flows (id, name, description, icon, color)
    VALUES (2, 'עסק', 'תזרים הוצאות והכנסות של העסק', '💼', '#2E7D32')
    ''')
    
    cursor.execute('''
    INSERT OR IGNORE INTO flows (id, name, description, icon, color)
    VALUES (3, 'השקעות', 'תזרים השקעות והכנסות פסיביות', '📈', '#F57C00')
    ''')
    
    # קטגוריית "לא מסווג" (מערכתית) - רק אחרי שהתזרימים קיימים
    cursor.execute('''
    INSERT OR IGNORE INTO categories (id, name, parent_id, level, full_path, flow_id, is_system)
    VALUES (0, 'לא מסווג', NULL, 1, 'לא מסווג', 0, 1)
    ''')
    
    # עדכון flow_id של קטגוריית "לא מסווג" אם קיימת כבר
    cursor.execute('''
    UPDATE categories 
    SET flow_id = 0 
    WHERE id = 0 AND (flow_id IS NULL OR flow_id != 0)
    ''')
    
    # הגדרות ברירת מחדל
    settings_data = [
        ('default_flow_id', '1', 'int', 'תזרים ברירת מחדל', 'general'),
        ('auto_categorize', 'true', 'bool', 'קיטלוג אוטומטי', 'import'),
        ('date_format', 'DD/MM/YYYY', 'string', 'פורמט תאריך', 'display'),
        ('currency_symbol', '₪', 'string', 'סמל מטבע', 'display'),
        ('learning_threshold', '0.8', 'float', 'סף למידה', 'learning'),
    ]
    
    for key, value, value_type, description, category in settings_data:
        cursor.execute('''
        INSERT OR IGNORE INTO settings (key, value, value_type, description, category)
        VALUES (?, ?, ?, ?, ?)
        ''', (key, value, value_type, description, category))
    
    conn.commit()
    print("  ✅ נתוני ברירת מחדל הוכנסו\n")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 יוצר מסד נתונים חדש")
    print("="*50 + "\n")
    init_database()
    print("="*50)
    print("✅ מסד הנתונים מוכן לשימוש!")
    print(f"📁 נמצא ב: {os.path.abspath(DB_PATH)}")
    print("="*50 + "\n")
