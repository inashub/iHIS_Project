"""
iHIS - Patient Routes
Patient portal with health records, appointments, prescriptions.
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.patient import Patient, Allergy, ChronicDisease, Vaccination, PatientDocument
from models.doctor import Appointment
from models.medical_record import MedicalRecord, Prescription, VitalSign

patient_bp = Blueprint('patient', __name__, template_folder='../templates/patient')


@patient_bp.route('/dashboard')
@login_required
def dashboard():
    """Patient dashboard."""
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    patient = Patient.query.filter_by(user_id=current_user.id, is_deleted=False).first()
    if not patient:
        flash('Patient record not found.', 'danger')
        return redirect(url_for('main.index'))

    upcoming_appts = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.scheduled_date >= date.today(),
        Appointment.is_deleted == False
    ).order_by(Appointment.scheduled_date).limit(5).all()

    active_meds = Prescription.query.filter(
        Prescription.patient_id == patient.id,
        Prescription.status == 'active',
        Prescription.is_deleted == False
    ).order_by(Prescription.created_at.desc()).limit(5).all()

    return render_template('patient/dashboard.html',
                         patient=patient,
                         upcoming_appointments=upcoming_appts,
                         active_medications=active_meds)
