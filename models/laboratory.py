"""
iHIS - Laboratory Model
Lab orders, test management, results, and reporting.
"""
from datetime import datetime
from extensions import db


class LabTestCatalog(db.Model):
    """Catalog of available laboratory tests."""
    __tablename__ = 'lab_test_catalog'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    # hematology, biochemistry, microbiology, immunology, pathology, endocrinology, coagulation, toxicology
    description = db.Column(db.Text)
    specimen_type = db.Column(db.String(100))  # blood, urine, stool, swab, tissue, csf
    specimen_volume = db.Column(db.String(50))
    container_type = db.Column(db.String(50))
    turnaround_time_hours = db.Column(db.Integer)  # Expected TAT
    is_stat_available = db.Column(db.Boolean, default=True)
    cost = db.Column(db.Float)
    cpt_code = db.Column(db.String(20))
    loinc_code = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    parameters = db.relationship('LabTestParameter', backref='test_catalog', lazy='dynamic')

    def __repr__(self):
        return f'<LabTestCatalog {self.name}>'


class LabTestParameter(db.Model):
    """Individual parameters/components of a lab test."""
    __tablename__ = 'lab_test_parameters'

    id = db.Column(db.Integer, primary_key=True)
    test_catalog_id = db.Column(db.Integer, db.ForeignKey('lab_test_catalog.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(50))
    reference_range_low = db.Column(db.Float)
    reference_range_high = db.Column(db.Float)
    reference_range_text = db.Column(db.String(255))
    is_critical_low = db.Column(db.Float)  # Panic value low
    is_critical_high = db.Column(db.Float)  # Panic value high
    data_type = db.Column(db.String(20), default='numeric')  # numeric, text, enumerated
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<LabTestParameter {self.name}>'


class LabOrder(db.Model):
    """Laboratory order/request."""
    __tablename__ = 'lab_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)

    # Order Details
    priority = db.Column(db.String(20), default='routine')  # routine, urgent, stat
    clinical_notes = db.Column(db.Text)
    diagnosis_notes = db.Column(db.Text)

    # Status
    status = db.Column(db.String(30), default='ordered')
    # ordered, collected, received, processing, completed, cancelled, rejected
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)
    collected_at = db.Column(db.DateTime)
    received_at = db.Column(db.DateTime)
    processing_started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Sample Information
    sample_type = db.Column(db.String(100))
    sample_collected_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    sample_received_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    sample_condition = db.Column(db.String(50))  # acceptable, hemolyzed, clotted, insufficient, etc.
    sample_rejection_reason = db.Column(db.Text)

    # Billing
    billing_status = db.Column(db.String(20), default='pending')

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    collector = db.relationship('User', foreign_keys=[sample_collected_by])
    receiver = db.relationship('User', foreign_keys=[sample_received_by])
    items = db.relationship('LabOrderItem', backref='lab_order', lazy='dynamic')

    def __repr__(self):
        return f'<LabOrder {self.order_number}>'


class LabOrderItem(db.Model):
    """Individual test item within a lab order."""
    __tablename__ = 'lab_order_items'

    id = db.Column(db.Integer, primary_key=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey('lab_orders.id'), nullable=False)
    test_catalog_id = db.Column(db.Integer, db.ForeignKey('lab_test_catalog.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    result = db.Column(db.Text)  # JSON or text result
    is_abnormal = db.Column(db.Boolean, default=False)
    is_critical = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    test_catalog = db.relationship('LabTestCatalog')
    verifier = db.relationship('User')

    def __repr__(self):
        return f'<LabOrderItem {self.test_catalog_id}>'


class LabResult(db.Model):
    """Individual lab result value."""
    __tablename__ = 'lab_results'

    id = db.Column(db.Integer, primary_key=True)
    lab_order_id = db.Column(db.Integer, db.ForeignKey('lab_orders.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    parameter_id = db.Column(db.Integer, db.ForeignKey('lab_test_parameters.id'), nullable=False)

    value_numeric = db.Column(db.Float)
    value_text = db.Column(db.Text)
    unit = db.Column(db.String(50))
    reference_range = db.Column(db.String(100))

    # Interpretation
    is_abnormal = db.Column(db.Boolean, default=False)
    is_critical = db.Column(db.Boolean, default=False)
    flag = db.Column(db.String(10))  # H=High, L=Low, C=Critical, N=Normal
    interpretation = db.Column(db.Text)

    # Verification
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)

    # Method & Instrument
    method = db.Column(db.String(100))
    instrument = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lab_order = db.relationship('LabOrder', backref='results')
    patient = db.relationship('Patient')
    parameter = db.relationship('LabTestParameter')
    verifier = db.relationship('User')

    def __repr__(self):
        return f'<LabResult {self.parameter_id}={self.value_numeric or self.value_text}>'


class QualityControl(db.Model):
    """Quality control tracking for lab instruments."""
    __tablename__ = 'quality_controls'

    id = db.Column(db.Integer, primary_key=True)
    test_parameter_id = db.Column(db.Integer, db.ForeignKey('lab_test_parameters.id'))
    instrument = db.Column(db.String(100), nullable=False)
    lot_number = db.Column(db.String(50), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # low, normal, high
    expected_value = db.Column(db.Float, nullable=False)
    observed_value = db.Column(db.Float, nullable=False)
    is_within_range = db.Column(db.Boolean, nullable=False)
    deviation = db.Column(db.Float)
    action_taken = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    performed_at = db.Column(db.DateTime, default=datetime.utcnow)

    performer = db.relationship('User')

    def __repr__(self):
        return f'<QualityControl {self.instrument}>'
