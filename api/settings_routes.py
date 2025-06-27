"""
Settings Routes Module for Offline Attenda@settings_bp.route('/api/denied', methods=['GET'])
def api_denied():
    try:
        from database.operations import get_denied_attempts_with_details
        denied = get_denied_attempts_with_details()
        return jsonify(denied)
    except Exception as e:
        print(f"Error getting denied attempts: {e}")
        return jsonify([])

This module contains all settings and data management endpoints:
- System settings configuration
- Data export functionality
- Data retrieval for various tables
- Email reporting and scheduling
- Report generation and preview

Settings Management Features:
- System configuration management
- Data export in multiple formats (PDF, Excel, CSV)
- Email report functionality with SMTP configuration
- Scheduled report management
- Data preview and analytics
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from database.operations import get_settings, update_settings, get_all_data
from services.reports import reports_service

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/api/attendances')
def api_attendances():
    try:
        from database.operations import get_attendance_records_with_details
        attendances = get_attendance_records_with_details()
        
        # Process device_info if it exists
        for attendance in attendances:
            if 'device_info' in attendance and attendance['device_info']:
                try:
                    # device_info might be JSON string, keep it as is for the frontend
                    pass
                except:
                    # If not JSON, leave as is
                    pass
        
        return jsonify(attendances)
    except Exception as e:
        print(f"Error getting attendances: {e}")
        return jsonify([])

@settings_bp.route('/api/denied')
def api_denied():
    try:
        denied = get_all_data('denied_attempts')
        for attempt in denied:
            if 'device_fingerprint_id' in attempt and attempt['device_fingerprint_id']:
                attempt['device_fingerprint_id'] = attempt['device_fingerprint_id'][:8] + '...'
        return jsonify(denied)
    except Exception as e:
        return jsonify([])

@settings_bp.route('/api/device_fingerprints', methods=['GET'])
def api_device_fingerprints():
    try:
        fingerprints = get_all_data('device_fingerprints')
        for fp in fingerprints:
            if 'hash' in fp and fp['hash']:
                fp['hash'] = fp['hash'][:8] + '...'
        return jsonify(fingerprints)
    except Exception as e:
        return jsonify([])

@settings_bp.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    try:
        if request.method == 'GET':
            return jsonify(get_settings())
        
        data = request.json or {}
        update_settings(data)
        return jsonify(get_settings())
    except Exception as e:
        return jsonify(get_settings())

@settings_bp.route('/api/export_data')
def export_data():
    try:
        export_data = {
            'class_attendees': get_all_data('class_attendees'),
            'denied_attempts': get_all_data('denied_attempts'),
            'settings': get_settings(),
            'device_fingerprints': get_all_data('device_fingerprints'),
            'export_timestamp': datetime.utcnow().isoformat()
        }
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)})

# Export and reporting endpoints
@settings_bp.route('/api/export/pdf')
def export_pdf():
    """Generate and download PDF report"""
    try:
        report_type = request.args.get('type', 'comprehensive')
        date_range = None
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date and end_date:
            date_range = (start_date, end_date)
        
        pdf_path = reports_service.generate_pdf_report(report_type, date_range)
        return send_file(pdf_path, as_attachment=True, download_name=os.path.basename(pdf_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/export/excel')
def export_excel():
    """Generate and download Excel report"""
    try:
        excel_path = reports_service.export_to_excel()
        return send_file(excel_path, as_attachment=True, download_name=os.path.basename(excel_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/export/csv')
def export_csv():
    """Generate and download CSV export"""
    try:
        data_type = request.args.get('type', 'all')
        csv_path = reports_service.export_to_csv(data_type)
        
        if data_type == 'all':
            # Return info about generated files
            return jsonify({
                'message': 'CSV files generated successfully',
                'files': [
                    f"{csv_path}_students.csv",
                    f"{csv_path}_attendance.csv", 
                    f"{csv_path}_sessions.csv"
                ]
            })
        else:
            return send_file(csv_path, as_attachment=True, download_name=os.path.basename(csv_path))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/reports/email', methods=['POST'])
def send_email_report():
    """Send email report to specified recipient"""
    try:
        data = request.json or {}
        recipient_email = data.get('recipient_email')
        report_type = data.get('report_type', 'pdf')
        smtp_config = data.get('smtp_config')
        
        if not recipient_email:
            return jsonify({'error': 'Recipient email is required'}), 400
        
        success = reports_service.send_email_report(recipient_email, report_type, smtp_config)
        
        if success:
            return jsonify({'message': 'Email report sent successfully'})
        else:
            return jsonify({'error': 'Failed to send email report'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@settings_bp.route('/api/reports/schedule', methods=['POST'])
def schedule_reports():
    """Schedule automated email reports"""
    try:
        schedule_config = request.json or {}
        
        required_fields = ['recipient_email', 'frequency', 'time']
        if not all(field in schedule_config for field in required_fields):
            return jsonify({'error': 'Missing required scheduling fields'}), 400
        
        reports_service.schedule_reports(schedule_config)
        return jsonify({'message': 'Report scheduling configured successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
