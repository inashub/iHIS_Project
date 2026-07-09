"""
iHIS - Doctor Routes
Doctor portal with EMR, prescriptions, lab orders, and patient management.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.user import User, Notification, AuditLog
from models.patient import Patient, Allergy, ChronicDisease
from models.doctor import Doctor, Appointment
from models.medical_record import MedicalRecord, Diagnosis, Prescription, PrescriptionItem, VitalSign, Referral
from models.laboratory import LabOrder, LabTestCatalog
from models.radiology import RadiologyOrder, ImagingProcedure

doctor_bp = Blueprint('doctor', __name__, template_folder='../templates/doctor')


def get_doctor():
    """Get current user's doctor profile."""
    return Doctor.query.filter_by(user_id=current_user.id).first()


@doctor_bp.route('/')
@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    """Doctor dashboard."""
    if current_user.role != 'doctor':
        flash('Access denied. Doctor role required.', 'danger')
        return redirect(url_for('main.index'))

    doctor = get_doctor()
    today = date.today()

    # Statistics
    today_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id if doctor else False,
        Appointment.scheduled_date == today,
        Appointment.is_deleted == False
    ).count() if doctor else 0

    total_patients = Patient.query.filter_by(is_deleted=False).count()
    pending_reports = MedicalRecord.query.filter(
        MedicalRecord.doctor_id == (doctor.id if doctor else 0),
        MedicalRecord.status == 'active',
        MedicalRecord.is_deleted == False
    ).count() if doctor else 0

    # Upcoming appointments
    upcoming = []
    if doctor:
        upcoming = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_date >= today,
            Appointment.is_deleted == False
        ).order_by(Appointment.scheduled_date, Appointment.scheduled_time).limit(10).all()

    # Recent patients
    recent_patients = Patient.query.filter_by(is_deleted=False).order_by(
        Patient.updated_at.desc()
    ).limit(8).all()

    return render_template('doctor/dashboard.html',
                         doctor=doctor,
                         today_appointments=today_appointments,
                         total_patients=total_patients,
                         pending_reports=pending_reports,
                         upcoming_appointments=upcoming,
                         recent_patients=recent_patients)


@doctor_bp.route('/patients')
@login_required
def patients():
    """Patient list."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))

    search = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    query = Patient.query.filter_by(is_deleted=False)
    if search:
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                Patient.patient_id.ilike(f'%{search}%'),
                Patient.email.ilike(f'%{search}%')
            )
        )

    patients = query.order_by(Patient.last_name).paginate(page=page, per_page=20, error_out=False)
    return render_template('doctor/patients.html', patients=patients, search=search)


@doctor_bp.route('/patients/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    """Patient detail view."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    allergies = Allergy.query.filter_by(patient_id=patient.id).all()
    chronic_diseases = ChronicDisease.query.filter_by(patient_id=patient.id).all()
    vital_signs = VitalSign.query.filter_by(patient_id=patient.id).order_by(VitalSign.measured_at.desc()).limit(10).all()
    medical_records = MedicalRecord.query.filter_by(patient_id=patient.id, is_deleted=False).order_by(
        MedicalRecord.visit_date.desc()).limit(10).all()
    prescriptions = Prescription.query.filter_by(patient_id=patient.id, is_deleted=False).order_by(
        Prescription.created_at.desc()).limit(10).all()

    return render_template('doctor/patient_detail.html',
                         patient=patient,
                         allergies=allergies,
                         chronic_diseases=chronic_diseases,
                         vital_signs=vital_signs,
                         medical_records=medical_records,
                         prescriptions=prescriptions)


