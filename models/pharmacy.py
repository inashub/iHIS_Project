"""
iHIS - Pharmacy Model
Dispensing, inventory, drug interactions, and refill management.
"""
from datetime import datetime
from extensions import db


class PharmacyInventory(db.Model):
    """Pharmacy inventory/stock tracking."""
    __tablename__ = 'pharmacy_inventory'

    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False, unique=True)
    batch_number = db.Column(db.String(50))
    supplier = db.Column(db.String(200))
    quantity_on_hand = db.Column(db.Float, default=0)
    quantity_reserved = db.Column(db.Float, default=0)  # For pending prescriptions
    quantity_available = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20))

    # Storage
    storage_location = db.Column(db.String(100))
    expiry_date = db.Column(db.Date)
    manufactured_date = db.Column(db.Date)

    # Stock control
    reorder_level = db.Column(db.Float, default=10)
    reorder_quantity = db.Column(db.Float, default=50)
    is_below_reorder = db.Column(db.Boolean, default=False)

    # Pricing
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)
    markup_percentage = db.Column(db.Float)

    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    medication = db.relationship('Medication', backref=db.backref('inventory', uselist=False))

    def __repr__(self):
        return f'<PharmacyInventory {self.medication_id}>'


class InventoryTransaction(db.Model):
    """Inventory transaction log (receipt, dispense, adjustment, return)."""
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('pharmacy_inventory.id'), nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False)
    # receipt, dispense, adjustment, return, waste, transfer_in, transfer_out
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    reference_type = db.Column(db.String(50))  # prescription, purchase_order, adjustment
    reference_id = db.Column(db.Integer)
    notes = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)

    inventory = db.relationship('PharmacyInventory', backref='transactions')
    performer = db.relationship('User')

    def __repr__(self):
        return f'<InventoryTransaction {self.transaction_type}>'


class DispensingRecord(db.Model):
    """Medication dispensing record."""
    __tablename__ = 'dispensing_records'

    id = db.Column(db.Integer, primary_key=True)
    dispensing_number = db.Column(db.String(20), unique=True, nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dispensed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # Pharmacist verification

    # Dispensing Details
    dispensed_at = db.Column(db.DateTime, default=datetime.utcnow)
    counseling_provided = db.Column(db.Boolean, default=False)
    counseling_notes = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='completed')  # pending, verified, completed, returned

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prescription = db.relationship('Prescription', backref='dispensing_records')
    patient = db.relationship('Patient')
    dispenser = db.relationship('User', foreign_keys=[dispensed_by])
    verifier = db.relationship('User', foreign_keys=[verified_by])
    items = db.relationship('DispensingItem', backref='dispensing_record', lazy='dynamic')

    def __repr__(self):
        return f'<DispensingRecord {self.dispensing_number}>'


class DispensingItem(db.Model):
    """Individual medication item dispensed."""
    __tablename__ = 'dispensing_items'

    id = db.Column(db.Integer, primary_key=True)
    dispensing_record_id = db.Column(db.Integer, db.ForeignKey('dispensing_records.id'), nullable=False)
    prescription_item_id = db.Column(db.Integer, db.ForeignKey('prescription_items.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey('pharmacy_inventory.id'))

    quantity_dispensed = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20))
    batch_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    label_instructions = db.Column(db.Text)

    medication = db.relationship('Medication')
    inventory = db.relationship('PharmacyInventory')

    def __repr__(self):
        return f'<DispensingItem {self.medication_id}>'


class DrugInteraction(db.Model):
    """Drug-drug interaction database."""
    __tablename__ = 'drug_interactions'

    id = db.Column(db.Integer, primary_key=True)
    drug1_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    drug2_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # minor, moderate, major, contraindicated
    mechanism = db.Column(db.Text)
    effect_description = db.Column(db.Text, nullable=False)
    clinical_management = db.Column(db.Text)
    evidence_level = db.Column(db.String(20))  # established, probable, suspected, possible
    references = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    drug1 = db.relationship('Medication', foreign_keys=[drug1_id], backref='interactions_as_drug1')
    drug2 = db.relationship('Medication', foreign_keys=[drug2_id], backref='interactions_as_drug2')

    def __repr__(self):
        return f'<DrugInteraction {self.drug1_id}-{self.drug2_id}>'


class RefillRequest(db.Model):
    """Medication refill request."""
    __tablename__ = 'refill_requests'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    requested_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    requested_quantity = db.Column(db.Float)
    reason = db.Column(db.Text)
    pickup_method = db.Column(db.String(20), default='pharmacy')  # pharmacy, delivery

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied, dispensed
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    denial_reason = db.Column(db.Text)

    prescription = db.relationship('Prescription', backref='refill_requests')
    patient = db.relationship('Patient')
    requester = db.relationship('User', foreign_keys=[requested_by])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<RefillRequest {self.id}>'


class Supplier(db.Model):
    """Pharmaceutical supplier/vendor."""
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    license_number = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Supplier {self.name}>'
