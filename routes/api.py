"""
iHIS - API Routes
RESTful API endpoints for external integration.
"""
from datetime import datetime, date
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from extensions import db

api_bp = Blueprint('api', __name__, url_prefix='/api')


def api_auth_required(f):
    """Decorator for API authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


@api_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@api_bp.route('/dashboard-stats')
@api_auth_required
def dashboard_stats():
    """Get dashboard statistics based on user role."""
    from models.patient import Patient
    from models.doctor import Appointment
    from models.medical_record import MedicalRecord, Prescription
    from models.laboratory import LabOrder
    from models.radiology import RadiologyOrder

    stats = {}
    today = date.today()

    if current_user.role == 'patient':
        patient = Patient.query.filter_by(user_id=current_user.id).first()
        if patient:
            stats['upcoming_appointments'] = Appointment.query.filter(
                Appointment.patient_id == patient.id,
                Appointment.scheduled_date >= today
            ).count()
            stats['active_prescriptions'] = Prescription.query.filter(
                Prescription.patient_id == patient.id,
                Prescription.status == 'active'
            ).count()
    elif current_user.role == 'doctor':
        from models.doctor import Doctor
        doctor = Doctor.query.filter_by(user_id=current_user.id).first()
        if doctor:
            stats['today_appointments'] = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.scheduled_date == today
            ).count()
            stats['total_patients'] = Patient.query.filter_by(is_deleted=False).count()
            stats['pending_reports'] = MedicalRecord.query.filter(
                MedicalRecord.doctor_id == doctor.id,
                MedicalRecord.status == 'active'
            ).count()
    else:
        stats['total_patients'] = Patient.query.filter_by(is_deleted=False).count()
        stats['today_appointments'] = Appointment.query.filter(
            Appointment.scheduled_date == today
        ).count()

    return jsonify(stats)


@api_bp.route('/patients')
@api_auth_required
def get_patients():
    """Get patients list."""
    from models.patient import Patient

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
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

    patients = query.order_by(Patient.last_name).paginate(
        page=page, per_page=per_page, error_out=False)

    return jsonify({
        'patients': [{
            'id': p.id,
            'patient_id': p.patient_id,
            'name': p.get_full_name(),
            'age': p.get_age(),
            'gender': p.gender,
            'blood_type': p.blood_type,
            'phone': p.phone_primary
        } for p in patients.items],
        'total': patients.total,
        'pages': patients.pages,
        'current_page': patients.page
    })


@api_bp.route('/patient/<int:patient_id>')
@api_auth_required
def get_patient(patient_id):
    """Get patient details."""
    from models.patient import Patient, Allergy, ChronicDisease

    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()
    allergies = Allergy.query.filter_by(patient_id=patient.id).all()
    conditions = ChronicDisease.query.filter_by(patient_id=patient.id).all()

    return jsonify({
        'id': patient.id,
        'patient_id': patient.patient_id,
        'name': patient.get_full_name(),
        'age': patient.get_age(),
        'gender': patient.gender,
        'blood_type': patient.blood_type,
        'phone': patient.phone_primary,
        'email': patient.email,
        'allergies': [{'allergen': a.allergen, 'severity': a.severity} for a in allergies],
        'conditions': [{'condition': c.condition, 'status': c.status} for c in conditions]
    })


@api_bp.route('/appointments')
@api_auth_required
def get_appointments():
    """Get appointments."""
    from models.doctor import Appointment

    date_filter = request.args.get('date', date.today().isoformat())
    status = request.args.get('status')

    query = Appointment.query.filter_by(is_deleted=False)
    if date_filter:
        query = query.filter(Appointment.scheduled_date == date_filter)
    if status:
        query = query.filter_by(status=status)

    appointments = query.order_by(Appointment.scheduled_time).all()

    return jsonify({
        'appointments': [{
            'id': a.id,
            'number': a.appointment_number,
            'patient': a.patient.get_full_name() if a.patient else None,
            'doctor': a.doctor.get_full_name() if a.doctor else None,
            'date': a.scheduled_date.isoformat(),
            'time': a.scheduled_time.isoformat(),
            'type': a.appointment_type,
            'status': a.status
        } for a in appointments]
    })


@api_bp.route('/lab-tests')
@api_auth_required
def get_lab_tests():
    """Get lab test catalog."""
    from models.laboratory import LabTestCatalog

    category = request.args.get('category')
    query = LabTestCatalog.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)

    tests = query.order_by(LabTestCatalog.name).all()
    return jsonify({
        'tests': [{
            'id': t.id,
            'code': t.code,
            'name': t.name,
            'category': t.category,
            'specimen': t.specimen_type,
            'tat_hours': t.turnaround_time_hours,
            'cost': t.cost
        } for t in tests]
    })


@api_bp.route('/medications')
@api_auth_required
def get_medications():
    """Get medication catalog."""
    from models.medical_record import Medication

    search = request.args.get('q', '')
    query = Medication.query.filter_by(is_active=True)
    if search:
        query = query.filter(
            db.or_(
                Medication.name.ilike(f'%{search}%'),
                Medication.generic_name.ilike(f'%{search}%')
            )
        )

    medications = query.order_by(Medication.name).limit(50).all()
    return jsonify({
        'medications': [{
            'id': m.id,
            'name': m.name,
            'generic': m.generic_name,
            'form': m.form,
            'strength': m.strength,
            'drug_class': m.drug_class,
            'stock': m.stock_quantity
        } for m in medications]
    })


@api_bp.route('/notifications')
@api_auth_required
def get_notifications():
    """Get user notifications."""
    from models.user import Notification

    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(10).all()

    return jsonify({
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
    })


@api_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@api_auth_required
def mark_notification_read(notification_id):
    """Mark notification as read."""
    from models.user import Notification

    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    if notification:
        notification.mark_as_read()
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Notification not found'}), 404
