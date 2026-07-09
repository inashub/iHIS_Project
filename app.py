"""
iHIS - Intelligent Health Information System
Main Application Entry Point
"""
import os
import logging
from extensions import db, login_manager, migrate
from datetime import datetime
from flask import Flask, render_template, request, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

# Initialize extensions


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('iHIS')


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Load configuration
    from config import config
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'lab_reports'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'radiology'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'dental'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'dicom'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'therapy'), exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register context processors
    @app.context_processor
    def inject_globals():
        return {
            'APP_NAME': app.config['APP_NAME'],
            'APP_FULL_NAME': app.config['APP_FULL_NAME'],
            'APP_VERSION': app.config['APP_VERSION'],
            'HOSPITAL_NAME': app.config['HOSPITAL_NAME'],
            'now': datetime.now()
        }

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json:
            return jsonify({'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.is_json:
            return jsonify({'error': 'Not Found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': 'Internal Server Error'}), 500
        return render_template('errors/500.html'), 500

    # Request logging for audit
    @app.before_request
    def before_request():
        g.start_time = datetime.now()
        if current_user.is_authenticated:
            g.user_role = current_user.role
        else:
            g.user_role = 'anonymous'

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.now() - g.start_time).total_seconds()
            logger.info(
                f"{request.method} {request.path} - {response.status_code} - "
                f"Duration: {duration:.3f}s - User: {g.get('user_role', 'unknown')}"
            )
        return response

    # Register blueprints
    register_blueprints(app)

    # Create database tables
    with app.app_context():
        db.create_all()
        # Seed initial data
        from database.seed import seed_database
        seed_database()

    return app


def register_blueprints(app):
    """Register all Flask blueprints."""
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.patient import patient_bp
    from routes.doctor import doctor_bp
    from routes.laboratory import laboratory_bp
    from routes.radiology import radiology_bp
    from routes.pharmacy import pharmacy_bp
    from routes.dentistry import dentistry_bp
    from routes.therapy import therapy_bp
    from routes.nursing import nursing_bp
    from routes.reception import reception_bp
    from routes.admin import admin_bp
    from routes.superadmin import superadmin_bp
    from routes.emr import emr_bp
    from routes.appointments import appointments_bp
    from routes.reports import reports_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(patient_bp, url_prefix='/patient')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(laboratory_bp, url_prefix='/laboratory')
    app.register_blueprint(radiology_bp, url_prefix='/radiology')
    app.register_blueprint(pharmacy_bp, url_prefix='/pharmacy')
    app.register_blueprint(dentistry_bp, url_prefix='/dentistry')
    app.register_blueprint(therapy_bp, url_prefix='/therapy')
    app.register_blueprint(nursing_bp, url_prefix='/nursing')
    app.register_blueprint(reception_bp, url_prefix='/reception')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(superadmin_bp, url_prefix='/superadmin')
    app.register_blueprint(emr_bp, url_prefix='/emr')
    app.register_blueprint(appointments_bp, url_prefix='/appointments')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')


# User loader callback
@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))


# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
