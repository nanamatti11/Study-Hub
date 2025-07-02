# Import required modules
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

# Initialize the database and create required tables
def init_db():
    # Remove existing database file if it exists
    if os.path.exists('study_hub.db'):
        os.remove('study_hub.db')
        
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()

    # Create students table with required fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create instructors table with required fields
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instructors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        subject TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create results table to store student grades
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        marks INTEGER NOT NULL,
        grade TEXT NOT NULL,
        credits INTEGER NOT NULL,
        semester TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id)
    )
    ''')

    # Test users data
    test_students = [
        ('john.doe', 'John Doe', 'john.doe@example.com', 'Student@123'),
        ('emma.smith', 'Emma Smith', 'emma.smith@example.com', 'Emma@456'),
        ('michael.brown', 'Michael Brown', 'michael.brown@example.com', 'Mike@789'),
        ('sarah.wilson', 'Sarah Wilson', 'sarah.wilson@example.com', 'Sarah@321')
    ]

    test_instructors = [
        ('prof.johnson', 'Professor Johnson', 'prof.johnson@example.com', 'Prof@123', 'Mathematics'),
        ('dr.smith', 'Dr. Smith', 'dr.smith@example.com', 'Dr@456', 'Physics'),
        ('ms.davis', 'Ms. Davis', 'ms.davis@example.com', 'Ms@789', 'Computer Science'),
        ('mr.wilson', 'Mr. Wilson', 'mr.wilson@example.com', 'Mr@321', 'English')
    ]

    # Add test students
    for username, fullname, email, password in test_students:
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO students (username, fullname, email, password) 
            VALUES (?, ?, ?, ?)
        ''', (username, fullname, email, hashed_password))

    # Add test instructors
    for username, fullname, email, password, subject in test_instructors:
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO instructors (username, fullname, email, password, subject) 
            VALUES (?, ?, ?, ?, ?)
        ''', (username, fullname, email, hashed_password, subject))

    conn.commit()
    conn.close()
    
    print("Database initialized successfully!") 

# Verify student login credentials
def verify_student(username, password):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        print(f"Attempting to verify student: {username}")
        
        # First try to find by username
        cursor.execute('SELECT password, username, email FROM students WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        # If not found by username, try by email
        if not result:
            print(f"User not found by username, trying email: {username}")
            cursor.execute('SELECT password, username, email FROM students WHERE email = ?', (username,))
            result = cursor.fetchone()
        
        if result:
            stored_password = result[0]
            found_username = result[1]
            found_email = result[2]
            print(f"Found user: {found_username} ({found_email})")
            
            # Verify password hash
            if check_password_hash(stored_password, password):
                print("Password verified successfully")
                return True
            else:
                print("Password verification failed")
                return False
                
        print(f"No user found with username/email: {username}")
        return False
    except Exception as e:
        print(f"Error verifying student: {str(e)}")
        return False
    finally:
        conn.close()

# Verify instructor login credentials
def verify_instructor(username, password):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        print(f"Attempting to verify instructor: {username}")
        
        # First try to find by username
        cursor.execute('SELECT password, username, email FROM instructors WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        # If not found by username, try by email
        if not result:
            print(f"User not found by username, trying email: {username}")
            cursor.execute('SELECT password, username, email FROM instructors WHERE email = ?', (username,))
            result = cursor.fetchone()
        
        if result:
            stored_password = result[0]
            found_username = result[1]
            found_email = result[2]
            print(f"Found instructor: {found_username} ({found_email})")
            
            # Verify password hash
            if check_password_hash(stored_password, password):
                print("Password verified successfully")
                return True
            else:
                print("Password verification failed")
                return False
                
        print(f"No instructor found with username/email: {username}")
        return False
    except Exception as e:
        print(f"Error verifying instructor: {str(e)}")
        return False
    finally:
        conn.close() 