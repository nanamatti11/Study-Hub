# auth.py
from flask import Blueprint, request, jsonify, redirect, url_for, flash, current_app
import jwt
from datetime import datetime, timedelta
from utils import get_token_from_request, validate_token, token_required
from database import verify_student, verify_instructor, add_student, add_instructor

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/student/login', methods=['POST'])
def student_login():
    try:
        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data received in login request")
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            current_app.logger.error("Missing credentials in login request")
            return jsonify({'success': False, 'message': 'Missing credentials'}), 400

        current_app.logger.info(f"Login attempt for user: {username}")

        # Check if user exists first
        if verify_student(username, password):
            current_app.logger.info(f"Successful login for user: {username}")
            token = jwt.encode({
                'user': username,
                'type': 'student',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
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
                secure=False,
                samesite='Lax',
                max_age=86400  # 24 hours
            )
            
            return response
            
        current_app.logger.warning(f"Failed login attempt for username: {username}")
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
        
    except Exception as e:
        current_app.logger.error(f"Error during student login: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

@auth_bp.route('/api/instructor/login', methods=['POST'])
def instructor_login():
    try:
        data = request.get_json()
        current_app.logger.debug(f"Login data received: {data}")

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        current_app.logger.debug(f"Username: {username}, Password: {password}")
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Missing credentials'}), 400
        
        if verify_instructor(username, password):
            current_app.logger.info(f"Login successful for: {username}")
            token = jwt.encode({
                'user': username,
                'type': 'instructor',
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
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
        
        current_app.logger.warning(f"Login failed for: {username}")
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401
    except Exception as e:
        current_app.logger.error(f"Error during instructor login: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during login'}), 500

@auth_bp.route('/api/student/register', methods=['POST'])
def student_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    fullname = data.get('fullname', username)
    email = data.get('email', f"{username}@example.com")

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})

    if add_student(username, password, fullname, email):
        token = jwt.encode({
            'user': username,
            'type': 'student',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        response = jsonify({'success': True, 'message': 'Student registered successfully', 'token': token})
        response.set_cookie('studentToken', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
        return response
    else:
        return jsonify({'success': False, 'message': 'Username already exists'})

@auth_bp.route('/api/instructor/register', methods=['POST'])
def instructor_register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    fullname = data.get('fullname', username)
    email = data.get('email', f"{username}@example.com")
    subject = data.get('subject', 'General')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required'})

    if add_instructor(username, password, fullname, email, subject):
        token = jwt.encode({
            'user': username,
            'type': 'instructor',
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')
        response = jsonify({'success': True, 'message': 'Instructor registered successfully', 'token': token})
        response.set_cookie('instructorToken', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
        return response
    else:
        return jsonify({'success': False, 'message': 'Username already exists'})

@auth_bp.route('/api/student/logout', methods=['POST'])
@token_required(allowed_types=("student",))
def student_logout():
    try:
        response = jsonify({'success': True, 'message': 'Logout successful'})
        response.delete_cookie('studentToken')
        return response
    except Exception as e:
        current_app.logger.error(f"Error during student logout: {str(e)}")
        return jsonify({'success': False, 'message': 'An error occurred during logout'}), 500