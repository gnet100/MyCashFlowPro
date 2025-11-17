# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
import database
import traceback

flows_bp = Blueprint('flows', __name__)

@flows_bp.route('/flows')
@flows_bp.route('/flows/')
def manage_flows():
    """דף ניהול תזרימים"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # שליפת תזרימים
        cursor.execute('''
            SELECT 
                id,
                COALESCE(name, '') as name,
                COALESCE(description, '') as description,
                COALESCE(icon, '') as icon,
                COALESCE(color, '#4A90E2') as color,
                COALESCE(is_active, 1) as is_active,
                created_at
            FROM flows
            ORDER BY id
        ''')
        
        flows = []
        for row in cursor.fetchall():
            flow_id = row[0]
            
            # ספירת חשבונות בתזרים
            cursor.execute('SELECT COUNT(*) FROM accounts WHERE flow_id = ? AND is_active = 1', (flow_id,))
            accounts_count = cursor.fetchone()[0]
            
            # ספירת קטגוריות בתזרים
            cursor.execute('SELECT COUNT(*) FROM categories WHERE flow_id = ?', (flow_id,))
            categories_count = cursor.fetchone()[0]
            
            # ספירת עסקאות בתזרים
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE flow_id = ?', (flow_id,))
            transactions_count = cursor.fetchone()[0]
            
            flows.append({
                'id': flow_id,
                'name': row[1],
                'description': row[2],
                'icon': row[3],
                'color': row[4],
                'is_active': row[5],
                'created_at': row[6],
                'stats': {
                    'accounts': accounts_count,
                    'categories': categories_count,
                    'transactions': transactions_count
                }
            })
        
        conn.close()
        
        stats = {
            'total': len(flows),
            'active': len([f for f in flows if f['is_active']]),
            'inactive': len([f for f in flows if not f['is_active']])
        }
        
        return render_template('flows/manage.html',
                             flows=flows,
                             stats=stats)
    
    except Exception as e:
        error_html = f"""
        <html dir="rtl">
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">שגיאה בדף תזרימים</h1>
            <pre style="background: #f0f0f0; padding: 15px; direction: ltr;">
{traceback.format_exc()}
            </pre>
        </body>
        </html>
        """
        return error_html, 500


@flows_bp.route('/api/flows', methods=['POST'])
def create_flow():
    """יצירת תזרים חדש"""
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO flows (name, description, icon, color, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], 
              data.get('description', ''), 
              data.get('icon', ''), 
              data.get('color', '#4A90E2'),
              data.get('is_active', 1)))
        
        conn.commit()
        flow_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': flow_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@flows_bp.route('/api/flows/<int:flow_id>', methods=['PUT'])
def update_flow(flow_id):
    """עדכון תזרים"""
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE flows 
            SET name = ?, description = ?, icon = ?, color = ?, is_active = ?
            WHERE id = ?
        ''', (data['name'], 
              data.get('description', ''), 
              data.get('icon', ''),
              data.get('color', '#4A90E2'),
              data.get('is_active', 1),
              flow_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@flows_bp.route('/api/flows/<int:flow_id>', methods=['DELETE'])
def delete_flow(flow_id):
    """מחיקת תזרים"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # בדיקה שאין חשבונות או קטגוריות בתזרים
        cursor.execute('SELECT COUNT(*) FROM accounts WHERE flow_id = ?', (flow_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': 'לא ניתן למחוק תזרים עם חשבונות'}), 400
        
        cursor.execute('SELECT COUNT(*) FROM categories WHERE flow_id = ?', (flow_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': 'לא ניתן למחוק תזרים עם קטגוריות'}), 400
        
        cursor.execute('DELETE FROM flows WHERE id = ?', (flow_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