@doctor_bp.route('/patients/<int:patient_id>/new-record', methods=['GET', 'POST'])
@login_required
def new_medical_record(patient_id):
    """Create new medical record / SOAP note."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    doctor = get_doctor()

    if request.method == 'POST':
        record = MedicalRecord(
            record_number=f'MR{datetime.now().strftime("%Y%m%d%H%M%S")}',
            patient_id=patient.id,
            doctor_id=doctor.id if doctor else 0,
            visit_date=datetime.now(),
            chief_complaint=request.form.get('chief_complaint'),
            subjective=request.form.get('subjective'),
            objective=request.form.get('objective'),
            assessment=request.form.get('assessment'),
            plan=request.form.get('plan'),
            general_appearance=request.form.get('general_appearance'),
            physical_exam_findings=request.form.get('physical_exam_findings'),
            follow_up_instructions=request.form.get('follow_up_instructions'),
            follow_up_date=datetime.strptime(request.form.get('follow_up_date'), '%Y-%m-%d').date() if request.form.get('follow_up_date') else None,
            follow_up_needed=bool(request.form.get('follow_up_needed')),
            status='active'
        )
        db.session.add(record)
        db.session.flush()

        # Handle diagnoses
        diagnoses_data = request.form.getlist('diagnosis[]')
        icd10_codes = request.form.getlist('icd10_code[]')
        for i, diag in enumerate(diagnoses_data):
            if diag.strip():
                diagnosis = Diagnosis(
                    medical_record_id=record.id,
                    patient_id=patient.id,
                    doctor_id=doctor.id if doctor else 0,
                    diagnosis_type='primary' if i == 0 else 'secondary',
                    icd10_code=icd10_codes[i] if i < len(icd10_codes) else None,
                    icd10_description=diag,
                    clinical_description=diag,
                    status='active'
                )
                db.session.add(diagnosis)

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            action='CREATE',
            resource='medical_record',
            resource_id=record.id,
            details=f'Created medical record for patient {patient.patient_id}',
            ip_address=request.remote_addr,
            status='success'
        )
        db.session.add(audit)
        db.session.commit()

        flash('Medical record created successfully.', 'success')
        return redirect(url_for('doctor.patient_detail', patient_id=patient.id))

    return render_template('doctor/new_record.html', patient=patient)


@doctor_bp.route('/patients/<int:patient_id>/new-prescription', methods=['GET', 'POST'])
@login_required
def new_prescription(patient_id):
    """Create new prescription."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    doctor = get_doctor()

    if request.method == 'POST':
        prescription = Prescription(
            prescription_number=f'RX{datetime.now().strftime("%Y%m%d%H%M%S")}',
            patient_id=patient.id,
            doctor_id=doctor.id if doctor else 0,
            diagnosis=request.form.get('diagnosis'),
            notes=request.form.get('notes'),
            instructions=request.form.get('instructions'),
            status='active',
            start_date=date.today()
        )
        db.session.add(prescription)
        db.session.flush()

        # Add prescription items
        medications = request.form.getlist('medication[]')
        dosages = request.form.getlist('dosage[]')
        frequencies = request.form.getlist('frequency[]')
        routes = request.form.getlist('route[]')
        durations = request.form.getlist('duration[]')

        for i in range(len(medications)):
            if medications[i].strip():
                from models.medical_record import Medication
                med = Medication.query.filter_by(name=medications[i]).first()
                med_id = med.id if med else None

                item = PrescriptionItem(
                    prescription_id=prescription.id,
                    medication_id=med_id,
                    dosage=dosages[i] if i < len(dosages) else '',
                    frequency=frequencies[i] if i < len(frequencies) else '',
                    route=routes[i] if i < len(routes) else 'oral',
                    duration=durations[i] if i < len(durations) else ''
                )
                db.session.add(item)

        db.session.commit()
        flash('Prescription created successfully.', 'success')
        return redirect(url_for('doctor.patient_detail', patient_id=patient.id))

    from models.medical_record import Medication
    medications = Medication.query.filter_by(is_active=True).all()
    return render_template('doctor/new_prescription.html', patient=patient, medications=medications)


