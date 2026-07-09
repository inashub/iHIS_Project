"""
iHIS - Appointments Routes
Shared appointment management across roles.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.doctor import Appointment, Doctor
from models.patient import Patient

appointments_bp = Blueprint('appointments', __name__, template_folder='../templates/appointments')


@appointments_bp.route('/')
@login_required
def list():
    """List appointments based on role."""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', date.today().isoformat())

    query = Appointment.query.filter_by(is_deleted=False)

    # Role-based filtering
    if current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient:
            query = query.filter_by(patient_id=patient.id)
    elif current_user.role == 'doctor':
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            query = query.filter_by(doctor_id=doctor.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if date_filter:
        query = query.filter(Appointment.scheduled_date == date_filter)

    appointments = query.order_by(Appointment.scheduled_date, Appointment.scheduled_time).paginate(
        page=page, per_page=20, error_out=False)

    return render_template('appointments/list.html',
                         appointments=appointments,
                         status_filter=status_filter,
                         date_filter=date_filter)


@appointments_bp.route('/book', methods=['GET', 'POST'])
@login_required
def book():
    """Book new appointment."""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')

        # If patient role, use their own patient record
        if current_user.role == 'patient':
            patient = Patient.query.filter_by(user_id=current_user.id).first()
            patient_id = patient.id if patient else None

        appointment = Appointment(
            appointment_number=f'APT{datetime.now().strftime("%Y%m%d%H%M%S")}',
            patient_id=int(patient_id),
            doctor_id=int(request.form.get('doctor_id')),
            scheduled_date=datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%d').date(),
            scheduled_time=datetime.strptime(request.form.get('scheduled_time'), '%H:%M').time(),
            duration_minutes=int(request.form.get('duration', 30)),
            appointment_type=request.form.get('appointment_type', 'consultation'),
            priority=request.form.get('priority', 'routine'),
            reason=request.form.get('reason'),
            symptoms=request.form.get('symptoms'),
            status='scheduled',
            created_by=current_user.id
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment booked successfully.', 'success')

        if current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))
        return redirect(url_for('appointments.list'))

    doctors = Doctor.query.filter_by(status='active').all()
    patients = Patient.query.filter_by(is_deleted=False).order_by(Patient.last_name).all()
    return render_template('appointments/book.html', doctors=doctors, patients=patients)


@appointments_bp.route('/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id):
    """Cancel appointment."""
    appointment = Appointment.query.filter_by(id=appointment_id, is_deleted=False).first_or_404()
    appointment.status = 'cancelled'
    appointment.cancelled_by = current_user.id
    appointment.cancelled_at = datetime.now()
    appointment.cancellation_reason = request.form.get('reason', 'Cancelled by user')
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointments.list'))


@appointments_bp.route('/status/<int:appointment_id>', methods=['POST'])
@login_required
def update_status(appointment_id):
    """Update appointment status."""
    appointment = Appointment.query.filter_by(id=appointment_id, is_deleted=False).first_or_404()
    new_status = request.form.get('status')
    valid_statuses = ['scheduled', 'confirmed', 'checked_in', 'in_progress', 'completed', 'no_show']

    if new_status in valid_statuses:
        appointment.status = new_status
        if new_status == 'checked_in':
            appointment.checked_in_at = datetime.now()
        elif new_status == 'in_progress':
            appointment.started_at = datetime.now()
        elif new_status == 'completed':
            appointment.completed_at = datetime.now()
        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')

    return redirect(url_for('appointments.list'))
