#!/usr/bin/env python3
"""
Test Data Generator for Analytics Dashboard
Generates 1 month of realistic attendance data for testing analytics functionality
"""

import sqlite3
import random
import json
from datetime import datetime, timedelta
from database.operations import get_db_connection
import hashlib

def generate_test_students():
    """Generate test student data"""
    students = [
        {"student_id": "2021-001", "name": "John Doe", "course": "Computer Science", "year": 3},
        {"student_id": "2021-002", "name": "Jane Smith", "course": "Computer Science", "year": 3},
        {"student_id": "2021-003", "name": "Bob Johnson", "course": "Mathematics", "year": 2},
        {"student_id": "2021-004", "name": "Alice Brown", "course": "Mathematics", "year": 2},
        {"student_id": "2021-005", "name": "Charlie Wilson", "course": "Physics", "year": 4},
        {"student_id": "2021-006", "name": "Diana Davis", "course": "Physics", "year": 4},
        {"student_id": "2021-007", "name": "Eve Anderson", "course": "Chemistry", "year": 1},
        {"student_id": "2021-008", "name": "Frank Miller", "course": "Chemistry", "year": 1},
        {"student_id": "2021-009", "name": "Grace Taylor", "course": "Computer Science", "year": 2},
        {"student_id": "2021-010", "name": "Henry Clark", "course": "Computer Science", "year": 2},
        {"student_id": "2021-011", "name": "Ivy Garcia", "course": "Mathematics", "year": 3},
        {"student_id": "2021-012", "name": "Jack Rodriguez", "course": "Mathematics", "year": 3},
        {"student_id": "2021-013", "name": "Kate Martinez", "course": "Physics", "year": 1},
        {"student_id": "2021-014", "name": "Leo Thompson", "course": "Physics", "year": 1},
        {"student_id": "2021-015", "name": "Mia White", "course": "Chemistry", "year": 4},
        {"student_id": "2021-016", "name": "Noah Lee", "course": "Chemistry", "year": 4},
        {"student_id": "2021-017", "name": "Olivia Hall", "course": "Computer Science", "year": 1},
        {"student_id": "2021-018", "name": "Paul Young", "course": "Computer Science", "year": 1},
        {"student_id": "2021-019", "name": "Quinn King", "course": "Mathematics", "year": 4},
        {"student_id": "2021-020", "name": "Rachel Scott", "course": "Mathematics", "year": 4},
    ]
    return students

def generate_device_fingerprint():
    """Generate a realistic device fingerprint"""
    device_types = ["Desktop", "Mobile", "Tablet", "Laptop"]
    browsers = ["Chrome", "Firefox", "Safari", "Edge"]
    platforms = ["Windows", "macOS", "iOS", "Android", "Linux"]
    
    device_info = {
        "device_type": random.choice(device_types),
        "browser": random.choice(browsers),
        "platform": random.choice(platforms),
        "screen_resolution": random.choice(["1920x1080", "1366x768", "414x896", "768x1024"]),
        "user_agent": f"Mozilla/5.0 ({random.choice(platforms)}) Test Browser",
        "timezone": random.choice(["UTC+8", "UTC-5", "UTC+0", "UTC+1"]),
        "language": random.choice(["en-US", "en-GB", "fr-FR", "es-ES"])
    }
    
    # Create a hash from device info
    device_string = json.dumps(device_info, sort_keys=True)
    fingerprint_hash = hashlib.sha256(device_string.encode()).hexdigest()
    
    return fingerprint_hash, device_info

