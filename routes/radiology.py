"""
iHIS - Radiology Routes
Radiology portal for imaging orders, studies, and reports.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.radiology import RadiologyOrder, RadiologyStudy, RadiologyImage, RadiologyReport, ImagingProcedure, ImagingModality

radiology_bp = Blueprint('radiology', __name__, template_folder='../templates/radiology')


@radiology_bp.route('/dashboard')
@login_required
def dashboard():
    """Radiology dashboard."""
    if current_user.role not in ['radiologist', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    pending_studies = RadiologyStudy.query.filter(
        RadiologyStudy.status.in_(['pending', 'acquired'])
    ).count()

    reporting_queue = RadiologyReport.query.filter_by(status='draft').count()
    critical_findings = RadiologyReport.query.filter_by(critical_findings=True, status='final').count()

    recent_orders = RadiologyOrder.query.filter_by(is_deleted=False).order_by(
        RadiologyOrder.ordered_at.desc()).limit(10).all()

    return render_template('radiology/dashboard.html',
                         pending_studies=pending_studies,
                         reporting_queue=reporting_queue,
                         critical_findings=critical_findings,
                         recent_orders=recent_orders)


@radiology_bp.route('/orders')
@login_required
def orders():
    """List imaging orders."""
    if current_user.role not in ['radiologist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')

    query = RadiologyOrder.query.filter_by(is_deleted=False)
    if status != 'all':
        query = query.filter_by(status=status)

    orders = query.order_by(RadiologyOrder.ordered_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('radiology/orders.html', orders=orders, status=status)


@radiology_bp.route('/studies')
@login_required
def studies():
    """List imaging studies."""
    if current_user.role not in ['radiologist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    studies = RadiologyStudy.query.order_by(RadiologyStudy.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('radiology/studies.html', studies=studies)


@radiology_bp.route('/study/<int:study_id>/report', methods=['GET', 'POST'])
@login_required
def write_report(study_id):
    """Write radiology report."""
    study = RadiologyStudy.query.get_or_404(study_id)

    if request.method == 'POST':
        report = RadiologyReport(
            report_number=f'RR{datetime.now().strftime("%Y%m%d%H%M%S")}',
            study_id=study.id,
            patient_id=study.patient_id,
            radiologist_id=current_user.id,
            clinical_history=request.form.get('clinical_history'),
            comparison=request.form.get('comparison'),
            technique=request.form.get('technique'),
            findings=request.form.get('findings'),
            impression=request.form.get('impression'),
            recommendations=request.form.get('recommendations'),
            critical_findings=bool(request.form.get('critical_findings')),
            status='final',
            signed_by=current_user.id,
            signed_at=datetime.now()
        )
        db.session.add(report)
        study.status = 'reported'
        db.session.commit()
        flash('Report submitted successfully.', 'success')
        return redirect(url_for('radiology.dashboard'))

    return render_template('radiology/write_report.html', study=study)


@radiology_bp.route('/procedures')
@login_required
def procedures():
    """List imaging procedures."""
    if current_user.role not in ['radiologist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    procedures = ImagingProcedure.query.filter_by(is_active=True).order_by(
        ImagingProcedure.name).all()
    return render_template('radiology/procedures.html', procedures=procedures)
