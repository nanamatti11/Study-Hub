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

    # Create messages table for chat functionality
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create future_tests table to store upcoming tests
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS future_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        test_date DATE NOT NULL,
        test_time TIME NOT NULL,
        duration TEXT NOT NULL,
        location TEXT,
        test_type TEXT,
        description TEXT,
        instructor_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instructor_id) REFERENCES instructors (id)
    )
    ''')

    # Create evaluations table to store student feedback
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        instructor_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        teaching_quality INTEGER NOT NULL CHECK (teaching_quality >= 1 AND teaching_quality <= 5),
        course_content INTEGER NOT NULL CHECK (course_content >= 1 AND course_content <= 5),
        communication INTEGER NOT NULL CHECK (communication >= 1 AND communication <= 5),
        overall_rating INTEGER NOT NULL CHECK (overall_rating >= 1 AND overall_rating <= 5),
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (instructor_id) REFERENCES instructors (id),
        UNIQUE(student_id, instructor_id, subject)
    )
    ''')

    # Add test users if they don't exist
    test_student = ('student1', 'password123', 'Test Student', 'student1@example.com')
    test_instructor = ('instructor1', 'password123', 'Test Instructor', 'instructor1@example.com', 'Mathematics')

    # Check if test student exists and add if not
    cursor.execute('SELECT username FROM students WHERE username = ?', (test_student[0],))
    if not cursor.fetchone():
        hashed_password = generate_password_hash(test_student[1])
        cursor.execute('INSERT INTO students (username, password, fullname, email) VALUES (?, ?, ?, ?)',
                      (test_student[0], hashed_password, test_student[2], test_student[3]))

    # Check if test instructor exists and add if not
    cursor.execute('SELECT username FROM instructors WHERE username = ?', (test_instructor[0],))
    if not cursor.fetchone():
        hashed_password = generate_password_hash(test_instructor[1])
        cursor.execute('INSERT INTO instructors (username, password, fullname, email, subject) VALUES (?, ?, ?, ?, ?)',
                      (test_instructor[0], hashed_password, test_instructor[2], test_instructor[3], test_instructor[4]))

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

# Search for students by username, full name (exact match), or ID
def search_students(search_term):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        # Search by username, full name (exact match), or ID
        cursor.execute('''
            SELECT id, username, fullname, email
            FROM students
            WHERE username LIKE ? OR id LIKE ? OR fullname = ?
        ''', (f'%{search_term}%', f'%{search_term}%', search_term))
        
        results = cursor.fetchall()
        return [{'id': row[0], 'username': row[1], 'fullname': row[2], 'email': row[3]} for row in results]
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
        if not result:
            cursor.execute('SELECT id, username FROM students WHERE email = ?', (username,))
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

def send_message(sender, receiver, message):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)
        ''', (sender, receiver, message))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False
    finally:
        conn.close()

def get_chat_history(user1, user2, limit=100):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT sender, receiver, message, timestamp FROM messages
            WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (user1, user2, user2, user1, limit))
        messages = cursor.fetchall()
        return [
            {
                'sender': row[0],
                'receiver': row[1],
                'message': row[2],
                'timestamp': row[3]
            } for row in messages
        ]
    except Exception as e:
        print(f"Error fetching chat history: {str(e)}")
        return []
    finally:
        conn.close()


# Get instructor by username
def get_instructor_by_username(username):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username, fullname, email, subject FROM instructors WHERE username = ? OR email = ?', (username, username))
        result = cursor.fetchone()
        if result:
            return {'id': result[0], 'username': result[1], 'fullname': result[2], 'email': result[3], 'subject': result[4]}
        return None
    except Exception as e:
        print(f"Error getting instructor: {str(e)}")
        return None
    finally:
        conn.close()

# Add a future test
def add_future_test(subject, test_date, test_time, duration, location, test_type, description, instructor_id):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO future_tests (subject, test_date, test_time, duration, location, test_type, description, instructor_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (subject, test_date, test_time, duration, location, test_type, description, instructor_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding future test: {str(e)}")
        return False
    finally:
        conn.close()

# Get all future tests
def get_all_future_tests():
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT ft.id, ft.subject, ft.test_date, ft.test_time, ft.duration, 
                   ft.location, ft.test_type, ft.description, i.fullname as instructor_name
            FROM future_tests ft
            JOIN instructors i ON ft.instructor_id = i.id
            ORDER BY ft.test_date ASC, ft.test_time ASC
        ''')
        results = cursor.fetchall()
        return [{
            'id': row[0], 'subject': row[1], 'test_date': row[2], 'test_time': row[3],
            'duration': row[4], 'location': row[5], 'test_type': row[6], 
            'description': row[7], 'instructor_name': row[8]
        } for row in results]
    except Exception as e:
        print(f"Error getting future tests: {str(e)}")
        return []
    finally:
        conn.close()

