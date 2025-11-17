# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
import database
import traceback

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/accounts')
@accounts_bp.route('/accounts/')
def manage_accounts():
    """דף ניהול חשבונות"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # שליפת חשבונות
        cursor.execute('''
            SELECT 
                a.id,
                COALESCE(a.account_name, '') as account_name,
                COALESCE(a.account_number, '') as account_number,
                COALESCE(a.account_type, '') as account_type,
                COALESCE(a.institution_name, '') as institution_name,
                COALESCE(a.flow_id, 1) as flow_id,
                COALESCE(a.currency, 'ILS') as currency,
                COALESCE(a.current_balance, 0) as current_balance,
                COALESCE(a.is_active, 1) as is_active,
                COALESCE(f.name, 'כללי') as flow_name,
                a.created_at
            FROM accounts a
            LEFT JOIN flows f ON a.flow_id = f.id
            ORDER BY a.is_active DESC, a.account_name
        ''')
        
        accounts = []
        for row in cursor.fetchall():
            account_id = row[0]
            
            # הטבלה כבר מכילה current_balance, אין צורך לחשב
            current_balance = row[7]
            
            # ספירת עסקאות
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = ?', (account_id,))
            transactions_count = cursor.fetchone()[0]
            
            accounts.append({
                'id': account_id,
                'name': row[1],  # account_name
                'account_number': row[2],
                'account_type': row[3],
                'bank_name': row[4],  # institution_name
                'flow_id': row[5],
                'flow_name': row[9],
                'currency': row[6],
                'initial_balance': 0,  # לא קיים בטבלה
                'current_balance': current_balance,
                'is_active': row[8],
                'created_at': row[10],
                'transactions_count': transactions_count
            })
        
        # שליפת תזרימים לבחירה
        cursor.execute('''
            SELECT id, name 
            FROM flows 
            WHERE is_active = 1 
            ORDER BY id
        ''')
        flows = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        stats = {
            'total': len(accounts),
            'active': len([a for a in accounts if a['is_active']]),
            'bank_accounts': len([a for a in accounts if a['account_type'] == 'bank']),
            'credit_cards': len([a for a in accounts if a['account_type'] == 'credit']),
            'total_balance': sum(a['current_balance'] for a in accounts if a['is_active'])
        }
        
        return render_template('accounts/manage.html',
                             accounts=accounts,
                             flows=flows,
                             stats=stats)
    
    except Exception as e:
        error_html = f"""
        <html dir="rtl">
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">שגיאה בדף חשבונות</h1>
            <pre style="background: #f0f0f0; padding: 15px; direction: ltr;">
{traceback.format_exc()}
            </pre>
        </body>
        </html>
        """
        return error_html, 500


@accounts_bp.route('/api/accounts', methods=['POST'])
def create_account():
    """יצירת חשבון חדש"""
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO accounts (
                account_name, account_number, account_type, institution_name, 
                flow_id, currency, current_balance, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], 
              data.get('account_number', ''),
              data.get('account_type', 'bank'),
              data.get('bank_name', ''),
              data.get('flow_id', 1),
              data.get('currency', 'ILS'),
              data.get('current_balance', 0),
              data.get('is_active', 1)))
        
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': account_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    """עדכון חשבון"""
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE accounts 
            SET account_name = ?, account_number = ?, account_type = ?, 
                institution_name = ?, flow_id = ?, currency = ?, 
                current_balance = ?, is_active = ?
            WHERE id = ?
        ''', (data['name'],
              data.get('account_number', ''),
              data.get('account_type', 'bank'),
              data.get('bank_name', ''),
              data.get('flow_id', 1),
              data.get('currency', 'ILS'),
              data.get('current_balance', 0),
              data.get('is_active', 1),
              account_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@accounts_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account(account_id):
    """מחיקת חשבון"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # בדיקה שאין עסקאות בחשבון
        cursor.execute('SELECT COUNT(*) FROM transactions WHERE account_id = ?', (account_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': 'לא ניתן למחוק חשבון עם עסקאות'}), 400
        
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
