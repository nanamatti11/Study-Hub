import os
import re
import io
import logging
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse, parse_qs

from flask import (
    Flask, request, jsonify, render_template, session, redirect, send_file, url_for, flash
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt
import requests
import gdown

from database import (
    add_student, add_instructor, verify_student, verify_instructor, 
    search_students, add_result, get_student_by_username, get_student_results,
    init_db, send_message, get_chat_history, get_instructor_by_username,
    add_future_test, get_all_future_tests, get_future_tests_by_instructor,
    update_future_test, delete_future_test, add_evaluation, get_instructor_evaluations,
    get_all_instructors
)

# Configure logging for debugging and error tracking
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(__name__)
# Use a fixed secret key for session and JWT security
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure key in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_hub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']  # Use the same key for JWT
app.config['RESOURCES_FOLDER'] = os.path.join(app.static_folder, 'resources')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}

# Initialize SQLAlchemy with the app for database operations
db = SQLAlchemy()
db.init_app(app)

# Initialize the database with required tables
init_db()

# Decorator to protect routes that require authentication
def token_required(allowed_types=("instructor",)):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = request.cookies.get('studentToken') or request.cookies.get('instructorToken')

            if not token:
                return jsonify({'success': False, 'message': 'Token is missing'}), 401

            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                if data.get('type') not in allowed_types:
                    return jsonify({'success': False, 'message': 'Invalid token type'}), 401
                request.user = data
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': 'Invalid token'}), 401
            except Exception as e:
                logger.error(f"Token validation error: {str(e)}")
                return jsonify({'success': False, 'message': 'An error occurred during token validation'}), 500
        return decorated
    return decorator

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')



def download_fileresources():
    try:
        file_id = "17-onD-fMI7gKBQjtN8i1y2Skl_EqgDCN"
        url = f"https://drive.google.com/uc?id={file_id}"
        output_file = "downloaded_file.ext"

        gdown.download(url, output_file, quiet=False)
        print("Download completed.")
    except Exception as e:
        print(f"Download failed: {e}")

# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Increased length for hashed password
    user_type = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50))  # Only for teachers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'


# Helper function to validate email format
def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Helper function to validate password strength
def validate_password(password):
    # Password must be at least 8 characters long and contain at least one number
    return len(password) >= 8 and any(char.isdigit() for char in password)

# Route for new user page
@app.route('/new/user')
def new():
    return render_template('new.html')

