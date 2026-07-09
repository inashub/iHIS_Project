"""
iHIS - Dentistry Routes
Dental portal for charting, procedures, and orthodontic tracking.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.dentistry import DentalRecord, DentalCharting, DentalProcedure, DentalImage, ToothRecord, OrthodonticCase
from models.patient import Patient

dentistry_bp = Blueprint('dentistry', __name__, template_folder='../templates/dentistry')


@dentistry_bp.route('/dashboard')
@login_required
def dashboard():
    """Dentistry dashboard."""
    if current_user.role not in ['dentist', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    today = date.today()
    from models.doctor import Appointment
    today_appts = Appointment.query.filter(
        Appointment.scheduled_date == today,
        Appointment.is_deleted == False
    ).count()

    pending_plans = DentalProcedure.query.filter(
        DentalProcedure.outcome == 'pending_review'
    ).count()

    active_ortho = OrthodonticCase.query.filter_by(status='active').count()

    recent_procedures = DentalProcedure.query.order_by(
        DentalProcedure.procedure_date.desc()).limit(10).all()

    return render_template('dentistry/dashboard.html',
                         today_appointments=today_appts,
                         pending_plans=pending_plans,
                         active_ortho=active_ortho,
                         recent_procedures=recent_procedures)


@dentistry_bp.route('/patients')
@login_required
def patients():
    """List patients with dental records."""
    if current_user.role not in ['dentist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')

    query = Patient.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.patient_id.ilike(f'%{search}%')
            )
        )

    patients = query.order_by(Patient.last_name).paginate(page=page, per_page=20, error_out=False)
    return render_template('dentistry/patients.html', patients=patients, search=search)


@dentistry_bp.route('/patient/<int:patient_id>/chart')
@login_required
def dental_chart(patient_id):
    """View dental chart."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    dental_record = DentalRecord.query.filter_by(patient_id=patient.id).first()

    if not dental_record:
        dental_record = DentalRecord(
            patient_id=patient.id,
            dental_history='',
            numbering_system='universal'
        )
        db.session.add(dental_record)
        db.session.flush()
        for tooth_num in range(1, 33):
            tooth = ToothRecord(
                dental_record_id=dental_record.id,
                tooth_number=tooth_num,
                is_present=True,
                condition='healthy'
            )
            db.session.add(tooth)
        db.session.commit()

    chartings = DentalCharting.query.filter_by(patient_id=patient.id).order_by(
        DentalCharting.charting_date.desc()).all()

    return render_template('dentistry/dental_chart.html',
                         patient=patient,
                         dental_record=dental_record,
                         chartings=chartings)


@dentistry_bp.route('/patient/<int:patient_id>/add-charting', methods=['POST'])
@login_required
def add_charting(patient_id):
    """Add dental charting entry."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()

    charting = DentalCharting(
        dental_record_id=request.form.get('dental_record_id'),
        patient_id=patient.id,
        dentist_id=current_user.id,
        tooth_number=int(request.form.get('tooth_number')),
        surface=request.form.get('surface'),
        condition=request.form.get('condition'),
        treatment_needed=bool(request.form.get('treatment_needed')),
        notes=request.form.get('notes')
    )
    db.session.add(charting)
    db.session.commit()
    flash('Charting entry added.', 'success')
    return redirect(url_for('dentistry.dental_chart', patient_id=patient.id))


@dentistry_bp.route('/procedures')
@login_required
def procedures():
    """List dental procedures."""
    if current_user.role not in ['dentist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    procedures = DentalProcedure.query.order_by(DentalProcedure.procedure_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('dentistry/procedures.html', procedures=procedures)


@dentistry_bp.route('/orthodontics')
@login_required
def orthodontics():
    """List orthodontic cases."""
    if current_user.role not in ['dentist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    cases = OrthodonticCase.query.order_by(OrthodonticCase.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('dentistry/orthodontics.html', cases=cases)
