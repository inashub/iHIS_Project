"""
iHIS - Authentication Routes
Login, logout, registration, password management.
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User, AuditLog

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect_to_dashboard()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter(
            db.or_(User.username == username, User.email == username),
            User.is_deleted == False
        ).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                return render_template('auth/login.html')

            if user.is_locked():
                flash('Your account is temporarily locked. Please try again later.', 'danger')
                return render_template('auth/login.html')

            # Successful login
            user.last_login = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            user.failed_login_attempts = 0
            db.session.commit()

            # Log audit
            audit = AuditLog(
                user_id=user.id,
                action='LOGIN',
                resource='user',
                resource_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:255] if request.user_agent else None,
                status='success'
            )
            db.session.add(audit)
            db.session.commit()

            login_user(user, remember=remember)
            session.permanent = remember

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect_to_dashboard()

        # Failed login
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                from datetime import timedelta
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            db.session.commit()

        flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    audit = AuditLog(
        user_id=current_user.id,
        action='LOGOUT',
        resource='user',
        resource_id=current_user.id,
        ip_address=request.remote_addr,
        status='success'
    )
    db.session.add(audit)
    db.session.commit()

    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle patient self-registration."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')

        # Validation
        if not all([username, email, password, first_name, last_name]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/register.html')

        # Check existing
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'danger')
            return render_template('auth/register.html')

        # Create user
        from models.patient import Patient
        from models.user import Role

        patient_role = Role.query.filter_by(name='patient').first()

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='patient',
            role_id=patient_role.id if patient_role else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create patient record
        patient = Patient(
            patient_id=f'PT{user.id:05d}',
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
            gender=gender or 'other',
            email=email,
            phone_primary=phone
        )
        db.session.add(patient)

        # Audit log
        audit = AuditLog(
            user_id=user.id,
            action='CREATE',
            resource='user',
            resource_id=user.id,
            details='Patient self-registration',
            ip_address=request.remote_addr,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.email = request.form.get('email', current_user.email)
        current_user.timezone = request.form.get('timezone', current_user.timezone)
        current_user.language = request.form.get('language', current_user.language)

        # Handle avatar upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file.filename:
                import os
                from werkzeug.utils import secure_filename
                filename = secure_filename(f'user_{current_user.id}_{file.filename}')
                filepath = os.path.join('static/uploads/avatars', filename)
                file.save(filepath)
                current_user.avatar = filename

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password."""
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('auth.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('auth.profile'))

    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'danger')
        return redirect(url_for('auth.profile'))

    current_user.set_password(new_password)
    db.session.commit()

    flash('Password changed successfully.', 'success')
    return redirect(url_for('auth.profile'))


def redirect_to_dashboard():
    """Redirect user to their role-specific dashboard."""
    role_redirects = {
        'patient': 'patient.dashboard',
        'doctor': 'doctor.dashboard',
        'lab_tech': 'laboratory.dashboard',
        'radiologist': 'radiology.dashboard',
        'pharmacist': 'pharmacy.dashboard',
        'dentist': 'dentistry.dashboard',
        'therapist': 'therapy.dashboard',
        'nurse': 'nursing.dashboard',
        'receptionist': 'reception.dashboard',
        'admin': 'admin.dashboard',
        'superadmin': 'superadmin.dashboard',
    }
    endpoint = role_redirects.get(current_user.role, 'main.index')
    return redirect(url_for(endpoint))
