# Import required modules
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize the database and create required tables
def init_db():
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

    # Add test users if they don't exist
    test_student = ('student1', 'password123')
    test_instructor = ('instructor1', 'password123')

    # Check if test student exists and add if not
    cursor.execute('SELECT username FROM students WHERE username = ?', (test_student[0],))
    if not cursor.fetchone():
        hashed_password = generate_password_hash(test_student[1])
        cursor.execute('INSERT INTO students (username, password) VALUES (?, ?)',
                      (test_student[0], hashed_password))

    # Check if test instructor exists and add if not
    cursor.execute('SELECT username FROM instructors WHERE username = ?', (test_instructor[0],))
    if not cursor.fetchone():
        hashed_password = generate_password_hash(test_instructor[1])
        cursor.execute('INSERT INTO instructors (username, password) VALUES (?, ?)',
                      (test_instructor[0], hashed_password))

    conn.commit()
    conn.close()

# Add a new student to the database
def add_student(username, password, fullname=None, email=None):
    if not all([username, password, fullname, email]):
        return False
        
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        # Check if username or email already exists
        cursor.execute('SELECT username, email FROM students WHERE username = ? OR email = ?', 
                      (username, email))
        if cursor.fetchone():
            return False

        # Hash password and insert new student
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO students (username, fullname, email, password) 
            VALUES (?, ?, ?, ?)
        ''', (username, fullname, email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error adding student: {str(e)}")
        return False
    finally:
        conn.close()

# Add a new instructor to the database
def add_instructor(username, password, fullname=None, email=None, subject=None):
    if not all([username, password, fullname, email, subject]):
        return False
        
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        # Check if username or email already exists
        cursor.execute('SELECT username, email FROM instructors WHERE username = ? OR email = ?', 
                      (username, email))
        if cursor.fetchone():
            return False

        # Hash password and insert new instructor
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO instructors (username, fullname, email, password, subject) 
            VALUES (?, ?, ?, ?, ?)
        ''', (username, fullname, email, hashed_password, subject))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Error adding instructor: {str(e)}")
        return False
    finally:
        conn.close()

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
        # First try to find by username
        cursor.execute('SELECT password FROM instructors WHERE username = ?', (username,))
        result = cursor.fetchone()
        
        # If not found by username, try by email
        if not result:
            cursor.execute('SELECT password FROM instructors WHERE email = ?', (username,))
            result = cursor.fetchone()
        
        if result:
            return check_password_hash(result[0], password)
        return False
    except Exception as e:
        print(f"Error verifying instructor: {str(e)}")
        return False
    finally:
        conn.close()

# Search for students by username or ID
def search_students(search_term):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        # Search by username or ID
        cursor.execute('''
            SELECT id, username 
            FROM students 
            WHERE username LIKE ? OR id LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%'))
        
        results = cursor.fetchall()
        return [{'id': row[0], 'username': row[1]} for row in results]
    finally:
        conn.close()

# Add a new result for a student
def add_result(student_id, subject, marks, grade, credits, semester, academic_year):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO results (student_id, subject, marks, grade, credits, semester, academic_year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, subject, marks, grade, credits, semester, academic_year))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding result: {str(e)}")
        return False
    finally:
        conn.close()

# Get student information by username
def get_student_by_username(username):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username FROM students WHERE username = ?', (username,))
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'username': result[1]}
        return None
    finally:
        conn.close()

# Get student results for a specific year and semester
def get_student_results(student_id, year, semester):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT subject, marks, grade, credits
            FROM results
            WHERE student_id = ? AND academic_year = ? AND semester = ?
            ORDER BY subject
        ''', (student_id, year, semester))
        
        results = cursor.fetchall()
        return [{
            'subject': row[0],
            'marks': row[1],
            'grade': row[2],
            'credits': row[3]
        } for row in results]
    finally:
        conn.close()

# Initialize the database when this module is imported
init_db()