@doctor_bp.route('/patients/<int:patient_id>/order-lab', methods=['GET', 'POST'])
@login_required
def order_lab(patient_id):
    """Order laboratory tests."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    doctor = get_doctor()

    if request.method == 'POST':
        test_ids = request.form.getlist('test_ids[]')
        priority = request.form.get('priority', 'routine')
        notes = request.form.get('clinical_notes', '')

        if test_ids:
            order = LabOrder(
                order_number=f'LAB{datetime.now().strftime("%Y%m%d%H%M%S")}',
                patient_id=patient.id,
                doctor_id=doctor.id if doctor else 0,
                priority=priority,
                clinical_notes=notes,
                status='ordered'
            )
            db.session.add(order)
            db.session.flush()

            for test_id in test_ids:
                from models.laboratory import LabOrderItem
                item = LabOrderItem(
                    lab_order_id=order.id,
                    test_catalog_id=int(test_id),
                    status='pending'
                )
                db.session.add(item)

            db.session.commit()
            flash(f'Lab order {order.order_number} created successfully.', 'success')
            return redirect(url_for('doctor.patient_detail', patient_id=patient.id))
        else:
            flash('Please select at least one test.', 'warning')

    tests = LabTestCatalog.query.filter_by(is_active=True).order_by(LabTestCatalog.category, LabTestCatalog.name).all()
    return render_template('doctor/order_lab.html', patient=patient, tests=tests)


@doctor_bp.route('/patients/<int:patient_id>/order-imaging', methods=['GET', 'POST'])
@login_required
def order_imaging(patient_id):
    """Order radiology imaging."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    doctor = get_doctor()

    if request.method == 'POST':
        procedure_ids = request.form.getlist('procedure_ids[]')
        priority = request.form.get('priority', 'routine')
        indication = request.form.get('clinical_indication', '')

        if procedure_ids:
            order = RadiologyOrder(
                order_number=f'RAD{datetime.now().strftime("%Y%m%d%H%M%S")}',
                patient_id=patient.id,
                doctor_id=doctor.id if doctor else 0,
                priority=priority,
                clinical_indication=indication,
                status='ordered'
            )
            db.session.add(order)
            db.session.flush()

            for proc_id in procedure_ids:
                from models.radiology import RadiologyOrderItem
                item = RadiologyOrderItem(
                    radiology_order_id=order.id,
                    procedure_id=int(proc_id)
                )
                db.session.add(item)

            db.session.commit()
            flash(f'Imaging order {order.order_number} created successfully.', 'success')
            return redirect(url_for('doctor.patient_detail', patient_id=patient.id))
        else:
            flash('Please select at least one imaging procedure.', 'warning')

    procedures = ImagingProcedure.query.filter_by(is_active=True).order_by(
        ImagingProcedure.modality_id, ImagingProcedure.name).all()
    return render_template('doctor/order_imaging.html', patient=patient, procedures=procedures)


@doctor_bp.route('/medical-records')
@login_required
def medical_records():
    """List medical records."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))

    doctor = get_doctor()
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '')

    query = MedicalRecord.query.filter_by(is_deleted=False)
    if doctor:
        query = query.filter_by(doctor_id=doctor.id)

    if search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{search}%'),
                Patient.last_name.ilike(f'%{search}%'),
                MedicalRecord.chief_complaint.ilike(f'%{search}%')
            )
        )

    records = query.order_by(MedicalRecord.visit_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('doctor/medical_records.html', records=records, search=search)


@doctor_bp.route('/prescriptions')
@login_required
def prescriptions():
    """List prescriptions."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))

    doctor = get_doctor()
    page = request.args.get('page', 1, type=int)

    query = Prescription.query.filter_by(is_deleted=False)
    if doctor:
        query = query.filter_by(doctor_id=doctor.id)

    prescriptions = query.order_by(Prescription.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('doctor/prescriptions.html', prescriptions=prescriptions)


@doctor_bp.route('/appointments')
@login_required
def appointments():
    """Doctor's appointments."""
    if current_user.role != 'doctor':
        return redirect(url_for('main.index'))

    doctor = get_doctor()
    today = date.today()

    upcoming = []
    past = []
    if doctor:
        upcoming = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_date >= today,
            Appointment.is_deleted == False
        ).order_by(Appointment.scheduled_date, Appointment.scheduled_time).all()

        past = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_date < today,
            Appointment.is_deleted == False
        ).order_by(Appointment.scheduled_date.desc()).limit(20).all()

    return render_template('doctor/appointments.html', upcoming=upcoming, past=past)
