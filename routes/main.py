"""
iHIS - Main Routes
Public pages and landing routes.
"""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page - redirect to dashboard if logged in."""
    if current_user.is_authenticated:
        from routes.auth import redirect_to_dashboard
        return redirect_to_dashboard()
    return render_template('index.html')


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')
