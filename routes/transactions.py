# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
import database
import traceback

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions')
@transactions_bp.route('/transactions/')
def list_transactions():
    """רשימת טרנזקציות"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # שליפת עסקאות
        cursor.execute('''
            SELECT 
                t.id, 
                COALESCE(t.transaction_date, '') as transaction_date,
                COALESCE(t.description, '') as description,
                COALESCE(t.amount, 0) as amount,
                COALESCE(t.transaction_type, '') as transaction_type
            FROM transactions t
            ORDER BY t.transaction_date DESC
            LIMIT 100
        ''')
        
        transactions = []
        for row in cursor.fetchall():
            transactions.append({
                'id': row[0],
                'date': row[1],
                'description': row[2],
                'amount': row[3],
                'type': row[4],
                'category': 'לא מסווג',
                'account': '-',
                'flow': '-'
            })
        
        # סטטיסטיקות
        cursor.execute('''
            SELECT 
                COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END), 0),
                COALESCE(SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END), 0),
                COUNT(*)
            FROM transactions
        ''')
        stats_row = cursor.fetchone()
        
        conn.close()
        
        stats = {
            'income': stats_row[0],
            'expenses': stats_row[1],
            'balance': stats_row[0] - stats_row[1],
            'total': stats_row[2]
        }
        
        return render_template('transactions/list.html',
                             transactions=transactions,
                             stats=stats,
                             flows=[],
                             current_flow_id=None)
    
    except Exception as e:
        error_html = f"""
        <html dir="rtl">
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">שגיאה בדף רשומות</h1>
            <pre style="background: #f0f0f0; padding: 15px; direction: ltr;">
{traceback.format_exc()}
            </pre>
        </body>
        </html>
        """
        return error_html, 500


@transactions_bp.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
