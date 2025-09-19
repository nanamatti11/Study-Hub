# app.py
import os
import re
import io
import logging
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlparse, parse_qs

from flask import (
    Flask, request, jsonify, render_template, session, redirect, send_file, url_for, flash, current_app
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
    get_all_instructors, get_student_fullname, get_all_results_joined, filter_results_db
)

# Import blueprints
from auth import auth_bp
from student_routes import student_bp
from instructor_routes import instructor_bp
from utils import token_required, protected_route, get_token_from_request, validate_token

# Configure logging for debugging and error tracking
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask application
app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), 'templates'),
    static_folder=os.path.join(os.path.dirname(__file__), 'static')
)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_hub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
app.config['RESOURCES_FOLDER'] = os.path.join(app.static_folder, 'resources')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(instructor_bp)

# Initialize SQLAlchemy with the app for database operations
db = SQLAlchemy()
db.init_app(app)

# Initialize the database with required tables
init_db()

# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

# Helper function to validate email format
def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

# Helper function to validate password strength
def validate_password(password):
    return len(password) >= 8 and any(char.isdigit() for char in password)

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for new user page
@app.route('/new/user')
def new():
    return render_template('new.html')

# Route for user registration (keep this as it uses form submission)
@app.route('/api/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get and validate form data
            fullname = request.form.get('fullname', '').strip()
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            user_type = request.form.get('user_type', '').strip()
            subject = request.form.get('subject', '').strip() if user_type == 'instructor' else None

            # Validation checks
            if not all([fullname, username, email, password, confirm_password, user_type]):
                app.logger.error(f"Missing fields: fullname={fullname}, username={username}, email={email}, password={'***' if password else ''}, confirm_password={'***' if confirm_password else ''}, user_type={user_type}")
                flash('All fields are required', 'error')
                return redirect(url_for('register'))

            # Check if passwords match
            if password != confirm_password:
                app.logger.error(f"Password mismatch for username={username}")
                flash('Passwords do not match', 'error')
                return redirect(url_for('register'))

            if user_type not in ['instructor', 'student']:
                app.logger.error(f"Invalid user_type: {user_type}")
                flash('Invalid user type selected', 'error')
                return redirect(url_for('register'))

            if not validate_email(email):
                app.logger.error(f"Invalid email format: {email}")
                flash('Invalid email format', 'error')
                return redirect(url_for('register'))

            if not validate_password(password):
                app.logger.error(f"Password does not meet requirements: {password}")
                flash('Password must be at least 8 characters long and contain at least one number', 'error')
                return redirect(url_for('register'))

            if user_type == 'instructor' and not subject:
                app.logger.error(f"Missing subject for instructor registration")
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
                app.logger.info(f"Tried to add student: username={username}, email={email}, success={success}")
            else:  # instructor
                success = add_instructor(
                    username=username,
                    password=password,
                    fullname=fullname,
                    email=email,
                    subject=subject
                )
                app.logger.info(f"Tried to add instructor: username={username}, email={email}, subject={subject}, success={success}")

            if success:
                flash('Registration successful!', 'success')
                return redirect(url_for('index'))
            else:
                app.logger.error(f"Registration failed for username={username}, email={email}")
                flash('Email or username already registered', 'error')
                return redirect(url_for('register'))

        except Exception as e:
            app.logger.error(f"Registration error: {str(e)}")
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))

    return render_template('register.html')

