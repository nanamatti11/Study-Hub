# instructor_routes.py
from flask import Blueprint, render_template, redirect, request
from utils import protected_route

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

@instructor_bp.route('/dashboard')
@protected_route('instructor')
def dashboard():
    return render_template('instructor_dashboard.html', username=request.user['user'])

@instructor_bp.route('/manage_results')
@protected_route('instructor')
def manage_results():
    return render_template('manage_results.html')

@instructor_bp.route('/search_student')
@protected_route('instructor')
def search_student():
    return render_template('search_student.html')

@instructor_bp.route('/update_results')
@protected_route('instructor')
def update_results():
    return render_template('update_results.html')

@instructor_bp.route('/manage_future_tests')
@protected_route('instructor')
def manage_future_tests():
    return render_template('manage_future_tests.html')

@instructor_bp.route('/evaluations')
@protected_route('instructor')
def instructor_evaluations():
    return render_template('instructor_evaluations.html')