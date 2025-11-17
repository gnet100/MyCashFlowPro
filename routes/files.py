# -*- coding: utf-8 -*-
"""
routes/files.py
נתיבי API לקבצים
"""

from flask import Blueprint, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from services.file_service import FileService

files_bp = Blueprint('files', __name__)

# יצירת FileService
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'files'))
file_service = FileService(UPLOAD_FOLDER)


@files_bp.route('/files')
@files_bp.route('/files/')
def files_list():
    """דף רשימת קבצים"""
    try:
        import database
        
        flow_id = request.args.get('flow_id', type=int)
        files = file_service.get_all_files(flow_id)
        
        # שליפת רשימת תזרימים
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
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'is_active': row[3]
            })
        
        conn.close()
        
        return render_template('files/files.html', 
                             files=files,
                             flows=flows,
                             current_flow_id=flow_id)
    
    except Exception as e:
        return f"שגיאה: {str(e)}", 500


@files_bp.route('/api/files/upload', methods=['POST'])
def upload_file():
    """העלאת קובץ"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'לא נבחר קובץ'}), 400
        
        file = request.files['file']
        flow_id = request.form.get('flow_id', 1, type=int)
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'שם קובץ ריק'}), 400
        
        # שמירת הקובץ
        success, file_id, error_message, duplicate_info = file_service.save_upload(file, flow_id)
        
        # טיפול בכפילות
        if duplicate_info:
            return jsonify({
                'success': False,
                'duplicate': True,
                'duplicate_info': duplicate_info
            }), 409
        
        if success:
            return jsonify({
                'success': True,
                'message': 'הקובץ הועלה בהצלחה!',
                'file_id': file_id
            })
        else:
            return jsonify({
                'success': False,
                'error': error_message or 'שגיאה בהעלאת הקובץ'
            }), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/files/<int:file_id>/process', methods=['POST'])
def process_file(file_id):
    """עיבוד קובץ לטרנזקציות"""
    try:
        flow_id = request.json.get('flow_id', 1) if request.json else 1
        
        success, error_message, num_transactions = file_service.process_file_to_transactions(file_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'הקובץ עובד בהצלחה! נוצרו {num_transactions} עסקאות',
                'num_transactions': num_transactions
            })
        else:
            return jsonify({
                'success': False,
                'error': error_message or 'שגיאה בעיבוד הקובץ'
            }), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """מחיקת קובץ"""
    try:
        success, error_message = file_service.delete_file(file_id)
        
        if success:
            return jsonify({'success': True, 'message': 'הקובץ נמחק בהצלחה'})
        else:
            return jsonify({'success': False, 'error': error_message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/files/<int:file_id>/details')
def get_file_details(file_id):
    """פרטי קובץ"""
    try:
        file_info = file_service.get_file_details(file_id)
        
        if file_info:
            return jsonify({'success': True, 'file': file_info})
        else:
            return jsonify({'success': False, 'error': 'קובץ לא נמצא'}), 404
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@files_bp.route('/api/files/clean-orphaned', methods=['POST'])
def clean_orphaned_records():
    """ניקוי רשומות ללא קובץ פיזי"""
    try:
        num_cleaned, num_transactions = file_service.clean_orphaned_records()
        
        if num_cleaned > 0:
            return jsonify({
                'success': True, 
                'message': f'נוקו {num_cleaned} רשומות ישנות ({num_transactions} עסקאות נמחקו)',
                'num_cleaned': num_cleaned,
                'num_transactions': num_transactions
            })
        else:
            return jsonify({
                'success': True,
                'message': 'לא נמצאו רשומות ישנות',
                'num_cleaned': 0,
                'num_transactions': 0
            })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

