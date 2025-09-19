# utils.py
import jwt
from flask import request, jsonify, redirect, current_app
from functools import wraps

def get_token_from_request():
    """Extract token from header or cookies"""
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        return token.split(' ')[1]
    
    # Check both instructor and student tokens
    return request.cookies.get('instructorToken') or request.cookies.get('studentToken')

def validate_token(token, expected_type=None):
    """Validate JWT token"""
    if not token:
        return None
        
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if expected_type and data.get('type') != expected_type:
            return None
        return data
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def token_required(allowed_types=("instructor",)):
    """Decorator for token validation"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            if not token:
                return jsonify({'success': False, 'message': 'Token is missing'}), 401

            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
                if data.get('type') not in allowed_types:
                    return jsonify({'success': False, 'message': 'Invalid token type'}), 401
                request.user = data
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': 'Invalid token'}), 401
            except Exception as e:
                current_app.logger.error(f"Token validation error: {str(e)}")
                return jsonify({'success': False, 'message': 'An error occurred during token validation'}), 500
        return decorated
    return decorator

def protected_route(expected_type):
    """Decorator for protected routes with automatic redirection"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            user_data = validate_token(token, expected_type)
            
            if not user_data:
                return redirect('/')
                
            # Add user data to request for access in routes
            request.user = user_data
            return f(*args, **kwargs)
        return decorated
    return decorator