# API endpoint for getting student results
@app.route('/api/student/results')
def get_student_results_api():
    try:
        token = get_token_from_request()
        user_data = validate_token(token, 'student')
        
        if not user_data:
            return jsonify({'success': False, 'message': 'Token is missing or invalid'}), 401
            
        username = user_data['user']
        year = request.args.get('year')
        semester = request.args.get('semester')
        
        if not year or not semester:
            return jsonify({'success': False, 'message': 'Year and semester are required'})
            
        student = get_student_by_username(username)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
            
        full_name = get_student_fullname(username) or username
        results = get_student_results(student['id'], year, semester)
        
        return jsonify({
            'success': True,
            'results': results,
            'student_info': {
                'name': full_name,
                'id': student['id']
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting student results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching results'}), 500

# API endpoint for getting future tests
@app.route('/api/student/future-tests')
@token_required(allowed_types=("student",))
def get_future_tests():
    try:
        tests = get_all_future_tests()
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
        app.logger.error(f"Error getting future tests: {str(e)}")
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
    # Get username from the already validated token (set by the decorator)
    username = request.user['user']
    
    # Fetch full name and id from the database
    conn = sqlite3.connect('study_hub.db')
    cursor = conn.cursor()
    cursor.execute('SELECT fullname, id FROM students WHERE username = ? OR email = ?', (username, username))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'success': False, 'message': 'Student not found'}), 404
    
    student_info = {
        'fullname': row[0],
        'id': row[1],
        'username': username
    }
    return jsonify({'success': True, 'student_info': student_info})

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
    except Exception as e:
        app.logger.error(f"Error searching students: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while searching students'}), 500

# API endpoint for submitting results
@app.route('/api/results', methods=['POST'])
def submit_result():
    try:
        # Get token from headers or cookies
        token = get_token_from_request()

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        user_data = validate_token(token, 'instructor')
        if not user_data:
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

    except Exception as e:
        app.logger.error(f"Error adding result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while adding the result'}), 500

# API endpoint for getting all results
@app.route('/api/results')
def get_all_results():
    try:
        # Get token from headers or cookies
        token = get_token_from_request()

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        user_data = validate_token(token, 'instructor')
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Get all results via database helper
        results = get_all_results_joined()

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
    except Exception as e:
        app.logger.error(f"Error getting results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching results'}), 500

# API endpoint for filtering results
@app.route('/api/results/filter')
def filter_results():
    try:
        # Get token from headers or cookies
        token = get_token_from_request()

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        user_data = validate_token(token, 'instructor')
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Get filter parameters
        student = request.args.get('student', '')
        subject = request.args.get('subject', '')
        year = request.args.get('year', '')
        semester = request.args.get('semester', '')

        # Execute via helper
        results = filter_results_db(student, subject, year, semester)

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
    except Exception as e:
        app.logger.error(f"Error filtering results: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while filtering results'}), 500

# API endpoint for updating a result
@app.route('/api/results/<int:result_id>', methods=['PUT'])
def update_result(result_id):
    try:
        # Get token from headers or cookies
        token = get_token_from_request()

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        user_data = validate_token(token, 'instructor')
        if not user_data:
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
    except Exception as e:
        app.logger.error(f"Error updating result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while updating the result'}), 500

# API endpoint for deleting a result
@app.route('/api/results/<int:result_id>', methods=['DELETE'])
def delete_result(result_id):
    try:
        # Get token from headers or cookies
        token = get_token_from_request()

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        # Decode token to get instructor info
        user_data = validate_token(token, 'instructor')
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid token type'}), 401

        # Delete result from database
        conn = sqlite3.connect('study_hub.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM results WHERE id = ?', (result_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Result deleted successfully'})
    except Exception as e:
        app.logger.error(f"Error deleting result: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the result'}), 500

# API endpoint for downloading coding resources
@app.route('/api/coding-resources/<resource_type>')
def download_resource(resource_type):
    try:
        # Get token from cookie or Authorization header
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        user_data = validate_token(token, 'student')
        if not user_data:
            return jsonify({'error': 'Unauthorized'}), 403

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
                app.logger.error(f"Error downloading file: {str(e)}")
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
        app.logger.error(f"Error in download_resource: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper functions for Google Drive
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

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Add this new route for Google Drive downloads
@app.route('/api/coding-resources/download/<file_id>')
def download_from_drive(file_id):
    try:
        # Get token from cookie or Authorization header
        token = get_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Verify token
        user_data = validate_token(token, 'student')
        if not user_data:
            return jsonify({'error': 'Unauthorized'}), 403

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
                app.logger.error(f"Error downloading file: {str(e)}")
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
        app.logger.error(f"Error in download_from_drive: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Route for showing the registration template
@app.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

# API endpoint to send a chat message
@app.route('/api/chat/send', methods=['POST'])
def chat_send():
    try:
        token = get_token_from_request()
        if not token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        user_data = validate_token(token)
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
            
        sender = user_data.get('user')
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
        app.logger.error(f"Error sending chat message: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# API endpoint to fetch chat history between two users
@app.route('/api/chat/history', methods=['GET'])
def chat_history():
    try:
        token = get_token_from_request()
        if not token:
            return jsonify({'success': False, 'message': 'Authentication required'}), 401
        
        user_data = validate_token(token)
        if not user_data:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
            
        user = user_data.get('user')
        other_user = request.args.get('other_user')
        
        if not other_user:
            return jsonify({'success': False, 'message': 'other_user parameter is required'}), 400
            
        messages = get_chat_history(user, other_user)
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        app.logger.error(f"Error fetching chat history: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

# Route to render the chat page
@app.route('/chat')
def chat_page():
    other_user = request.args.get('user', '')
    return render_template('chat.html', other_user=other_user)

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
    except Exception as e:
        app.logger.error(f"Error getting instructor's future tests: {str(e)}")
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

    except Exception as e:
        app.logger.error(f"Error adding future test: {str(e)}")
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

    except Exception as e:
        app.logger.error(f"Error updating future test: {str(e)}")
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

    except Exception as e:
        app.logger.error(f"Error deleting future test: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while deleting the test'}), 500

# API endpoint for getting all instructors (for student evaluation)
@app.route('/api/instructors')
@token_required(allowed_types=("student",))
def get_instructors_api():
    try:
        instructors = get_all_instructors()
        return jsonify({'success': True, 'instructors': instructors})
    except Exception as e:
        app.logger.error(f"Error getting instructors: {str(e)}")
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
        app.logger.error(f"Error submitting evaluation: {str(e)}")
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
        app.logger.error(f"Error getting evaluations: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred while fetching evaluations'}), 500

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)