# Route for user registration
@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get and validate form data
            fullname = request.form.get('fullname', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            user_type = request.form.get('user_type', '').strip()
            subject = request.form.get('subject', '').strip() if user_type == 'instructor' else None

            # Validation checks
            if not all([fullname, username, email, password, user_type]):
                logger.error(f"Missing fields: fullname={fullname}, username={username}, email={email}, password={'***' if password else ''}, user_type={user_type}")
                flash('All fields are required', 'error')
                return redirect(url_for('register'))

            if user_type not in ['instructor', 'student']:
                logger.error(f"Invalid user_type: {user_type}")
                flash('Invalid user type selected', 'error')
                return redirect(url_for('register'))

            if not validate_email(email):
                logger.error(f"Invalid email format: {email}")
                flash('Invalid email format', 'error')
                return redirect(url_for('register'))

            if not validate_password(password):
                logger.error(f"Password does not meet requirements: {password}")
                flash('Password must be at least 8 characters long and contain at least one number', 'error')
                return redirect(url_for('register'))

            if user_type == 'instructor' and not subject:
                logger.error(f"Missing subject for instructor registration")
                flash('Subject is required for instructors', 'error')
                return redirect(url_for('register'))

            # Add user to appropriate table based on user_type
            if user_type == 'student':
                success = add_student(
                    username=username,
                    password=password,
                    fullname=fullname,
                    email=email
                )
                logger.info(f"Tried to add student: username={username}, email={email}, success={success}")
            else:  # instructor
                success = add_instructor(
                    username=username,
                    password=password,
                    fullname=fullname,
                    email=email,
                    subject=subject
                )
                logger.info(f"Tried to add instructor: username={username}, email={email}, subject={subject}, success={success}")

            if success:
                flash('Registration successful!', 'success')
                return redirect(url_for('index'))
            else:
                logger.error(f"Registration failed for username={username}, email={email}")
                flash('Email or username already registered', 'error')
                return redirect(url_for('register'))

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

# Route for student dashboard
@app.route('/student/dashboard')
def student_dashboard():
    try:
        # Get the token from cookie or Authorization header
        token = request.cookies.get('studentToken')
        if not token:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token.split(' ')[1]
        
        if not token:
            return redirect('/')
            
        # Verify the token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Verify it's a student token
        if data.get('type') != 'student':
            return redirect('/')
            
        # Get student username from token
        username = data['user']
        
        # Render the student dashboard template
        return render_template('student_dashboard.html', username=username)
    except Exception as e:
        logger.error(f"Error accessing student dashboard: {str(e)}")
        return redirect('/')

# Route for student result checking
@app.route('/student/check-result')
def check_result():
    return render_template('check_result.html')

# Route for future tests page
@app.route('/student/future-tests')
def future_tests():
    return render_template('future_tests.html')

# Route for learning resources page
@app.route('/student/learning-resources')
def learning_resources():
    return render_template('learning_resources.html')

# Route for coding resources page
@app.route('/student/coding-resources')
def coding_resources():
    try:
        # Get token from cookie or Authorization header
        token = request.cookies.get('studentToken') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return redirect(url_for('index'))
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('type') != 'student':
                return redirect(url_for('index'))
        except jwt.InvalidTokenError:
            return redirect(url_for('index'))
        
        return render_template('coding_resources.html')
    except Exception as e:
        logger.error(f"Error in coding_resources route: {str(e)}")
        return redirect(url_for('index'))

# API endpoint for student login
@app.route('/api/student/login', methods=['POST'])
def student_login():
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received in login request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            logger.error("Missing credentials in login request")
            return jsonify({'success': False, 'message': 'Missing credentials'}), 400

        logger.info(f"Login attempt for user: {username}")

        # Check if user exists first
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, email, password FROM students WHERE username = ? OR email = ?', (username, username))
        user = cursor.fetchone()
        conn.close()

        if not user:
            logger.warning(f"Login attempt for non-existent user: {username}")
            return jsonify({'success': False, 'message': 'User not found'}), 401

        # Try both username and email
        if verify_student(username, password):
            logger.info(f"Successful login for user: {username}")
            token = jwt.encode({
                'user': username,
                'type': 'student',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            response = jsonify({
                'success': True, 
                'token': token, 
                'message': 'Login successful'
            })
            
            # Set the token in a cookie
            response.set_cookie(
                'studentToken',
                token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='Lax',
                max_age=86400  # 24 hours
            )
            
            return response
            
        logger.warning(f"Failed login attempt for username: {username}")
        return jsonify({'success': False, 'message': 'Invalid password'}), 401
        
    except Exception as e:
        logger.error(f"Error during student login: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

# API endpoint for getting student results
@app.route('/api/student/results')
def get_student_results_api():
    try:
        token = request.cookies.get('studentToken')
        if not token:
            token = request.headers.get('Authorization')
            if token and token.startswith('Bearer '):
                token = token.split(' ')[1]
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'student':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401
        username = data['user']
        year = request.args.get('year')
        semester = request.args.get('semester')
        if not year or not semester:
            return jsonify({'success': False, 'message': 'Year and semester are required'})
        student = get_student_by_username(username)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        # Fetch full name from the database
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('SELECT fullname FROM students WHERE username = ? OR email = ?', (username, username))
        row = cursor.fetchone()
        conn.close()
        full_name = row[0] if row else username
        results = get_student_results(student['id'], year, semester)
        return jsonify({
            'success': True,
            'results': results,
            'student_info': {
                'name': full_name,
                'id': student['id']
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        logger.error(f"Error getting student results: Invalid token")
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error getting student results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching results'}), 500

# API endpoint for getting future tests
@app.route('/api/student/future-tests')
@token_required(allowed_types=("student",))
def get_future_tests():
    try:
        tests = get_all_future_tests()
        # Format the data for frontend consumption
        formatted_tests = []
        for test in tests:
            formatted_tests.append({
                'id': test['id'],
                'subject': test['subject'],
                'date': test['test_date'],
                'time': test['test_time'],
                'duration': test['duration'],
                'location': test['location'],
                'test_type': test['test_type'],
                'description': test['description'],
                'instructor_name': test['instructor_name']
            })
        
        return jsonify({'success': True, 'tests': formatted_tests})
    except Exception as e:
        logger.error(f"Error getting future tests: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching future tests'}), 500

# API endpoint for getting learning resources
@app.route('/api/student/resources')
@token_required(allowed_types=("student",))
def get_learning_resources():
    # Mock learning resources data - Replace with actual database query
    resources = [
        {
            'title': 'Mathematics Formula Sheet',
            'description': 'Complete formula sheet for calculus and algebra',
            'link': 'https://example.com/math-formulas'
        },
        {
            'title': 'Physics Video Lectures',
            'description': 'Video lectures covering mechanics and thermodynamics',
            'link': 'https://example.com/physics-lectures'
        }
    ]
    
    return jsonify({'success': True, 'resources': resources})

# API endpoint for getting student info
@app.route('/api/student/info')
@token_required(allowed_types=("student",))
def get_student_info():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token.split(' ')[1]
    else:
        token = request.cookies.get('studentToken')
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    username = data['user']
    student = get_student_by_username(username)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    # Fetch full name and id from the database
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fullname, id FROM students WHERE username = ? OR email = ?', (username, username))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    student_info = {
        'name': row[0],
        'id': row[1],
        'username': username
    }
    return jsonify({'success': True, 'student_info': student_info})

# API endpoint for instructor login
@app.route('/api/instructor/login', methods=['POST'])
def instructor_login():
    try:
        data = request.get_json()
        print("Login data received:", data)  # DEBUG

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        print("Username:", username, "Password:", password)  # DEBUG
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Missing credentials'}), 400
        
        if verify_instructor(username, password):
            print("Login successful for:", username)  # DEBUG
            token = jwt.encode({
                'user': username,
                'type': 'instructor',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')
            
            response = jsonify({
                'success': True,
                'token': token,
                'message': 'Login successful'
            })
            
            response.set_cookie(
                'instructorToken',
                token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=86400
            )
            
            return response
        
        print("Login failed for:", username)  # DEBUG
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        logger.error(f"Error during instructor login: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

# API endpoint for student registration
@app.route('/api/student/register', methods=['POST'])
def student_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    fullname = data.get('fullname', username)  # Default to username if not provided
    email = data.get('email', f"{username}@example.com")  # Default email if not provided

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})

    if add_student(username, password, fullname, email):
        return jsonify({'success': True, 'message': 'Student registered successfully'})
    else:
        return jsonify({'success': False, 'message': 'Username already exists'})

# API endpoint for instructor registration
@app.route('/api/instructor/register', methods=['POST'])
def instructor_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})

    if add_instructor(username, password):
        return jsonify({'success': True, 'message': 'Instructor registered successfully'})
    else:
        return jsonify({'success': False, 'message': 'Username already exists'})

# Route for instructor dashboard
@app.route('/instructor/dashboard')
def instructor_dashboard():
    try:
        # Get the token from localStorage
        token = request.cookies.get('instructorToken')
        if not token:
            return redirect('/')
            
        # Verify the token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Verify it's an instructor token
        if data.get('type') != 'instructor':
            return redirect('/')
            
        # Get instructor username from token
        username = data['user']
        
        # Render the instructor dashboard template
        return render_template('instructor_dashboard.html', username=username)
    except Exception as e:
        logger.error(f"Error accessing instructor dashboard: {str(e)}")
        return redirect('/')

# Route for managing results
@app.route('/instructor/manage_results')
@token_required(allowed_types=("instructor",))
def manage_results():
    return render_template('manage_results.html')

# Route for searching students
@app.route('/instructor/search_student')
@token_required(allowed_types=("instructor",))
def search_student():
    return render_template('search_student.html')

# Route for updating results
@app.route('/instructor/update_results')
def update_results():
    try:
        # Get the token from localStorage
        token = request.cookies.get('instructorToken')
        if not token:
            return redirect('/')
            
        # Verify the token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # Verify it's an instructor token
        if data.get('type') != 'instructor':
            return redirect('/')
            
        return render_template('update_results.html')
    except Exception as e:
        logger.error(f"Error accessing update results page: {str(e)}")
        return redirect('/')

# API endpoint for searching students
@app.route('/api/students/search')
@token_required(allowed_types=("instructor",))
def search_students_api():
    try:
        search_term = request.args.get('query', '')
        if not search_term:
            return jsonify({'success': False, 'message': 'Search term is required'}), 400

        students = search_students(search_term)
        return jsonify({'success': True, 'students': students})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error searching students: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while searching students'}), 500

# API endpoint for submitting results
@app.route('/api/results', methods=['POST'])
def submit_result():
    try:
        # Get token from headers or cookies
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            token = request.cookies.get('instructorToken')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'instructor':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        result_data = request.get_json()
        
        # Validate required fields
        required_fields = ['student_id', 'subject', 'marks', 'grade', 'credits', 'academic_year', 'semester']
        for field in required_fields:
            if field not in result_data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Add result to database
        if add_result(
            result_data['student_id'],
            result_data['subject'],
            result_data['marks'],
            result_data['grade'],
            result_data['credits'],
            result_data['semester'],
            result_data['academic_year']
        ):
            return jsonify({'success': True, 'message': 'Result added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add result'}), 500

    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error adding result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the result'}), 500

# API endpoint for instructor button
@app.route('/api/instructor/button', methods=['GET'])
def instructor_button():
    try:
        # Check if there's a token in the request
        token = request.headers.get('Authorization')
        if token:
            try:
                # Verify the token
                token = token.split(' ')[1]  # Remove 'Bearer ' prefix
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                if data['type'] == 'instructor':
                    return jsonify({
                        'success': True,
                        'is_logged_in': True,
                        'message': 'Instructor is already logged in'
                    })
            except:
                pass

        # If no token or invalid token, just return success
        return jsonify({
            'success': True,
            'is_logged_in': False,
            'message': 'Instructor login form requested'
        })
    except Exception as e:
        logger.error(f"Error in instructor button: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred'
        }), 500

# API endpoint for getting all results
@app.route('/api/results')
def get_all_results():
    try:
        # Get token from headers or cookies
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            token = request.cookies.get('instructorToken')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'instructor':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Get all results from database
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.id, s.username as student_name, r.subject, r.marks, r.grade, 
                   r.credits, r.academic_year, r.semester
            FROM results r
            JOIN students s ON r.student_id = s.id
            ORDER BY s.username, r.academic_year, r.semester, r.subject
        ''')
        results = cursor.fetchall()
        conn.close()

        formatted_results = [{
            'id': row[0],
            'student_name': row[1],
            'subject': row[2],
            'marks': row[3],
            'grade': row[4],
            'credits': row[5],
            'academic_year': row[6],
            'semester': row[7]
        } for row in results]

        return jsonify({'success': True, 'results': formatted_results})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching results'}), 500

# API endpoint for filtering results
@app.route('/api/results/filter')
def filter_results():
    try:
        # Get token from headers or cookies
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            token = request.cookies.get('instructorToken')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'instructor':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Get filter parameters
        student = request.args.get('student', '')
        subject = request.args.get('subject', '')
        year = request.args.get('year', '')
        semester = request.args.get('semester', '')

        # Build query
        query = '''
            SELECT r.id, s.username as student_name, r.subject, r.marks, r.grade, 
                   r.credits, r.academic_year, r.semester
            FROM results r
            JOIN students s ON r.student_id = s.id
            WHERE 1=1
        '''
        params = []

        if student:
            query += ' AND (s.username LIKE ? OR s.id LIKE ?)'
            params.extend([f'%{student}%', f'%{student}%'])
        if subject:
            query += ' AND r.subject LIKE ?'
            params.append(f'%{subject}%')
        if year:
            query += ' AND r.academic_year = ?'
            params.append(year)
        if semester:
            query += ' AND r.semester = ?'
            params.append(semester)

        query += ' ORDER BY s.username, r.academic_year, r.semester, r.subject'

        # Execute query
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        formatted_results = [{
            'id': row[0],
            'student_name': row[1],
            'subject': row[2],
            'marks': row[3],
            'grade': row[4],
            'credits': row[5],
            'academic_year': row[6],
            'semester': row[7]
        } for row in results]

        return jsonify({'success': True, 'results': formatted_results})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error filtering results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while filtering results'}), 500

# API endpoint for updating a result
@app.route('/api/results/<int:result_id>', methods=['PUT'])
def update_result(result_id):
    try:
        # Get token from headers or cookies
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            token = request.cookies.get('instructorToken')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'instructor':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Get update data
        update_data = request.get_json()
        marks = update_data.get('marks')
        grade = update_data.get('grade')
        credits = update_data.get('credits')

        if not all([marks, grade, credits]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Update result in database
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE results
            SET marks = ?, grade = ?, credits = ?
            WHERE id = ?
        ''', (marks, grade, credits, result_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Result updated successfully'})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error updating result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the result'}), 500

# API endpoint for deleting a result
@app.route('/api/results/<int:result_id>', methods=['DELETE'])
def delete_result(result_id):
    try:
        # Get token from headers or cookies
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token.split(' ')[1]
        else:
            token = request.cookies.get('instructorToken')

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if data.get('type') != 'instructor':
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Delete result from database
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM results WHERE id = ?', (result_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Result deleted successfully'})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error deleting result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the result'}), 500

# API endpoint for downloading coding resources
@app.route('/api/coding-resources/<resource_type>')
def download_resource(resource_type):
    try:
        # Get token from cookie or Authorization header
        token = request.cookies.get('studentToken') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('type') != 'student':
                return jsonify({'error': 'Unauthorized'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        # Map resource types to their Google Drive URLs
        resource_urls = {
            'python': 'https://drive.google.com/file/d/17-onD-fMI7gKBQjtN8i1y2Skl_EqgDCN/view',
            'javascript': 'https://drive.google.com/file/d/17-onD-fMI7gKBQjtN8i1y2Skl_EqgDCN/view',
            'data-structures': 'https://drive.google.com/file/d/17-onD-fMI7gKBQjtN8i1y2Skl_EqgDCN/view'
        }

        if resource_type not in resource_urls:
            return jsonify({'error': 'Invalid resource type'}), 400

        # Get the Google Drive URL
        drive_url = resource_urls[resource_type]
        
        # Extract file ID from Google Drive URL
        file_id = get_google_drive_file_id(drive_url)
        if not file_id:
            return jsonify({'error': 'Invalid Google Drive URL'}), 400

        # Create resources directory if it doesn't exist
        os.makedirs(app.config['RESOURCES_FOLDER'], exist_ok=True)

        # Generate a secure filename
        filename = secure_filename(f"{resource_type}_guide.pdf")
        file_path = os.path.join(app.config['RESOURCES_FOLDER'], filename)

        # Download the file if it doesn't exist locally
        if not os.path.exists(file_path):
            try:
                # Use gdown for downloading from Google Drive
                url = f"https://drive.google.com/uc?id={file_id}"
                gdown.download(url, file_path, quiet=False)
            except Exception as e:
                logger.error(f"Error downloading file: {str(e)}")
                return jsonify({'error': 'Failed to download resource'}), 500

        # Check if file exists and is allowed
        if not os.path.exists(file_path) or not allowed_file(filename):
            return jsonify({'error': 'Resource not found'}), 404

        # Send the file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"Error in download_resource: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Add these helper functions
def is_valid_google_drive_url(url):
    """Check if the URL is a valid Google Drive URL."""
    parsed = urlparse(url)
    return 'drive.google.com' in parsed.netloc

def get_google_drive_file_id(url):
    """Extract file ID from Google Drive URL."""
    parsed = urlparse(url)
    if 'drive.google.com' in parsed.netloc:
        if '/file/d/' in url:
            return url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            return parse_qs(parsed.query)['id'][0]
    return None

def download_from_google_drive(file_id, destination):
    """Download a file from Google Drive using its file ID."""
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning_'):
                return value
        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32768
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk:
                    f.write(chunk)

    url = f"https://docs.google.com/uc?export=download"
    session = requests.Session()
    response = session.get(url, params={'id': file_id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': file_id, 'export': 'download', 'confirm': token}
        response = session.get(url, params=params, stream=True)

    save_response_content(response, destination)
    return True

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Add this new route for Google Drive downloads
@app.route('/api/coding-resources/download/<file_id>')
def download_from_drive(file_id):
    try:
        # Get token from cookie or Authorization header
        token = request.cookies.get('studentToken') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            if payload.get('type') != 'student':
                return jsonify({'error': 'Unauthorized'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        # Create resources directory if it doesn't exist
        os.makedirs(app.config['RESOURCES_FOLDER'], exist_ok=True)

        # Generate a secure filename
        filename = secure_filename(f"{file_id.split('-')[1]}_guide.pdf")
        file_path = os.path.join(app.config['RESOURCES_FOLDER'], filename)

        # Download the file if it doesn't exist locally
        if not os.path.exists(file_path):
            try:
                # Use gdown for downloading from Google Drive
                url = f"https://drive.google.com/uc?id={file_id}"
                gdown.download(url, file_path, quiet=False)
            except Exception as e:
                logger.error(f"Error downloading file: {str(e)}")
                return jsonify({'error': 'Failed to download resource'}), 500

        # Check if file exists and is allowed
        if not os.path.exists(file_path) or not allowed_file(filename):
            return jsonify({'error': 'Resource not found'}), 404

        # Send the file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )

    except Exception as e:
        logger.error(f"Error in download_from_drive: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Route for showing the registration template
@app.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

# API endpoint to send a chat message
@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    try:
        token = request.cookies.get('studentToken') or request.cookies.get('instructorToken')
        if not token:
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            sender = payload.get('user')
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        data = request.get_json()
        receiver = data.get('receiver')
        message = data.get('message')
        if not receiver or not message:
            return jsonify({'success': False, 'message': 'Receiver and message are required'}), 400
        if send_message(sender, receiver, message):
            return jsonify({'success': True, 'message': 'Message sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send message'}), 500
    except Exception as e:
        logger.error(f"Error sending chat message: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# API endpoint to fetch chat history between two users
@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    try:
        token = request.cookies.get('studentToken') or request.cookies.get('instructorToken')
        if not token:
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = payload.get('user')
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        other_user = request.args.get('other_user')
        if not other_user:
            return jsonify({'success': False, 'message': 'other_user parameter is required'}), 400
        messages = get_chat_history(user, other_user)
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        logger.error(f"Error fetching chat history: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# Route to render the chat page
@app.route('/chat')
def chat_page():
    other_user = request.args.get('user', '')
    return render_template('chat.html', other_user=other_user)

# Route for managing future tests
@app.route('/instructor/manage_future_tests')
@token_required(allowed_types=("instructor",))
def manage_future_tests():
    return render_template('manage_future_tests.html')

# API endpoint for getting instructor's future tests
@app.route('/api/instructor/future-tests')
@token_required(allowed_types=("instructor",))
def get_instructor_future_tests():
    try:
        # Get instructor info from the token (already validated by decorator)
        username = request.user['user']
        instructor = get_instructor_by_username(username)
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found'}), 404

        tests = get_future_tests_by_instructor(instructor['id'])
        return jsonify({'success': True, 'tests': tests})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error getting instructor's future tests: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching tests'}), 500

# API endpoint for adding a future test
@app.route('/api/instructor/future-tests', methods=['POST'])
@token_required(allowed_types=("instructor",))
def add_future_test_api():
    try:
        # Get instructor info from the token (already validated by decorator)
        username = request.user['user']
        instructor = get_instructor_by_username(username)
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found'}), 404

        test_data = request.get_json()
        
        # Validate required fields
        required_fields = ['subject', 'test_date', 'test_time', 'duration']
        for field in required_fields:
            if field not in test_data or not test_data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Add test to database
        if add_future_test(
            test_data['subject'],
            test_data['test_date'],
            test_data['test_time'],
            test_data['duration'],
            test_data.get('location', ''),
            test_data.get('test_type', ''),
            test_data.get('description', ''),
            instructor['id']
        ):
            return jsonify({'success': True, 'message': 'Test added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to add test'}), 500

    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error adding future test: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the test'}), 500

# API endpoint for updating a future test
@app.route('/api/instructor/future-tests/<int:test_id>', methods=['PUT'])
@token_required(allowed_types=("instructor",))
def update_future_test_api(test_id):
    try:
        test_data = request.get_json()
        
        # Validate required fields
        required_fields = ['subject', 'test_date', 'test_time', 'duration']
        for field in required_fields:
            if field not in test_data or not test_data[field]:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Update test in database
        if update_future_test(
            test_id,
            test_data['subject'],
            test_data['test_date'],
            test_data['test_time'],
            test_data['duration'],
            test_data.get('location', ''),
            test_data.get('test_type', ''),
            test_data.get('description', '')
        ):
            return jsonify({'success': True, 'message': 'Test updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to update test or test not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error updating future test: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the test'}), 500

# API endpoint for deleting a future test
@app.route('/api/instructor/future-tests/<int:test_id>', methods=['DELETE'])
@token_required(allowed_types=("instructor",))
def delete_future_test_api(test_id):
    try:
        # Delete test from database
        if delete_future_test(test_id):
            return jsonify({'success': True, 'message': 'Test deleted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to delete test or test not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Invalid token'}), 401
    except Exception as e:
        logger.error(f"Error deleting future test: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the test'}), 500

# Route for student evaluation page
@app.route('/student/evaluation')
@token_required(allowed_types=("student",))
def student_evaluation():
    return render_template('student_evaluation.html')

# Route for instructor evaluations page
@app.route('/instructor/evaluations')
@token_required(allowed_types=("instructor",))
def instructor_evaluations():
    return render_template('instructor_evaluations.html')

# API endpoint for getting all instructors (for student evaluation)
@app.route('/api/instructors')
@token_required(allowed_types=("student",))
def get_instructors_api():
    try:
        instructors = get_all_instructors()
        return jsonify({'success': True, 'instructors': instructors})
    except Exception as e:
        logger.error(f"Error getting instructors: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching instructors'}), 500

# API endpoint for submitting evaluation
@app.route('/api/evaluation', methods=['POST'])
@token_required(allowed_types=("student",))
def submit_evaluation():
    try:
        # Get student info from token
        username = request.user['user']
        student = get_student_by_username(username)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404

        evaluation_data = request.get_json()
        
        # Validate required fields
        required_fields = ['instructor_id', 'subject', 'teaching_quality', 'course_content', 'communication', 'overall_rating']
        for field in required_fields:
            if field not in evaluation_data:
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        # Add evaluation to database
        if add_evaluation(
            student['id'],
            evaluation_data['instructor_id'],
            evaluation_data['subject'],
            evaluation_data['teaching_quality'],
            evaluation_data['course_content'],
            evaluation_data['communication'],
            evaluation_data['overall_rating'],
            evaluation_data.get('comments', '')
        ):
            return jsonify({'success': True, 'message': 'Evaluation submitted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to submit evaluation'}), 500

    except Exception as e:
        logger.error(f"Error submitting evaluation: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while submitting evaluation'}), 500

# API endpoint for getting instructor's evaluations
@app.route('/api/instructor/evaluations')
@token_required(allowed_types=("instructor",))
def get_evaluations_api():
    try:
        # Get instructor info from token
        username = request.user['user']
        instructor = get_instructor_by_username(username)
        if not instructor:
            return jsonify({'success': False, 'message': 'Instructor not found'}), 404

        evaluations = get_instructor_evaluations(instructor['id'])
        return jsonify({'success': True, 'evaluations': evaluations})
    except Exception as e:
        logger.error(f"Error getting evaluations: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching evaluations'}), 500


MATH_API_URL = "https://api.mathjs.org/v4/"
WOLFRAM_API_URL = "https://api.wolframalpha.com/v1/result"

# Sample math topics and resources for students
MATH_TOPICS = {
    "algebra": {
        "title": "Algebra",
        "description": "Learn about equations, inequalities, and functions",
        "topics": [
            {"name": "Linear Equations", "formula": "ax + b = c", "example": "2x + 3 = 7"},
            {"name": "Quadratic Equations", "formula": "ax² + bx + c = 0", "example": "x² - 5x + 6 = 0"},
            {"name": "Systems of Equations", "formula": "Multiple equations with multiple variables", "example": "2x + y = 5, x - y = 1"}
        ]
    },
    "geometry": {
        "title": "Geometry",
        "description": "Study shapes, sizes, and spatial relationships",
        "topics": [
            {"name": "Area of Circle", "formula": "A = πr²", "example": "r = 5, A = 25π"},
            {"name": "Pythagorean Theorem", "formula": "a² + b² = c²", "example": "3² + 4² = 5²"},
            {"name": "Volume of Sphere", "formula": "V = (4/3)πr³", "example": "r = 3, V = 36π"}
        ]
    },
    "calculus": {
        "title": "Calculus",
        "description": "Explore limits, derivatives, and integrals",
        "topics": [
            {"name": "Derivative", "formula": "f'(x) = lim(h→0) [f(x+h) - f(x)]/h", "example": "d/dx(x²) = 2x"},
            {"name": "Integral", "formula": "∫f(x)dx", "example": "∫x dx = x²/2 + C"},
            {"name": "Chain Rule", "formula": "d/dx[f(g(x))] = f'(g(x))·g'(x)", "example": "d/dx(sin(x²)) = 2x·cos(x²)"}
        ]
    },
    "statistics": {
        "title": "Statistics",
        "description": "Learn about data analysis and probability",
        "topics": [
            {"name": "Mean", "formula": "μ = Σx/n", "example": "Mean of [1,2,3,4,5] = 3"},
            {"name": "Standard Deviation", "formula": "σ = √(Σ(x-μ)²/n)", "example": "SD of [1,2,3,4,5] ≈ 1.58"},
            {"name": "Probability", "formula": "P(A) = favorable/total", "example": "P(rolling 6) = 1/6"}
        ]
    }
}

@app.route("/math")
def math():
    return render_template("math.html")

@app.route("/api/math-topics")
def get_math_topics():
    return jsonify(MATH_TOPICS)

@app.route("/api/calculate", methods=["POST"])
def calculate():
    try:
        data = request.get_json()
        expression = data.get('expression', '')
        
        # Use MathJax API for calculations
        response = requests.post(MATH_API_URL, json={
            "expr": expression,
            "precision": 14
        })
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({"result": result.get('result', 'Error in calculation')})
        else:
            return jsonify({"error": "Calculation failed"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/topic/<topic_name>")
def get_topic_details(topic_name):
    if topic_name in MATH_TOPICS:
        return jsonify(MATH_TOPICS[topic_name])
    else:
        return jsonify({"error": "Topic not found"}), 404

#math  stuff ends here

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)