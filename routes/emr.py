"""
iHIS - EMR Routes
Electronic Medical Record access across roles.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.patient import Patient
from models.medical_record import MedicalRecord, Diagnosis, Prescription, VitalSign

emr_bp = Blueprint('emr', __name__, template_folder='../templates/emr')


@emr_bp.route('/patient/<int:patient_id>')
@login_required
def view_emr(patient_id):
    """View complete EMR for a patient."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()

    # Check permission
    if current_user.role == 'patient' and patient.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    medical_records = MedicalRecord.query.filter_by(
        patient_id=patient.id, is_deleted=False
    ).order_by(MedicalRecord.visit_date.desc()).all()

    diagnoses = Diagnosis.query.filter_by(patient_id=patient.id, is_deleted=False).order_by(
        Diagnosis.created_at.desc()).all()

    prescriptions = Prescription.query.filter_by(patient_id=patient.id, is_deleted=False).order_by(
        Prescription.created_at.desc()).all()

    vital_signs = VitalSign.query.filter_by(patient_id=patient.id).order_by(
        VitalSign.measured_at.desc()).limit(20).all()

    return render_template('emr/view.html',
                         patient=patient,
                         medical_records=medical_records,
                         diagnoses=diagnoses,
                         prescriptions=prescriptions,
                         vital_signs=vital_signs)
