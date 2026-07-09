"""
iHIS - Nursing Routes
Nursing portal for vitals, medication administration, and care plans.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.nursing import Nurse, NurseAssignment, NursingNote, MedicationAdministration, CarePlan, IntakeOutput
from models.patient import Patient
from models.medical_record import VitalSign

nursing_bp = Blueprint('nursing', __name__, template_folder='../templates/nursing')


@nursing_bp.route('/dashboard')
@login_required
def dashboard():
    """Nursing dashboard."""
    if current_user.role not in ['nurse', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    nurse = Nurse.query.filter_by(user_id=current_user.id).first()
    today = date.today()

    assigned_patients = NurseAssignment.query.filter(
        NurseAssignment.nurse_id == (nurse.id if nurse else 0),
        NurseAssignment.assigned_date == today
    ).count() if nurse else 0

    med_schedules = MedicationAdministration.query.filter(
        db.func.date(MedicationAdministration.scheduled_time) == today,
        MedicationAdministration.status == 'scheduled'
    ).count()

    critical_alerts = VitalSign.query.filter(
        VitalSign.is_critical == True,
        db.func.date(VitalSign.measured_at) == today
    ).count()

    assignments = []
    if nurse:
        assignments = NurseAssignment.query.filter(
            NurseAssignment.nurse_id == nurse.id,
            NurseAssignment.assigned_date == today
        ).all()

    return render_template('nursing/dashboard.html',
                         assigned_patients=assigned_patients,
                         med_schedules=med_schedules,
                         critical_alerts=critical_alerts,
                         assignments=assignments)


@nursing_bp.route('/patients')
@login_required
def patients():
    """List assigned patients."""
    if current_user.role not in ['nurse', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    patients = Patient.query.filter_by(is_deleted=False).order_by(
        Patient.last_name).paginate(page=page, per_page=20, error_out=False)
    return render_template('nursing/patients.html', patients=patients)


@nursing_bp.route('/patient/<int:patient_id>/vitals', methods=['GET', 'POST'])
@login_required
def record_vitals(patient_id):
    """Record vital signs."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()

    if request.method == 'POST':
        vitals = VitalSign(
            patient_id=patient.id,
            recorded_by=current_user.id,
            temperature=float(request.form.get('temperature', 0)),
            temperature_site=request.form.get('temperature_site', 'oral'),
            heart_rate=int(request.form.get('heart_rate', 0)),
            blood_pressure_systolic=int(request.form.get('bp_systolic', 0)),
            blood_pressure_diastolic=int(request.form.get('bp_diastolic', 0)),
            respiratory_rate=int(request.form.get('respiratory_rate', 0)),
            oxygen_saturation=float(request.form.get('oxygen_saturation', 0)),
            pain_score=int(request.form.get('pain_score', 0)),
            weight_kg=float(request.form.get('weight', 0)) if request.form.get('weight') else None,
            height_cm=float(request.form.get('height', 0)) if request.form.get('height') else None,
            notes=request.form.get('notes'),
            measured_at=datetime.now()
        )

        # Check critical values
        if (vitals.temperature and (vitals.temperature > 39.5 or vitals.temperature < 35)) or \
           (vitals.heart_rate and (vitals.heart_rate > 120 or vitals.heart_rate < 50)) or \
           (vitals.blood_pressure_systolic and vitals.blood_pressure_systolic > 180) or \
           (vitals.oxygen_saturation and vitals.oxygen_saturation < 90):
            vitals.is_critical = True
            vitals.critical_alert = 'Critical vital signs detected'

        db.session.add(vitals)
        db.session.commit()
        flash('Vital signs recorded.', 'success')
        return redirect(url_for('nursing.patients'))

    return render_template('nursing/record_vitals.html', patient=patient)


@nursing_bp.route('/patient/<int:patient_id>/notes', methods=['GET', 'POST'])
@login_required
def nursing_notes(patient_id):
    """Nursing notes."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    nurse = Nurse.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        note = NursingNote(
            patient_id=patient.id,
            nurse_id=nurse.id if nurse else 0,
            note_type=request.form.get('note_type', 'shift_note'),
            subjective=request.form.get('subjective'),
            objective=request.form.get('objective'),
            assessment=request.form.get('assessment'),
            plan=request.form.get('plan'),
            narrative=request.form.get('narrative'),
            shift=request.form.get('shift', 'day'),
            note_date=datetime.now()
        )
        db.session.add(note)
        db.session.commit()
        flash('Note added.', 'success')
        return redirect(url_for('nursing.patients'))

    notes = NursingNote.query.filter_by(patient_id=patient.id).order_by(
        NursingNote.created_at.desc()).all()
    return render_template('nursing/notes.html', patient=patient, notes=notes)


@nursing_bp.route('/medication-admin')
@login_required
def medication_admin():
    """Medication administration."""
    if current_user.role not in ['nurse', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    today = date.today()
    pending_meds = MedicationAdministration.query.filter(
        db.func.date(MedicationAdministration.scheduled_time) == today,
        MedicationAdministration.status == 'scheduled'
    ).order_by(MedicationAdministration.scheduled_time).all()
    return render_template('nursing/medication_admin.html', pending_meds=pending_meds)


@nursing_bp.route('/care-plans')
@login_required
def care_plans():
    """List care plans."""
    if current_user.role not in ['nurse', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    plans = CarePlan.query.order_by(CarePlan.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('nursing/care_plans.html', plans=plans)
