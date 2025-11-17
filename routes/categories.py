# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
import database
import traceback

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
@categories_bp.route('/categories/')
def manage_categories():
    """דף ניהול קטגוריות"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        # שליפת קטגוריות
        cursor.execute('''
            SELECT 
                id,
                COALESCE(name, '') as name,
                parent_id,
                COALESCE(level, 1) as level,
                COALESCE(color, '#808080') as color
            FROM categories
            ORDER BY level, name
        ''')
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'parent_id': row[2],
                'level': row[3],
                'color': row[4],
                'usage_count': 0
            })
        
        conn.close()
        
        stats = {
            'total': len(categories),
            'root': len([c for c in categories if c['parent_id'] is None]),
            'uncategorized': 0
        }
        
        return render_template('categories/manage.html',
                             categories=categories,
                             stats=stats)
    
    except Exception as e:
        error_html = f"""
        <html dir="rtl">
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: red;">שגיאה בדף קטגוריות</h1>
            <pre style="background: #f0f0f0; padding: 15px; direction: ltr;">
{traceback.format_exc()}
            </pre>
        </body>
        </html>
        """
        return error_html, 500


@categories_bp.route('/api/categories', methods=['POST'])
def create_category():
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        level = 1
        if data.get('parent_id'):
            cursor.execute('SELECT level FROM categories WHERE id = ?', (data['parent_id'],))
            parent = cursor.fetchone()
            if parent:
                level = parent[0] + 1
        
        cursor.execute('''
            INSERT INTO categories (name, parent_id, level, color, flow_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data.get('parent_id'), level, 
              data.get('color', '#808080'), data.get('flow_id', 1)))
        
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'id': category_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@categories_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    try:
        data = request.json
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE categories 
            SET name = ?, color = ?
            WHERE id = ?
        ''', (data['name'], data.get('color', '#808080'), category_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@categories_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM categories WHERE parent_id = ?', (category_id,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'error': 'לא ניתן למחוק קטגוריה עם תתי-קטגוריות'}), 400
        
        cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@categories_bp.route('/api/categories/by-flow/<int:flow_id>')
def get_categories_by_flow(flow_id):
    """שליפת קטגוריות לפי תזרים"""
    try:
        conn = database.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, level, parent_id
            FROM categories
            WHERE flow_id = ? OR flow_id IS NULL
            ORDER BY level, name
        ''', (flow_id,))
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'id': row[0],
                'name': row[1],
                'level': row[2],
                'parent_id': row[3]
            })
        
        conn.close()
        
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
