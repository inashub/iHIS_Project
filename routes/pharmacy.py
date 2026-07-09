"""
iHIS - Pharmacy Routes
Pharmacy portal for dispensing, inventory, and drug interactions.
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.pharmacy import PharmacyInventory, DispensingRecord, DispensingItem, RefillRequest, DrugInteraction
from models.medical_record import Prescription, PrescriptionItem, Medication

pharmacy_bp = Blueprint('pharmacy', __name__, template_folder='../templates/pharmacy')


@pharmacy_bp.route('/dashboard')
@login_required
def dashboard():
    """Pharmacy dashboard."""
    if current_user.role not in ['pharmacist', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    pending_prescriptions = Prescription.query.filter(
        Prescription.status == 'active',
        Prescription.is_deleted == False
    ).count()

    low_stock = PharmacyInventory.query.filter(
        PharmacyInventory.quantity_available <= PharmacyInventory.reorder_level,
        PharmacyInventory.is_active == True
    ).count()

    dispensed_today = DispensingRecord.query.filter(
        db.func.date(DispensingRecord.dispensed_at) == datetime.now().date()
    ).count()

    pending_rx = Prescription.query.filter(
        Prescription.status == 'active',
        Prescription.is_deleted == False
    ).order_by(Prescription.created_at.desc()).limit(10).all()

    low_stock_items = PharmacyInventory.query.filter(
        PharmacyInventory.quantity_available <= PharmacyInventory.reorder_level,
        PharmacyInventory.is_active == True
    ).order_by(PharmacyInventory.quantity_available).limit(10).all()

    return render_template('pharmacy/dashboard.html',
                         pending_prescriptions=pending_prescriptions,
                         low_stock=low_stock,
                         dispensed_today=dispensed_today,
                         pending_rx=pending_rx,
                         low_stock_items=low_stock_items)


@pharmacy_bp.route('/prescriptions')
@login_required
def prescriptions():
    """List pending prescriptions."""
    if current_user.role not in ['pharmacist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    prescriptions = Prescription.query.filter_by(is_deleted=False).order_by(
        Prescription.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('pharmacy/prescriptions.html', prescriptions=prescriptions)


@pharmacy_bp.route('/prescription/<int:prescription_id>/dispense', methods=['GET', 'POST'])
@login_required
def dispense(prescription_id):
    """Dispense prescription."""
    prescription = Prescription.query.filter_by(id=prescription_id, is_deleted=False).first_or_404()

    if request.method == 'POST':
        dispensing = DispensingRecord(
            dispensing_number=f'DSP{datetime.now().strftime("%Y%m%d%H%M%S")}',
            prescription_id=prescription.id,
            patient_id=prescription.patient_id,
            dispensed_by=current_user.id,
            verified_by=current_user.id,
            status='completed'
        )
        db.session.add(dispensing)
        db.session.flush()

        for item in prescription.items:
            dispensed_qty = request.form.get(f'qty_{item.id}', item.quantity or 1)
            disp_item = DispensingItem(
                dispensing_record_id=dispensing.id,
                prescription_item_id=item.id,
                medication_id=item.medication_id,
                quantity_dispensed=float(dispensed_qty) if dispensed_qty else 0,
                label_instructions=item.special_instructions or ''
            )
            db.session.add(disp_item)
            item.is_dispensed = True

        prescription.status = 'dispensed'
        prescription.is_dispensed = True
        prescription.dispensed_at = datetime.now()
        prescription.dispensed_by = current_user.id
        db.session.commit()

        flash('Prescription dispensed successfully.', 'success')
        return redirect(url_for('pharmacy.dashboard'))

    return render_template('pharmacy/dispense.html', prescription=prescription)


@pharmacy_bp.route('/inventory')
@login_required
def inventory():
    """Pharmacy inventory."""
    if current_user.role not in ['pharmacist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    inventory = PharmacyInventory.query.order_by(
        PharmacyInventory.quantity_available).paginate(page=page, per_page=20, error_out=False)
    return render_template('pharmacy/inventory.html', inventory=inventory)


@pharmacy_bp.route('/refills')
@login_required
def refills():
    """List refill requests."""
    if current_user.role not in ['pharmacist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    refills = RefillRequest.query.order_by(RefillRequest.request_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('pharmacy/refills.html', refills=refills)
