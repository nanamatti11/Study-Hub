# student_routes.py
from flask import Blueprint, render_template, request, jsonify, redirect, current_app
from utils import protected_route
from database import get_student_results, get_all_future_tests, get_student_by_username, get_student_fullname

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@protected_route('student')
def dashboard():
    return render_template('student_dashboard.html', username=request.user['user'])

@student_bp.route('/check-result')
@protected_route('student')
def check_result():
    return render_template('check_result.html')

@student_bp.route('/future-tests')
@protected_route('student')
def future_tests():
    return render_template('future_tests.html')

@student_bp.route('/learning-resources')
@protected_route('student')
def learning_resources():
    return render_template('learning_resources.html')

@student_bp.route('/coding-resources')
@protected_route('student')
def coding_resources():
    return render_template('coding_resources.html')

@student_bp.route('/evaluation')
@protected_route('student')
def student_evaluation():
    return render_template('student_evaluation.html')