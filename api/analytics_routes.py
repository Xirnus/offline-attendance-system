"""
Analytics Routes Module for Offline Attendance System

This module contains all analytics and reporting endpoints for generating
statistics, trends, and insights about attendance patterns.

Key Analytics Endpoints:
- /api/analytics/overview - Overall system statistics and metrics
- /api/analytics/trends - Attendance trends over time (weekly/monthly/daily)
- /api/analytics/late-arrivals - Late arrival statistics and patterns
- /api/analytics/courses - Course-wise attendance comparison
- /api/analytics/weekly-patterns - Weekly attendance patterns by day
- /api/analytics/top-performers - Top performing students ranking
- /api/analytics/issues - Attendance issues and alerts detection
- /api/reports/analytics - Comprehensive analytics data
- /api/reports/preview - Preview report data without file generation

Analytics Features:
- Real-time attendance statistics
- Trend analysis and pattern recognition
- Course performance comparisons
- Student ranking and performance tracking
- Issue detection and alerting
- Data visualization support
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from database.operations import get_all_students, get_all_data, get_students_with_attendance_data
from services.reports import reports_service

# Create the analytics routes blueprint
analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/api/analytics/overview')
def analytics_overview():
    """Get overview analytics statistics"""
    try:
        students = get_all_students()
        attendances = get_all_data('class_attendees', limit=10000)  # Get all attendance records
        sessions = get_all_data('attendance_sessions', limit=1000)  # Get all sessions
        
        # Calculate metrics
        total_students = len(students)
        total_sessions = len(sessions)
        total_checkins = len(attendances)
        
        # Calculate average attendance
        avg_attendance = 0
        if total_students > 0:
            present_students = len([s for s in students if s.get('status') == 'present'])
            avg_attendance = (present_students / total_students) * 100
        
        # Calculate weekly trend (simplified)
        weekly_trend = 0  # This could be calculated based on historical data
        
        # Count active courses
        courses = set(s.get('course', 'Unknown') for s in students)
        active_courses = len(courses) if courses else 0
        
        return jsonify({
            'total_students': total_students,
            'avg_attendance': avg_attendance,
            'active_courses': active_courses,
            'weekly_trend': weekly_trend,
            'total_sessions': total_sessions,
            'total_checkins': total_checkins
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/trends')
def analytics_trends():
    """Get attendance trends data"""
    try:
        period = request.args.get('period', 'weekly')
        
        # Mock data for now - in production, this would query historical data
        if period == 'weekly':
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4']
            values = [75.2, 80.1, 78.5, 85.3]
        elif period == 'monthly':
            labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            values = [82.1, 78.9, 85.2, 79.8, 88.1, 84.5]
        else:  # daily
            labels = ['Day ' + str(i) for i in range(1, 31)]
            values = [85 + (i % 10) - 5 for i in range(30)]
        
        return jsonify({
            'labels': labels,
            'values': values
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/late-arrivals')
def analytics_late_arrivals():
    """Get late arrival statistics"""
    try:
        # Mock data - in production, this would analyze actual check-in times
        return jsonify({
            'late_today': 8,
            'avg_late_time': 12,
            'chronic_late': 3,
            'late_distribution': [25, 15, 8, 3]  # 0-5, 5-15, 15-30, 30+ minutes
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/courses')
def analytics_courses():
    """Get course comparison data"""
    try:
        students = get_all_students()
        course_stats = {}
        
        # Calculate course statistics
        for student in students:
            course = student.get('course', 'Unknown')
            if course not in course_stats:
                course_stats[course] = {
                    'students': 0,
                    'present': 0,
                    'name': course
                }
            
            course_stats[course]['students'] += 1
            if student.get('status') == 'present':
                course_stats[course]['present'] += 1
        
        # Prepare data for charts
        labels = []
        values = []
        details = []
        
        for course, stats in course_stats.items():
            labels.append(course)
            values.append(stats['students'])
            
            avg_attendance = 0
            if stats['students'] > 0:
                avg_attendance = (stats['present'] / stats['students']) * 100
            
            details.append({
                'name': course,
                'students': stats['students'],
                'avg_attendance': avg_attendance
            })
        
        return jsonify({
            'labels': labels,
            'values': values,
            'details': details
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/weekly-patterns')
def analytics_weekly_patterns():
    """Get weekly attendance patterns"""
    try:
        # Mock data - in production, this would analyze attendance by day of week
        values = [85.2, 88.1, 82.5, 90.3, 78.2, 45.8, 30.1]  # Mon-Sun
        
        return jsonify({
            'values': values
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/top-performers')
def analytics_top_performers():
    """Get top performing students"""
    try:
        students = get_all_students()
        performers = []
        
        # Calculate attendance rates and create rankings
        for student in students:
            # Mock calculation - in production, use actual attendance history
            attendance_rate = 85 + (hash(student.get('student_id', '')) % 15)  # Mock rate 85-100%
            
            performers.append({
                'name': student.get('name', 'Unknown'),
                'course': student.get('course', 'Unknown'),
                'attendance_rate': attendance_rate,
                'trend': 'up' if attendance_rate > 90 else 'neutral' if attendance_rate > 80 else 'down'
            })
        
        # Sort by attendance rate and add rank
        performers.sort(key=lambda x: x['attendance_rate'], reverse=True)
        for i, performer in enumerate(performers[:10]):  # Top 10
            performer['rank'] = i + 1
        
        return jsonify({
            'performers': performers[:10]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/issues')
def analytics_issues():
    """Get attendance issues and alerts"""
    try:
        students = get_all_students()
        issues = []
        
        # Identify students with potential issues
        for student in students:
            # Mock issue detection - in production, analyze actual patterns
            if student.get('status') != 'present':
                issues.append({
                    'student': student.get('name', 'Unknown'),
                    'course': student.get('course', 'Unknown'),
                    'issue': 'Absent Today',
                    'severity': 'Medium',
                    'last_seen': student.get('last_check_in', 'Unknown')
                })
        
        # Add some mock chronic issues
        if len(issues) == 0:
            issues = [
                {
                    'student': 'Sample Student',
                    'course': 'Computer Science',
                    'issue': 'No Recent Issues',
                    'severity': 'Low',
                    'last_seen': 'Today'
                }
            ]
        
        return jsonify({
            'issues': issues[:20]  # Limit to 20 issues
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/reports/analytics')
def get_analytics():
    """Get comprehensive attendance analytics"""
    try:
        analytics = reports_service.get_attendance_analytics()
        return jsonify(analytics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/reports/preview')
def preview_report():
    """Preview report data without generating file"""
    try:
        report_type = request.args.get('type', 'summary')
        
        if report_type == 'analytics':
            data = reports_service.get_attendance_analytics()
        else:
            # Return basic preview data
            students_data = get_students_with_attendance_data()
            attendance_data = get_all_data('class_attendees')
            
            data = {
                'summary': {
                    'total_students': len(students_data),
                    'total_checkins': len(attendance_data),
                    'generated_at': datetime.utcnow().isoformat()
                },
                'recent_attendance': attendance_data[-10:] if attendance_data else [],
                'student_count_by_course': {}
            }
            
            # Group students by course
            for student in students_data:
                course = student.get('course', 'Unknown')
                if course not in data['student_count_by_course']:
                    data['student_count_by_course'][course] = 0
                data['student_count_by_course'][course] += 1
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500