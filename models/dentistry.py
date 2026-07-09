"""
iHIS - Dentistry Model
Dental records, charting, procedures, and orthodontic tracking.
"""
from datetime import datetime
from extensions import db


class DentalSpecialty(db.Model):
    """Dental specialty catalog."""
    __tablename__ = 'dental_specialties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DentalSpecialty {self.name}>'


class Dentist(db.Model):
    """Dentist model - extends doctor for dental practice."""
    __tablename__ = 'dentists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), unique=True, nullable=True)
    dental_license = db.Column(db.String(50), unique=True)
    dental_specialty_id = db.Column(db.Integer, db.ForeignKey('dental_specialties.id'))

    # Status
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('dentist_profile', uselist=False))
    specialty = db.relationship('DentalSpecialty', backref='dentists')

    def get_full_name(self):
        return self.user.get_full_name() if self.user else 'Unknown'

    def __repr__(self):
        return f'<Dentist {self.get_full_name()}>'


class DentalRecord(db.Model):
    """Patient dental record."""
    __tablename__ = 'dental_records'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dentist_id = db.Column(db.Integer, db.ForeignKey('dentists.id'))

    # Dental History
    dental_history = db.Column(db.Text)
    dental_allergies = db.Column(db.Text)
    previous_procedures = db.Column(db.Text)
    habits = db.Column(db.Text)  # smoking, grinding, etc.
    hygiene_assessment = db.Column(db.Text)

    # Examination
    occlusion = db.Column(db.String(50))  # class_i, class_ii, class_iii
    oral_hygiene_status = db.Column(db.String(50))  # good, fair, poor
    gingival_status = db.Column(db.String(50))
    plaque_index = db.Column(db.Float)
    calculus_index = db.Column(db.Float)

    # Charting Numbering System
    numbering_system = db.Column(db.String(20), default='universal')  # universal, fdi, palmer

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tooth_records = db.relationship('ToothRecord', backref='dental_record', lazy='dynamic')
    chartings = db.relationship('DentalCharting', backref='dental_record', lazy='dynamic')
    procedures = db.relationship('DentalProcedure', backref='dental_record', lazy='dynamic')
    images = db.relationship('DentalImage', backref='dental_record', lazy='dynamic')
    orthodontic_cases = db.relationship('OrthodonticCase', backref='dental_record', lazy='dynamic')

    def __repr__(self):
        return f'<DentalRecord Patient:{self.patient_id}>'


class ToothRecord(db.Model):
    """Individual tooth status record."""
    __tablename__ = 'tooth_records'

    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    tooth_number = db.Column(db.Integer, nullable=False)  # 1-32 for universal, 11-48 for FDI

    # Tooth Status
    is_present = db.Column(db.Boolean, default=True)
    condition = db.Column(db.String(50))  # healthy, caries, filled, crowned, missing, etc.
    notes = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ToothRecord #{self.tooth_number}>'


class DentalCharting(db.Model):
    """Detailed dental charting entry."""
    __tablename__ = 'dental_charts'

    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dentist_id = db.Column(db.Integer, db.ForeignKey('dentists.id'), nullable=False)
    charting_date = db.Column(db.DateTime, default=datetime.utcnow)

    tooth_number = db.Column(db.Integer, nullable=False)
    surface = db.Column(db.String(20))  # mesial, distal, occlusal, buccal, lingual, incisal, root
    condition = db.Column(db.String(50), nullable=False)
    # healthy, caries, filling_amalgam, filling_composite, crown, bridge,
    # implant, root_canal, extraction, missing, abscess, fracture, erosion, abrasion

    treatment_needed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')
    dentist = db.relationship('Dentist')

    def __repr__(self):
        return f'<DentalCharting Tooth:{self.tooth_number} {self.condition}>'


class DentalProcedure(db.Model):
    """Dental procedure performed."""
    __tablename__ = 'dental_procedures'

    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dentist_id = db.Column(db.Integer, db.ForeignKey('dentists.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))

    # Procedure Details
    procedure_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    procedure_type = db.Column(db.String(50), nullable=False)
    # examination, cleaning, filling, root_canal, extraction, crown, bridge,
    # implant, scaling, orthodontics, surgery, bleaching, veneer, denture

    teeth_treated = db.Column(db.String(100))  # Comma-separated tooth numbers
    surfaces = db.Column(db.String(50))
    procedure_code = db.Column(db.String(20))  # CDT/ADA code
    description = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)

    # Materials Used
    materials = db.Column(db.Text)
    anesthesia_used = db.Column(db.String(100))

    # Outcome
    outcome = db.Column(db.String(50), default='successful')  # successful, partial, failed, pending_review
    complications = db.Column(db.Text)
    post_op_instructions = db.Column(db.Text)

    # Follow-up
    follow_up_needed = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.Date)

    # Consent
    consent_obtained = db.Column(db.Boolean, default=False)
    consent_document = db.Column(db.String(255))

    # Fees
    fee = db.Column(db.Float)
    insurance_claim_status = db.Column(db.String(20), default='pending')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='dental_procedures')
    dentist = db.relationship('Dentist', backref='procedures')

    def __repr__(self):
        return f'<DentalProcedure {self.procedure_type}>'


class DentalImage(db.Model):
    """Dental imaging (X-rays, photos, 3D scans)."""
    __tablename__ = 'dental_images'

    id = db.Column(db.Integer, primary_key=True)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

    image_type = db.Column(db.String(50), nullable=False)
    # periapical, bitewing, panoramic, cbct, intraoral_photo, extraoral_photo, 3d_scan

    tooth_number = db.Column(db.Integer)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    thumbnail_path = db.Column(db.String(255))
    taken_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')

    def __repr__(self):
        return f'<DentalImage {self.image_type}>'


class OrthodonticCase(db.Model):
    """Orthodontic case tracking."""
    __tablename__ = 'orthodontic_cases'

    id = db.Column(db.Integer, primary_key=True)
    case_number = db.Column(db.String(20), unique=True, nullable=False)
    dental_record_id = db.Column(db.Integer, db.ForeignKey('dental_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    orthodontist_id = db.Column(db.Integer, db.ForeignKey('dentists.id'), nullable=False)

    # Case Details
    case_type = db.Column(db.String(50))  # braces, aligners, retainer, expander, other
    start_date = db.Column(db.Date, nullable=False)
    estimated_end_date = db.Column(db.Date)
    actual_end_date = db.Column(db.Date)

    # Diagnosis
    malocclusion_class = db.Column(db.String(50))  # class_i, class_ii_div1, class_ii_div2, class_iii
    skeletal_pattern = db.Column(db.String(50))
    crowding = db.Column(db.String(20))  # mild, moderate, severe
    spacing = db.Column(db.String(20))
    overjet_mm = db.Column(db.Float)
    overbite_mm = db.Column(db.Float)

    # Treatment
    treatment_plan = db.Column(db.Text, nullable=False)
    appliances_used = db.Column(db.Text)
    extraction_plan = db.Column(db.Text)
    estimated_treatment_months = db.Column(db.Integer)

    # Progress
    status = db.Column(db.String(20), default='active')  # planned, active, retention, completed, discontinued
    progress_notes = db.Column(db.Text)
    next_appointment_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient')
    orthodontist = db.relationship('Dentist')

    def __repr__(self):
        return f'<OrthodonticCase {self.case_number}>'
