"""
iHIS - Administration Routes
Admin portal for staff management, departments, and reports.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.user import User, Role, AuditLog
from models.patient import Patient, Department
from models.doctor import Doctor
from models.nursing import Nurse
from models.dentistry import Dentist
from models.therapy import PhysicalTherapist

admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')


@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard."""
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    total_patients = Patient.query.filter_by(is_deleted=False).count()
    total_doctors = Doctor.query.filter_by(is_deleted=False).count()
    total_staff = User.query.filter(User.is_deleted == False, User.role != 'patient').count()
    total_departments = Department.query.filter_by(is_active=True).count()

    # Patient volume by month (mock data for chart)
    patient_volumes = [120, 135, 148, 162, 155, 170, 185, 190, 175, 195, 210, 225]

    # Department performance
    departments = Department.query.filter_by(is_active=True).all()

    return render_template('admin/dashboard.html',
                         total_patients=total_patients,
                         total_doctors=total_doctors,
                         total_staff=total_staff,
                         total_departments=total_departments,
                         patient_volumes=patient_volumes,
                         departments=departments)


@admin_bp.route('/staff')
@login_required
def staff():
    """Manage staff."""
    if current_user.role not in ['admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', 'all')

    query = User.query.filter(User.is_deleted == False, User.role != 'patient')
    if role_filter != 'all':
        query = query.filter_by(role=role_filter)

    staff = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)

    roles = Role.query.all()
    return render_template('admin/staff.html', staff=staff, roles=roles, current_role=role_filter)


@admin_bp.route('/staff/<int:user_id>/toggle', methods=['POST'])
@login_required
def toggle_staff(user_id):
    """Activate/deactivate staff."""
    if current_user.role not in ['admin', 'superadmin']:
        return redirect(url_for('main.index'))

    user = User.query.filter_by(id=user_id, is_deleted=False).first_or_404()
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'Status updated for {user.get_full_name()}.', 'success')
    return redirect(url_for('admin.staff'))


@admin_bp.route('/departments')
@login_required
def departments():
    """Manage departments."""
    if current_user.role not in ['admin', 'superadmin']:
        return redirect(url_for('main.index'))

    departments = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', departments=departments)


@admin_bp.route('/audit-logs')
@login_required
def audit_logs():
    """View audit logs."""
    if current_user.role not in ['admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False)
    return render_template('admin/audit_logs.html', logs=logs)


@admin_bp.route('/reports')
@login_required
def reports():
    """Administrative reports."""
    if current_user.role not in ['admin', 'superadmin']:
        return redirect(url_for('main.index'))

    return render_template('admin/reports.html')
