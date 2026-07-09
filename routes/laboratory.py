"""
iHIS - Laboratory Routes
Lab portal for test processing, result entry, and quality control.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.laboratory import LabOrder, LabOrderItem, LabTestCatalog, LabResult, QualityControl
from models.patient import Patient

laboratory_bp = Blueprint('laboratory', __name__, template_folder='../templates/laboratory')


@laboratory_bp.route('/dashboard')
@login_required
def dashboard():
    """Laboratory dashboard."""
    if current_user.role not in ['lab_tech', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    pending_orders = LabOrder.query.filter(
        LabOrder.status.in_(['ordered', 'collected', 'received']),
        LabOrder.is_deleted == False
    ).count()

    completed_today = LabOrder.query.filter(
        LabOrder.status == 'completed',
        db.func.date(LabOrder.completed_at) == datetime.now().date(),
        LabOrder.is_deleted == False
    ).count()

    critical_values = LabResult.query.filter_by(is_critical=True, verified=False).count()

    pending_orders_list = LabOrder.query.filter(
        LabOrder.status.in_(['ordered', 'collected', 'received']),
        LabOrder.is_deleted == False
    ).order_by(LabOrder.ordered_at.desc()).limit(10).all()

    return render_template('laboratory/dashboard.html',
                         pending_orders=pending_orders,
                         completed_today=completed_today,
                         critical_values=critical_values,
                         pending_orders_list=pending_orders_list)


@laboratory_bp.route('/orders')
@login_required
def orders():
    """List lab orders."""
    if current_user.role not in ['lab_tech', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    status = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)

    query = LabOrder.query.filter_by(is_deleted=False)
    if status != 'all':
        query = query.filter_by(status=status)

    orders = query.order_by(LabOrder.ordered_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('laboratory/orders.html', orders=orders, status=status)


@laboratory_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """View lab order details."""
    order = LabOrder.query.filter_by(id=order_id, is_deleted=False).first_or_404()
    return render_template('laboratory/order_detail.html', order=order)


@laboratory_bp.route('/order/<int:order_id>/process', methods=['POST'])
@login_required
def process_order(order_id):
    """Process lab order - update status."""
    order = LabOrder.query.filter_by(id=order_id, is_deleted=False).first_or_404()
    new_status = request.form.get('status')
    if new_status in ['collected', 'received', 'processing', 'completed', 'rejected']:
        order.status = new_status
        if new_status == 'processing':
            order.processing_started_at = datetime.now()
        elif new_status == 'completed':
            order.completed_at = datetime.now()
        db.session.commit()
        flash(f'Order status updated to {new_status}.', 'success')
    return redirect(url_for('laboratory.order_detail', order_id=order.id))


@laboratory_bp.route('/order/<int:order_id>/enter-results', methods=['GET', 'POST'])
@login_required
def enter_results(order_id):
    """Enter lab results."""
    order = LabOrder.query.filter_by(id=order_id, is_deleted=False).first_or_404()

    if request.method == 'POST':
        for item in order.items:
            if item.status == 'pending':
                result_value = request.form.get(f'result_{item.id}')
                if result_value:
                    result = LabResult(
                        lab_order_id=order.id,
                        patient_id=order.patient_id,
                        parameter_id=item.test_catalog.parameters[0].id if item.test_catalog.parameters else None,
                        value_text=result_value,
                        unit=item.test_catalog.parameters[0].unit if item.test_catalog.parameters else None,
                        reference_range=item.test_catalog.parameters[0].reference_range_text if item.test_catalog.parameters else None,
                        is_abnormal=False  # Would be calculated based on reference range
                    )
                    db.session.add(result)
                    item.status = 'completed'
                    item.result = result_value

        # Check if all items completed
        if all(item.status == 'completed' for item in order.items):
            order.status = 'completed'
            order.completed_at = datetime.now()

        db.session.commit()
        flash('Results entered successfully.', 'success')
        return redirect(url_for('laboratory.order_detail', order_id=order.id))

    return render_template('laboratory/enter_results.html', order=order)


@laboratory_bp.route('/test-catalog')
@login_required
def test_catalog():
    """View lab test catalog."""
    if current_user.role not in ['lab_tech', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)

    query = LabTestCatalog.query.filter_by(is_active=True)
    if category != 'all':
        query = query.filter_by(category=category)

    tests = query.order_by(LabTestCatalog.name).paginate(
        page=page, per_page=20, error_out=False)

    categories = db.session.query(LabTestCatalog.category).distinct().all()
    return render_template('laboratory/test_catalog.html',
                         tests=tests,
                         categories=[c[0] for c in categories],
                         current_category=category)


@laboratory_bp.route('/quality-control')
@login_required
def quality_control():
    """Quality control dashboard."""
    if current_user.role not in ['lab_tech', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    recent_qc = QualityControl.query.order_by(QualityControl.performed_at.desc()).limit(20).all()
    return render_template('laboratory/quality_control.html', quality_controls=recent_qc)