def generate_attendance_data(students, start_date, num_days=30):
    """Generate realistic attendance data for given period"""
    attendance_records = []
    session_records = []
    denied_attempts = []
    device_fingerprints = {}
    
    # Student attendance patterns (some students are more reliable than others)
    student_patterns = {}
    for student in students:
        # Assign attendance probability (70-95% for good students, 40-70% for poor students)
        if student["student_id"] in ["2021-007", "2021-012", "2021-015"]:  # Poor attendance
            student_patterns[student["student_id"]] = {
                "base_prob": 0.55,  # 55% base attendance
                "late_prob": 0.25,   # 25% chance of being late
                "pattern": "poor"
            }
        elif student["student_id"] in ["2021-003", "2021-008", "2021-014", "2021-018"]:  # Average attendance
            student_patterns[student["student_id"]] = {
                "base_prob": 0.75,  # 75% base attendance
                "late_prob": 0.15,   # 15% chance of being late
                "pattern": "average"
            }
        else:  # Good attendance
            student_patterns[student["student_id"]] = {
                "base_prob": 0.90,  # 90% base attendance
                "late_prob": 0.05,   # 5% chance of being late
                "pattern": "good"
            }
    
    session_id_counter = 1
    attendance_id_counter = 1
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        
        # Skip weekends (Saturday=5, Sunday=6)
        if current_date.weekday() >= 5:
            continue
        
        # Create 2-3 sessions per day
        sessions_per_day = random.choice([2, 3])
        
        for session_num in range(sessions_per_day):
            # Session times
            if session_num == 0:
                session_time = current_date.replace(hour=8, minute=0)  # Morning session
            elif session_num == 1:
                session_time = current_date.replace(hour=13, minute=0)  # Afternoon session
            else:
                session_time = current_date.replace(hour=15, minute=30)  # Late afternoon session
            
            session_name = f"Session {current_date.strftime('%Y-%m-%d')} - {session_num + 1}"
            session_token = hashlib.md5(f"{session_name}{session_time}".encode()).hexdigest()[:16]
            
            # Create session record
            session_record = {
                "session_name": session_name,
                "start_time": session_time.isoformat(),
                "end_time": (session_time + timedelta(hours=2)).isoformat(),
                "is_active": False,  # Completed sessions
                "created_at": session_time.isoformat()
            }
            session_records.append(session_record)
            
            # Generate attendance for each student
            for student in students:
                student_id = student["student_id"]
                pattern = student_patterns[student_id]
                
                # Check if student attends this session
                attendance_roll = random.random()
                
                # Day of week effect (Friday has lower attendance)
                day_penalty = 0.1 if current_date.weekday() == 4 else 0
                adjusted_prob = pattern["base_prob"] - day_penalty
                
                if attendance_roll < adjusted_prob:
                    # Student attends - generate attendance record
                    fingerprint_hash, device_info = generate_device_fingerprint()
                    
                    # Store device fingerprint if new
                    if fingerprint_hash not in device_fingerprints:
                        device_fingerprints[fingerprint_hash] = {
                            "fingerprint_hash": fingerprint_hash,
                            "device_info": json.dumps(device_info),
                            "first_seen": session_time.isoformat(),
                            "last_seen": session_time.isoformat(),
                            "usage_count": 1
                        }
                    else:
                        device_fingerprints[fingerprint_hash]["last_seen"] = session_time.isoformat()
                        device_fingerprints[fingerprint_hash]["usage_count"] += 1
                    
                    # Check if late
                    late_roll = random.random()
                    if late_roll < pattern["late_prob"]:
                        # Late arrival (5-30 minutes)
                        late_minutes = random.randint(5, 30)
                        checkin_time = session_time + timedelta(minutes=late_minutes)
                    else:
                        # On time (within 5 minutes)
                        checkin_time = session_time + timedelta(minutes=random.randint(0, 5))
                    
                    attendance_record = {
                        "student_id": student_id,
                        "token": session_token,
                        "fingerprint_hash": fingerprint_hash,
                        "timestamp": checkin_time.timestamp(),
                        "created_at": checkin_time.isoformat(),
                        "name": student["name"],
                        "course": student["course"],
                        "year": str(student["year"]),
                        "device_info": json.dumps(device_info),
                        "device_signature": json.dumps(device_info),
                        "session_counter": session_id_counter  # Track session for later reference
                    }
                    attendance_records.append(attendance_record)
                
                else:
                    # Student doesn't attend - possibly generate a denied attempt
                    denied_roll = random.random()
                    if denied_roll < 0.1:  # 10% chance of denied attempt
                        denied_reasons = [
                            "Invalid student ID",
                            "Token expired",
                            "Device blocked",
                            "Session not active"
                        ]
                        
                        denied_record = {
                            "student_id": student_id,
                            "reason": random.choice(denied_reasons),
                            "attempt_time": (session_time + timedelta(minutes=random.randint(-5, 60))).isoformat(),
                            "token": session_token,
                            "name": student["name"],
                            "timestamp": (session_time + timedelta(minutes=random.randint(-5, 60))).timestamp()
                        }
                        denied_attempts.append(denied_record)
            
            session_id_counter += 1
    
    return attendance_records, session_records, denied_attempts, list(device_fingerprints.values())

