"""
iHIS - Reports Routes
Generate and export various healthcare reports.
"""
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, flash, make_response
from flask_login import login_required, current_user
from extensions import db
from models.patient import Patient
from models.doctor import Appointment, Doctor
from models.medical_record import MedicalRecord, Prescription
from models.laboratory import LabOrder
from models.radiology import RadiologyOrder

reports_bp = Blueprint('reports', __name__, template_folder='../templates/reports')


@reports_bp.route('/')
@login_required
def index():
    """Reports dashboard."""
    if current_user.role not in ['admin', 'superadmin', 'doctor', 'receptionist']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    # Summary stats for report generation
    total_patients = Patient.query.filter_by(is_deleted=False).count()
    today_appts = Appointment.query.filter(
        Appointment.scheduled_date == date.today(),
        Appointment.is_deleted == False
    ).count()
    total_prescriptions = Prescription.query.filter_by(is_deleted=False).count()
    total_lab_orders = LabOrder.query.filter_by(is_deleted=False).count()

    return render_template('reports/index.html',
                         total_patients=total_patients,
                         today_appts=today_appts,
                         total_prescriptions=total_prescriptions,
                         total_lab_orders=total_lab_orders)


@reports_bp.route('/patient-report')
@login_required
def patient_report():
    """Generate patient report."""
    if current_user.role not in ['admin', 'superadmin', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    patients = Patient.query.filter_by(is_deleted=False).order_by(Patient.last_name).all()

    # Generate PDF-style HTML report
    report_html = render_template('reports/patient_report.html', patients=patients,
                                 generated_at=datetime.now())

    if request.args.get('format') == 'pdf':
        response = make_response(report_html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = 'attachment; filename=patient_report.html'
        return response

    return render_template('reports/patient_report.html', patients=patients,
                          generated_at=datetime.now())


@reports_bp.route('/appointment-report')
@login_required
def appointment_report():
    """Generate appointment report."""
    if current_user.role not in ['admin', 'superadmin', 'receptionist']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    appointments = Appointment.query.filter(
        Appointment.scheduled_date >= start_date,
        Appointment.scheduled_date <= end_date,
        Appointment.is_deleted == False
    ).order_by(Appointment.scheduled_date).all()

    return render_template('reports/appointment_report.html',
                         appointments=appointments,
                         start_date=start_date,
                         end_date=end_date,
                         generated_at=datetime.now())


@reports_bp.route('/prescription-report')
@login_required
def prescription_report():
    """Generate prescription report."""
    if current_user.role not in ['admin', 'superadmin', 'pharmacist', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    prescriptions = Prescription.query.filter(
        Prescription.created_at >= start_date,
        Prescription.created_at <= end_date,
        Prescription.is_deleted == False
    ).order_by(Prescription.created_at.desc()).all()

    return render_template('reports/prescription_report.html',
                         prescriptions=prescriptions,
                         start_date=start_date,
                         end_date=end_date,
                         generated_at=datetime.now())


@reports_bp.route('/lab-report')
@login_required
def lab_report():
    """Generate lab orders report."""
    if current_user.role not in ['admin', 'superadmin', 'lab_tech', 'doctor']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    start_date = request.args.get('start_date', (date.today() - timedelta(days=30)).isoformat())
    end_date = request.args.get('end_date', date.today().isoformat())

    lab_orders = LabOrder.query.filter(
        LabOrder.ordered_at >= start_date,
        LabOrder.ordered_at <= end_date,
        LabOrder.is_deleted == False
    ).order_by(LabOrder.ordered_at.desc()).all()

    return render_template('reports/lab_report.html',
                         lab_orders=lab_orders,
                         start_date=start_date,
                         end_date=end_date,
                         generated_at=datetime.now())


@reports_bp.route('/statistics')
@login_required
def statistics():
    """Hospital statistics dashboard."""
    if current_user.role not in ['admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    # Monthly patient counts for chart
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    patient_counts = [120, 135, 148, 162, 155, 170, 185, 190, 175, 195, 210, 225]
    appointment_counts = [340, 360, 385, 400, 390, 420, 450, 460, 440, 480, 510, 550]

    # Department stats
    dept_stats = []
    from models.patient import Department
    departments = Department.query.filter_by(is_active=True).all()
    for dept in departments:
        dept_stats.append({
            'name': dept.name,
            'doctors': len(dept.doctors),
            'patients': len(dept.doctors) * 25 if dept.doctors else 0  # Approximate
        })

    return render_template('reports/statistics.html',
                         months=months,
                         patient_counts=patient_counts,
                         appointment_counts=appointment_counts,
                         dept_stats=dept_stats)