# Get future tests by instructor
def get_future_tests_by_instructor(instructor_id):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, subject, test_date, test_time, duration, location, test_type, description
            FROM future_tests 
            WHERE instructor_id = ?
            ORDER BY test_date ASC, test_time ASC
        ''', (instructor_id,))
        results = cursor.fetchall()
        return [{
            'id': row[0], 'subject': row[1], 'test_date': row[2], 'test_time': row[3],
            'duration': row[4], 'location': row[5], 'test_type': row[6], 'description': row[7]
        } for row in results]
    except Exception as e:
        print(f"Error getting instructor's future tests: {str(e)}")
        return []
    finally:
        conn.close()

# Update a future test
def update_future_test(test_id, subject, test_date, test_time, duration, location, test_type, description):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE future_tests 
            SET subject = ?, test_date = ?, test_time = ?, duration = ?, 
                location = ?, test_type = ?, description = ?
            WHERE id = ?
        ''', (subject, test_date, test_time, duration, location, test_type, description, test_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error updating future test: {str(e)}")
        return False
    finally:
        conn.close()

# Delete a future test
def delete_future_test(test_id):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM future_tests WHERE id = ?', (test_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting future test: {str(e)}")
        return False
    finally:
        conn.close()

# Add an evaluation
def add_evaluation(student_id, instructor_id, subject, teaching_quality, course_content, communication, overall_rating, comments):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO evaluations 
            (student_id, instructor_id, subject, teaching_quality, course_content, communication, overall_rating, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, instructor_id, subject, teaching_quality, course_content, communication, overall_rating, comments))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding evaluation: {str(e)}")
        return False
    finally:
        conn.close()

# Get evaluations for an instructor
def get_instructor_evaluations(instructor_id):
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT e.id, s.fullname as student_name, e.subject, e.teaching_quality, 
                   e.course_content, e.communication, e.overall_rating, e.comments, e.created_at
            FROM evaluations e
            JOIN students s ON e.student_id = s.id
            WHERE e.instructor_id = ?
            ORDER BY e.created_at DESC
        ''', (instructor_id,))
        results = cursor.fetchall()
        return [{
            'id': row[0], 'student_name': row[1], 'subject': row[2], 'teaching_quality': row[3],
            'course_content': row[4], 'communication': row[5], 'overall_rating': row[6], 
            'comments': row[7], 'created_at': row[8]
        } for row in results]
    except Exception as e:
        print(f"Error getting instructor evaluations: {str(e)}")
        return []
    finally:
        conn.close()

# Get all instructors for evaluation selection
def get_all_instructors():
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, username, fullname, subject FROM instructors ORDER BY fullname')
        results = cursor.fetchall()
        return [{'id': row[0], 'username': row[1], 'fullname': row[2], 'subject': row[3]} for row in results]
    except Exception as e:
        print(f"Error getting instructors: {str(e)}")
        return []
    finally:
        conn.close()

# Initialize the database when this module is imported
init_db()