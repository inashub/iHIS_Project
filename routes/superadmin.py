"""
iHIS - Super Admin Routes
Full system control, user management, configuration.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User, Role, Permission, SystemSetting
from models.patient import Patient

superadmin_bp = Blueprint('superadmin', __name__, template_folder='../templates/superadmin')


@superadmin_bp.route('/dashboard')
@login_required
def dashboard():
    """Super Admin dashboard."""
    if current_user.role != 'superadmin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    total_users = User.query.filter_by(is_deleted=False).count()
    active_users = User.query.filter_by(is_active=True, is_deleted=False).count()
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    total_roles = Role.query.count()

    recent_users = User.query.filter_by(is_deleted=False).order_by(
        User.created_at.desc()).limit(10).all()

    return render_template('superadmin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_patients=total_patients,
                         total_roles=total_roles,
                         recent_users=recent_users)


@superadmin_bp.route('/users')
@login_required
def users():
    """Manage all users."""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(is_deleted=False).order_by(
        User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('superadmin/users.html', users=users)


@superadmin_bp.route('/roles')
@login_required
def roles():
    """Manage roles and permissions."""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

    roles = Role.query.all()
    permissions = Permission.query.all()
    return render_template('superadmin/roles.html', roles=roles, permissions=permissions)


@superadmin_bp.route('/settings')
@login_required
def settings():
    """System settings."""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

    settings = SystemSetting.query.order_by(SystemSetting.category, SystemSetting.key).all()
    return render_template('superadmin/settings.html', settings=settings)


@superadmin_bp.route('/settings/update', methods=['POST'])
@login_required
def update_setting():
    """Update system setting."""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

    setting_id = request.form.get('setting_id')
    value = request.form.get('value')

    setting = SystemSetting.query.get_or_404(setting_id)
    setting.value = value
    setting.updated_at = datetime.now()
    db.session.commit()
    flash('Setting updated.', 'success')
    return redirect(url_for('superadmin.settings'))


@superadmin_bp.route('/backup')
@login_required
def backup():
    """Database backup."""
    if current_user.role != 'superadmin':
        return redirect(url_for('main.index'))

    import sqlite3
    import shutil
    from flask import current_app

    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    backup_dir = 'database/backups'
    import os
    os.makedirs(backup_dir, exist_ok=True)

    backup_file = f'{backup_dir}/ihis_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    shutil.copy2(db_path, backup_file)
    flash(f'Database backed up to {backup_file}.', 'success')
    return redirect(url_for('superadmin.dashboard'))
