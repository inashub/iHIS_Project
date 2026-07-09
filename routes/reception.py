"""
iHIS - Reception Routes
Reception portal for scheduling, check-in, and queue management.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.doctor import Appointment, Doctor
from models.patient import Patient

reception_bp = Blueprint('reception', __name__, template_folder='../templates/reception')


@reception_bp.route('/dashboard')
@login_required
def dashboard():
    """Reception dashboard."""
    if current_user.role not in ['receptionist', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    today = date.today()

    daily_appts = Appointment.query.filter(
        Appointment.scheduled_date == today,
        Appointment.is_deleted == False
    ).count()

    waiting = Appointment.query.filter(
        Appointment.scheduled_date == today,
        Appointment.status == 'checked_in',
        Appointment.is_deleted == False
    ).count()

    checked_in = Appointment.query.filter(
        Appointment.scheduled_date == today,
        Appointment.status.in_(['checked_in', 'in_progress']),
        Appointment.is_deleted == False
    ).count()

    todays_appointments = Appointment.query.filter(
        Appointment.scheduled_date == today,
        Appointment.is_deleted == False
    ).order_by(Appointment.scheduled_time).all()

    return render_template('reception/dashboard.html',
                         daily_appointments=daily_appts,
                         waiting=waiting,
                         checked_in=checked_in,
                         todays_appointments=todays_appointments)


@reception_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    """Schedule appointment."""
    if current_user.role not in ['receptionist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        appointment = Appointment(
            appointment_number=f'APT{datetime.now().strftime("%Y%m%d%H%M%S")}',
            patient_id=int(request.form.get('patient_id')),
            doctor_id=int(request.form.get('doctor_id')),
            scheduled_date=datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%d').date(),
            scheduled_time=datetime.strptime(request.form.get('scheduled_time'), '%H:%M').time(),
            duration_minutes=int(request.form.get('duration', 30)),
            appointment_type=request.form.get('appointment_type', 'consultation'),
            reason=request.form.get('reason'),
            symptoms=request.form.get('symptoms'),
            notes=request.form.get('notes'),
            status='scheduled',
            created_by=current_user.id
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment scheduled successfully.', 'success')
        return redirect(url_for('reception.dashboard'))

    patients = Patient.query.filter_by(is_deleted=False).order_by(Patient.last_name).all()
    doctors = Doctor.query.filter_by(status='active').all()
    return render_template('reception/schedule.html', patients=patients, doctors=doctors)


@reception_bp.route('/checkin/<int:appointment_id>', methods=['POST'])
@login_required
def checkin(appointment_id):
    """Check in patient."""
    appointment = Appointment.query.filter_by(id=appointment_id, is_deleted=False).first_or_404()
    appointment.status = 'checked_in'
    appointment.checked_in_at = datetime.now()
    db.session.commit()
    flash('Patient checked in.', 'success')
    return redirect(url_for('reception.dashboard'))


@reception_bp.route('/appointments')
@login_required
def appointments():
    """List appointments."""
    if current_user.role not in ['receptionist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', date.today().isoformat())

    appointments = Appointment.query.filter(
        Appointment.scheduled_date == date_filter,
        Appointment.is_deleted == False
    ).order_by(Appointment.scheduled_time).paginate(page=page, per_page=20, error_out=False)

    return render_template('reception/appointments.html',
                         appointments=appointments,
                         date_filter=date_filter)


@reception_bp.route('/register-patient', methods=['GET', 'POST'])
@login_required
def register_patient():
    """Register new patient."""
    if current_user.role not in ['receptionist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Check if user exists
        from models.user import User, Role
        role = Role.query.filter_by(name='patient').first()

        user = User(
            username=request.form.get('email').split('@')[0],
            email=request.form.get('email'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            role='patient',
            role_id=role.id if role else None
        )
        user.set_password(request.form.get('phone') or 'password123')
        db.session.add(user)
        db.session.flush()

        patient = Patient(
            patient_id=f'PT{user.id:05d}',
            user_id=user.id,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            gender=request.form.get('gender', 'other'),
            email=request.form.get('email'),
            phone_primary=request.form.get('phone'),
            address=request.form.get('address'),
            city=request.form.get('city'),
            state=request.form.get('state'),
            zip_code=request.form.get('zip_code'),
            emergency_contact_name=request.form.get('emergency_name'),
            emergency_contact_phone=request.form.get('emergency_phone'),
            emergency_contact_relationship=request.form.get('emergency_relationship'),
            insurance_provider=request.form.get('insurance_provider'),
            insurance_policy_number=request.form.get('insurance_policy')
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient registered successfully.', 'success')
        return redirect(url_for('reception.dashboard'))

    return render_template('reception/register_patient.html')