def clear_existing_data():
    """Clear existing test data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM attendances")
        cursor.execute("DELETE FROM attendance_sessions")
        cursor.execute("DELETE FROM denied_attempts")
        cursor.execute("DELETE FROM device_fingerprints")
        cursor.execute("DELETE FROM students")
        conn.commit()
        print("✅ Cleared existing data")
    except Exception as e:
        print(f"❌ Error clearing data: {e}")
        conn.rollback()
    finally:
        conn.close()

def insert_test_data():
    """Insert all test data into database"""
    print("🔄 Generating test data for analytics...")
    
    # Clear existing data
    clear_existing_data()
    
    # Generate test data
    students = generate_test_students()
    start_date = datetime.now() - timedelta(days=30)  # Start 30 days ago
    
    attendance_records, session_records, denied_attempts, device_fingerprints = generate_attendance_data(
        students, start_date, num_days=30
    )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert students
        print(f"📚 Inserting {len(students)} students...")
        for student in students:
            cursor.execute("""
                INSERT INTO students (student_id, name, course, year, status, created_at)
                VALUES (?, ?, ?, ?, 'active', ?)
            """, (
                student["student_id"],
                student["name"],
                student["course"],
                student["year"],
                datetime.now().isoformat()
            ))
        
        # Insert sessions and keep track of session IDs
        print(f"📅 Inserting {len(session_records)} sessions...")
        session_id_map = {}  # Map session_counter to actual database IDs
        
        for i, session in enumerate(session_records):
            cursor.execute("""
                INSERT INTO attendance_sessions (session_name, start_time, end_time, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["session_name"],
                session["start_time"],
                session["end_time"],
                session["is_active"],
                session["created_at"]
            ))
            # Get the actual session ID from database
            actual_session_id = cursor.lastrowid
            session_id_map[i + 1] = actual_session_id  # Map counter to actual ID
        
        # Insert attendance records
        print(f"✅ Inserting {len(attendance_records)} attendance records...")
        for record in attendance_records:
            # Get the actual session ID from the mapping
            actual_session_id = session_id_map.get(record["session_counter"], None)
            
            cursor.execute("""
                INSERT INTO attendances (student_id, token, fingerprint_hash, timestamp, created_at, name, course, year, device_info, device_signature, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["student_id"],
                record["token"],
                record["fingerprint_hash"],
                record["timestamp"],
                record["created_at"],
                record["name"],
                record["course"],
                record["year"],
                record["device_info"],
                record["device_signature"],
                actual_session_id
            ))
        
        # Insert denied attempts
        print(f"❌ Inserting {len(denied_attempts)} denied attempts...")
        for attempt in denied_attempts:
            cursor.execute("""
                INSERT INTO denied_attempts (token, timestamp, created_at, reason, name)
                VALUES (?, ?, ?, ?, ?)
            """, (
                attempt["token"],
                attempt["timestamp"],
                attempt["attempt_time"],
                attempt["reason"],
                attempt["name"]
            ))
        
        # Insert device fingerprints
        print(f"📱 Inserting {len(device_fingerprints)} device fingerprints...")
        for device in device_fingerprints:
            cursor.execute("""
                INSERT INTO device_fingerprints (fingerprint_hash, device_info, first_seen, last_seen, usage_count)
                VALUES (?, ?, ?, ?, ?)
            """, (
                device["fingerprint_hash"],
                device["device_info"],
                device["first_seen"],
                device["last_seen"],
                device["usage_count"]
            ))
        
        conn.commit()
        print("🎉 Successfully inserted all test data!")
        
        # Print summary
        print("\n📊 Test Data Summary:")
        print(f"  • Students: {len(students)}")
        print(f"  • Sessions: {len(session_records)}")
        print(f"  • Attendance Records: {len(attendance_records)}")
        print(f"  • Denied Attempts: {len(denied_attempts)}")
        print(f"  • Unique Devices: {len(device_fingerprints)}")
        
        # Calculate some stats
        total_possible_attendance = len(students) * len(session_records)
        actual_attendance = len(attendance_records)
        overall_rate = (actual_attendance / total_possible_attendance) * 100
        print(f"  • Overall Attendance Rate: {overall_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def print_analytics_preview():
    """Print a preview of analytics data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Course breakdown
        cursor.execute("""
            SELECT course, COUNT(*) as student_count
            FROM students 
            GROUP BY course
        """)
        courses = cursor.fetchall()
        
        print("\n📈 Analytics Preview:")
        print("Course Breakdown:")
        for course in courses:
            course_name, total = course
            print(f"  • {course_name}: {total} students")
        
        # Weekly patterns from attendance records
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM attendances
            GROUP BY DATE(created_at)
            ORDER BY date
            LIMIT 7
        """)
        daily_data = cursor.fetchall()
        
        print("\nDaily Attendance (last 7 days):")
        for date, count in daily_data:
            print(f"  • {date}: {count} check-ins")
        
        # Total statistics
        cursor.execute("SELECT COUNT(*) FROM attendances")
        total_attendances = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM denied_attempts")
        total_denied = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT fingerprint_hash) FROM device_fingerprints")
        unique_devices = cursor.fetchone()[0]
        
        print(f"\nOverall Statistics:")
        print(f"  • Total Successful Check-ins: {total_attendances}")
        print(f"  • Total Failed Attempts: {total_denied}")
        print(f"  • Unique Devices: {unique_devices}")
        
    except Exception as e:
        print(f"❌ Error getting analytics preview: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 Analytics Test Data Generator")
    print("================================")
    
    try:
        insert_test_data()
        print_analytics_preview()
        
        print("\n✅ Test data generation complete!")
        print("🌐 You can now test the analytics at: http://127.0.0.1:5000/analytics")
        
    except Exception as e:
        print(f"❌ Error generating test data: {e}")
        import traceback
        traceback.print_exc()
