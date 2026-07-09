"""
iHIS - Radiology Model
Imaging orders, studies, reports, and DICOM-ready structure.
"""
from datetime import datetime
from extensions import db


class ImagingModality(db.Model):
    """Imaging modality catalog (X-Ray, CT, MRI, etc.)."""
    __tablename__ = 'imaging_modalities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # X-Ray, CT, MRI, Ultrasound, etc.
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    dicom_modality_code = db.Column(db.String(10))  # DX, CT, MR, US, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ImagingModality {self.name}>'


class ImagingProcedure(db.Model):
    """Specific imaging procedures/exams."""
    __tablename__ = 'imaging_procedures'

    id = db.Column(db.Integer, primary_key=True)
    modality_id = db.Column(db.Integer, db.ForeignKey('imaging_modalities.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True)
    cpt_code = db.Column(db.String(20))
    description = db.Column(db.Text)
    body_part = db.Column(db.String(100))
    contrast_required = db.Column(db.Boolean, default=False)
    contrast_agent = db.Column(db.String(200))
    preparation_instructions = db.Column(db.Text)
    estimated_duration_minutes = db.Column(db.Integer)
    cost = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    modality = db.relationship('ImagingModality', backref='procedures')

    def __repr__(self):
        return f'<ImagingProcedure {self.name}>'


class RadiologyOrder(db.Model):
    """Radiology imaging order/request."""
    __tablename__ = 'radiology_orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)

    # Order Details
    priority = db.Column(db.String(20), default='routine')  # routine, urgent, stat
    clinical_indication = db.Column(db.Text, nullable=False)
    relevant_history = db.Column(db.Text)
    comparison_study = db.Column(db.String(255))  # Previous study to compare with

    # Status
    status = db.Column(db.String(30), default='ordered')
    # ordered, scheduled, in_progress, completed, cancelled, reviewed
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)
    scheduled_at = db.Column(db.DateTime)
    performed_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Scheduling
    scheduled_date = db.Column(db.Date)
    scheduled_time = db.Column(db.Time)
    room = db.Column(db.String(50))

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    items = db.relationship('RadiologyOrderItem', backref='radiology_order', lazy='dynamic')
    studies = db.relationship('RadiologyStudy', backref='order', lazy='dynamic')

    def __repr__(self):
        return f'<RadiologyOrder {self.order_number}>'


class RadiologyOrderItem(db.Model):
    """Individual imaging procedure within an order."""
    __tablename__ = 'radiology_order_items'

    id = db.Column(db.Integer, primary_key=True)
    radiology_order_id = db.Column(db.Integer, db.ForeignKey('radiology_orders.id'), nullable=False)
    procedure_id = db.Column(db.Integer, db.ForeignKey('imaging_procedures.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    procedure = db.relationship('ImagingProcedure')

    def __repr__(self):
        return f'<RadiologyOrderItem {self.procedure_id}>'


class RadiologyStudy(db.Model):
    """Radiology study/exam performed."""
    __tablename__ = 'radiology_studies'

    id = db.Column(db.Integer, primary_key=True)
    study_instance_uid = db.Column(db.String(100), unique=True)  # DICOM Study Instance UID
    order_id = db.Column(db.Integer, db.ForeignKey('radiology_orders.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    procedure_id = db.Column(db.Integer, db.ForeignKey('imaging_procedures.id'), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Study Details
    study_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    body_part_examined = db.Column(db.String(100))
    contrast_used = db.Column(db.Boolean, default=False)
    contrast_agent = db.Column(db.String(200))
    exposure_time = db.Column(db.Float)  # seconds
    kv = db.Column(db.Float)  # kilovoltage
    mas = db.Column(db.Float)  # milliampere-seconds

    # DICOM
    dicom_study_uid = db.Column(db.String(100))
    dicom_accession_number = db.Column(db.String(50))
    number_of_series = db.Column(db.Integer, default=0)
    number_of_images = db.Column(db.Integer, default=0)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, acquired, reported
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='radiology_studies')
    procedure = db.relationship('ImagingProcedure')
    technician = db.relationship('User')
    images = db.relationship('RadiologyImage', backref='study', lazy='dynamic')
    report = db.relationship('RadiologyReport', backref='study', uselist=False)

    def __repr__(self):
        return f'<RadiologyStudy {self.id}>'


class RadiologyImage(db.Model):
    """Individual radiology image/DICOM instance."""
    __tablename__ = 'radiology_images'

    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('radiology_studies.id'), nullable=False)
    series_instance_uid = db.Column(db.String(100))
    sop_instance_uid = db.Column(db.String(100), unique=True)
    instance_number = db.Column(db.Integer)
    series_number = db.Column(db.Integer)
    series_description = db.Column(db.String(255))

    # File
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    thumbnail_path = db.Column(db.String(255))

    # DICOM Tags
    image_type = db.Column(db.String(50))
    rows = db.Column(db.Integer)
    columns = db.Column(db.Integer)
    photometric_interpretation = db.Column(db.String(50))
    pixel_spacing = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<RadiologyImage {self.id}>'


class RadiologyReport(db.Model):
    """Radiology report with findings and impressions."""
    __tablename__ = 'radiology_reports'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(20), unique=True, nullable=False)
    study_id = db.Column(db.Integer, db.ForeignKey('radiology_studies.id'), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    radiologist_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    # Report Content
    clinical_history = db.Column(db.Text)
    comparison = db.Column(db.Text)
    technique = db.Column(db.Text)
    findings = db.Column(db.Text, nullable=False)
    impression = db.Column(db.Text, nullable=False)
    recommendations = db.Column(db.Text)
    critical_findings = db.Column(db.Boolean, default=False)

    # Status
    status = db.Column(db.String(20), default='draft')  # draft, preliminary, final, amended
    is_urgent = db.Column(db.Boolean, default=False)
    communicated_to_clinician = db.Column(db.Boolean, default=False)
    communicated_at = db.Column(db.DateTime)

    # Sign-off
    digital_signature = db.Column(db.Text)
    signed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    signed_at = db.Column(db.DateTime)

    # Amendment
    amended_from = db.Column(db.Integer, db.ForeignKey('radiology_reports.id'))
    amendment_reason = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    patient = db.relationship('Patient')
    radiologist = db.relationship('Doctor')
    signer = db.relationship('User')

    def __repr__(self):
        return f'<RadiologyReport {self.report_number}>'
