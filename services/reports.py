"""
Reports and Export Service Module for Offline Attendance System

This module handles all export and reporting functionality including PDF reports,
Excel exports, CSV exports, and scheduled email reports.
"""

import os
import csv
import pandas as pd
import xlsxwriter
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import schedule
import time
import threading

from database.operations import (
    get_all_data, get_students_with_attendance_data, 
    get_all_students, get_settings
)

# Default email configuration
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'ofasccs@gmail.com',
    'sender_password': 'hclrcrjgjkywydnr',
    'sender_name': 'Attendance-System'
}

class ReportsService:
    def __init__(self):
        self.reports_dir = "reports"
        self.ensure_reports_directory()
    
    def ensure_reports_directory(self):
        """Create reports directory if it doesn't exist"""
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def generate_pdf_report(self, report_type="comprehensive", date_range=None):
        """Generate a professional PDF attendance report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.reports_dir}/attendance_report_{report_type}_{timestamp}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,
            textColor=colors.darkblue
        )
        story.append(Paragraph("Attendance Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata
        meta_style = styles['Normal']
        story.append(Paragraph(f"<b>Report Type:</b> {report_type.title()}", meta_style))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
        if date_range:
            story.append(Paragraph(f"<b>Date Range:</b> {date_range[0]} to {date_range[1]}", meta_style))
        story.append(Spacer(1, 20))
        
        # Get data
        students_data = get_students_with_attendance_data()
        attendance_data = get_all_data('attendances')
        
        # Summary statistics
        total_students = len(students_data)
        total_sessions = len(set([att.get('session_id') for att in attendance_data if att.get('session_id')]))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Students', str(total_students)],
            ['Total Sessions', str(total_sessions)],
            ['Total Check-ins', str(len(attendance_data))],
            ['Average Attendance', f"{(len(attendance_data) / max(total_students, 1) * 100):.1f}%"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Summary Statistics", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Student attendance table
        if report_type in ['comprehensive', 'detailed']:
            story.append(Paragraph("Student Attendance Details", styles['Heading2']))
            
            student_table_data = [['Student ID', 'Name', 'Course', 'Present Count', 'Absent Count', 'Attendance Rate']]
            
            for student in students_data:
                present_count = len([att for att in attendance_data if att.get('student_id') == student.get('student_id')])
                absent_count = student.get('absent_count', 0)
                total_sessions_for_student = present_count + absent_count
                attendance_rate = (present_count / max(total_sessions_for_student, 1)) * 100 if total_sessions_for_student > 0 else 0
                
                student_table_data.append([
                    student.get('student_id', ''),
                    student.get('name', ''),
                    student.get('course', ''),
                    str(present_count),
                    str(absent_count),
                    f"{attendance_rate:.1f}%"
                ])
            
            student_table = Table(student_table_data)
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(student_table)
        
        # Build PDF
        doc.build(story)
        return filename
    
    def export_to_excel(self, filename=None):
        """Export attendance data to Excel with multiple sheets and formatting"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.reports_dir}/attendance_data_{timestamp}.xlsx"
        
        # Get all data
        students_data = get_students_with_attendance_data()
        attendance_data = get_all_data('attendances')
        sessions_data = get_all_data('attendance_sessions')
        denied_attempts = get_all_data('denied_attempts')
        
        # Create workbook
        workbook = xlsxwriter.Workbook(filename)
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#D7E4BC',
            'border': 1
        })
        
        data_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'num_format': '#,##0'
        })
        
        # Students sheet
        students_sheet = workbook.add_worksheet('Students')
        students_headers = ['Student ID', 'Name', 'Course', 'Year', 'Last Check-in', 'Status', 'Absent Count', 'Created At']
        
        for col, header in enumerate(students_headers):
            students_sheet.write(0, col, header, header_format)
        
        for row, student in enumerate(students_data, 1):
            students_sheet.write(row, 0, student.get('student_id', ''), data_format)
            students_sheet.write(row, 1, student.get('name', ''), data_format)
            students_sheet.write(row, 2, student.get('course', ''), data_format)
            students_sheet.write(row, 3, student.get('year', ''), number_format)
            students_sheet.write(row, 4, student.get('last_check_in', ''), data_format)
            students_sheet.write(row, 5, student.get('status', ''), data_format)
            students_sheet.write(row, 6, student.get('absent_count', 0), number_format)
            students_sheet.write(row, 7, student.get('created_at', ''), data_format)
        
        students_sheet.set_column('A:H', 15)
        
        # Attendance sheet
        attendance_sheet = workbook.add_worksheet('Attendance Records')
        attendance_headers = ['ID', 'Student ID', 'Session ID', 'Check-in Time', 'Device Info', 'Fingerprint Hash']
        
        for col, header in enumerate(attendance_headers):
            attendance_sheet.write(0, col, header, header_format)
        
        for row, record in enumerate(attendance_data, 1):
            attendance_sheet.write(row, 0, record.get('id', ''), number_format)
            attendance_sheet.write(row, 1, record.get('student_id', ''), data_format)
            attendance_sheet.write(row, 2, record.get('session_id', ''), data_format)
            attendance_sheet.write(row, 3, record.get('checkin_time', ''), data_format)
            attendance_sheet.write(row, 4, record.get('device_info', ''), data_format)
            attendance_sheet.write(row, 5, record.get('fingerprint_hash', ''), data_format)
        
        attendance_sheet.set_column('A:F', 20)
        
        # Summary statistics sheet
        summary_sheet = workbook.add_worksheet('Summary')
        
        total_students = len(students_data)
        total_sessions = len(sessions_data)
        total_checkins = len(attendance_data)
        total_denied = len(denied_attempts)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Students', total_students],
            ['Total Sessions', total_sessions],
            ['Total Check-ins', total_checkins],
            ['Total Denied Attempts', total_denied],
            ['Average Attendance Rate', total_checkins / max(total_students, 1) if total_students > 0 else 0]
        ]
        
        for row, (metric, value) in enumerate(summary_data):
            if row == 0:
                summary_sheet.write(row, 0, metric, header_format)
                summary_sheet.write(row, 1, value, header_format)
            else:
                summary_sheet.write(row, 0, metric, data_format)
                summary_sheet.write(row, 1, value, number_format)
        
        summary_sheet.set_column('A:B', 25)
        
        workbook.close()
        return filename
    
    def export_to_csv(self, data_type="all", filename=None):
        """Export data to CSV format"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.reports_dir}/attendance_export_{data_type}_{timestamp}.csv"
        
        if data_type == "students":
            data = get_students_with_attendance_data()
            headers = ['student_id', 'name', 'course', 'year', 'last_check_in', 'status', 'absent_count', 'created_at']
        elif data_type == "attendance":
            data = get_all_data('attendances')
            headers = ['id', 'student_id', 'session_id', 'checkin_time', 'device_info', 'fingerprint_hash']
        elif data_type == "sessions":
            data = get_all_data('attendance_sessions')
            headers = ['id', 'name', 'created_at', 'started_at', 'ended_at', 'status', 'token']
        else:  # all data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.export_to_csv("students", f"{self.reports_dir}/students_{timestamp}.csv")
            self.export_to_csv("attendance", f"{self.reports_dir}/attendance_{timestamp}.csv")
            self.export_to_csv("sessions", f"{self.reports_dir}/sessions_{timestamp}.csv")
            return f"{self.reports_dir}/complete_export_{timestamp}"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for row in data:
                filtered_row = {key: row.get(key, '') for key in headers}
                writer.writerow(filtered_row)
        
        return filename
    
    def send_email_report(self, recipient_email, report_type="pdf", smtp_config=None):
        """Send email report to specified recipient"""
        if not smtp_config:
            smtp_config = EMAIL_CONFIG
        
        # Generate report
        if report_type == "pdf":
            attachment_path = self.generate_pdf_report("comprehensive")
            attachment_name = os.path.basename(attachment_path)
        elif report_type == "excel":
            attachment_path = self.export_to_excel()
            attachment_name = os.path.basename(attachment_path)
        else:
            attachment_path = self.export_to_csv("all")
            attachment_name = f"attendance_data_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # Get report statistics for email body
        analytics = self.get_attendance_analytics()
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = smtp_config['sender_email']
        msg['To'] = recipient_email
        msg['Subject'] = f"Attendance Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""Dear Instructor,

Please find attached the attendance report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.

Report Details:
- Report Type: {report_type.upper()}
- Total Students: {analytics['overview']['total_students']}
- Total Sessions: {analytics['overview']['total_sessions']}
- Total Check-ins: {analytics['overview']['total_checkins']}

Best regards,
Attendance System"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach file
        if os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {attachment_name}')
            msg.attach(part)
        
        # Send email
        try:
            server = smtplib.SMTP(smtp_config['smtp_server'], smtp_config['smtp_port'])
            server.starttls()
            server.login(smtp_config['sender_email'], smtp_config['sender_password'])
            text = msg.as_string()
            server.sendmail(smtp_config['sender_email'], recipient_email, text)
            server.quit()
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def schedule_reports(self, schedule_config):
        """Schedule automated reports"""
        def send_scheduled_report():
            self.send_email_report(
                schedule_config['recipient_email'],
                schedule_config.get('report_type', 'pdf'),
                schedule_config.get('smtp_config')
            )
        
        if schedule_config['frequency'] == 'daily':
            schedule.every().day.at(schedule_config['time']).do(send_scheduled_report)
        elif schedule_config['frequency'] == 'weekly':
            schedule.every().week.do(send_scheduled_report)
        elif schedule_config['frequency'] == 'monthly':
            # Use a workaround for monthly scheduling since schedule library doesn't support it directly
            schedule.every(30).days.do(send_scheduled_report)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def get_attendance_analytics(self):
        """Generate comprehensive attendance analytics"""
        students_data = get_students_with_attendance_data()
        attendance_data = get_all_data('attendances')
        sessions_data = get_all_data('attendance_sessions')
        
        analytics = {
            'overview': {
                'total_students': len(students_data),
                'total_sessions': len(sessions_data),
                'total_checkins': len(attendance_data),
                'active_sessions': len([s for s in sessions_data if s.get('status') == 'active'])
            },
            'attendance_rates': {},
            'course_breakdown': {},
        }
        
        # Calculate attendance rates by student
        for student in students_data:
            student_checkins = len([att for att in attendance_data if att.get('student_id') == student.get('student_id')])
            total_sessions_for_student = student_checkins + student.get('absent_count', 0)
            if total_sessions_for_student > 0:
                rate = (student_checkins / total_sessions_for_student) * 100
                analytics['attendance_rates'][student.get('student_id')] = {
                    'name': student.get('name'),
                    'rate': round(rate, 2),
                    'present': student_checkins,
                    'absent': student.get('absent_count', 0)
                }
        
        # Course breakdown
        courses = {}
        for student in students_data:
            course = student.get('course', 'Unknown')
            if course not in courses:
                courses[course] = {'students': 0, 'checkins': 0}
            courses[course]['students'] += 1
            courses[course]['checkins'] += len([att for att in attendance_data if att.get('student_id') == student.get('student_id')])
        
        analytics['course_breakdown'] = courses
        
        return analytics

# Global instance
reports_service = ReportsService()
