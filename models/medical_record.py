"""
iHIS - Medical Record Model (EMR)
Electronic Medical Records - SOAP notes, diagnoses, prescriptions, vitals.
"""
from datetime import datetime
from extensions import db


class MedicalRecord(db.Model):
    """Medical Record / Encounter - central EMR document."""
    __tablename__ = 'medical_records'

    id = db.Column(db.Integer, primary_key=True)
    record_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)

    # Visit Information
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visit_type = db.Column(db.String(50), default='outpatient')  # outpatient, inpatient, emergency, telemedicine
    chief_complaint = db.Column(db.Text)

    # SOAP Notes
    subjective = db.Column(db.Text)  # Patient's description
    objective = db.Column(db.Text)   # Physical exam, observations
    assessment = db.Column(db.Text)  # Diagnosis/differential
    plan = db.Column(db.Text)        # Treatment plan

    # Physical Examination
    general_appearance = db.Column(db.Text)
    physical_exam_findings = db.Column(db.Text)

    # Follow-up
    follow_up_instructions = db.Column(db.Text)
    follow_up_date = db.Column(db.Date)
    follow_up_needed = db.Column(db.Boolean, default=False)

    # Status
    status = db.Column(db.String(20), default='active')  # active, completed, amended
    is_locked = db.Column(db.Boolean, default=False)
    locked_at = db.Column(db.DateTime)
    digital_signature = db.Column(db.Text)
    signed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    signed_at = db.Column(db.DateTime)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    diagnoses = db.relationship('Diagnosis', backref='medical_record', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='medical_record', lazy='dynamic')
    vital_signs = db.relationship('VitalSign', backref='medical_record', lazy='dynamic')
    attachments = db.relationship('MedicalAttachment', backref='medical_record', lazy='dynamic')

    signer = db.relationship('User', foreign_keys=[signed_by])

    def __repr__(self):
        return f'<MedicalRecord {self.record_number}>'


class Diagnosis(db.Model):
    """Diagnosis record with ICD-10 coding."""
    __tablename__ = 'diagnoses'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    # Diagnosis
    diagnosis_type = db.Column(db.String(20), default='primary')  # primary, secondary, differential
    icd10_code = db.Column(db.String(10))
    icd10_description = db.Column(db.Text)
    clinical_description = db.Column(db.Text, nullable=False)

    # Status
    status = db.Column(db.String(20), default='active')  # active, resolved, ruled_out
    onset_date = db.Column(db.Date)
    resolved_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Diagnosis {self.icd10_code}>'


class Prescription(db.Model):
    """Prescription / medication order."""
    __tablename__ = 'prescriptions'

    id = db.Column(db.Integer, primary_key=True)
    prescription_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)

    # Prescription Details
    diagnosis = db.Column(db.Text)
    notes = db.Column(db.Text)
    instructions = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='active')  # active, dispensed, partially_dispensed, cancelled, completed
    is_dispensed = db.Column(db.Boolean, default=False)
    dispensed_at = db.Column(db.DateTime)
    dispensed_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Duration
    start_date = db.Column(db.Date, default=datetime.utcnow)
    end_date = db.Column(db.Date)
    is_chronic = db.Column(db.Boolean, default=False)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    items = db.relationship('PrescriptionItem', backref='prescription', lazy='dynamic')
    dispenser = db.relationship('User', foreign_keys=[dispensed_by])

    def __repr__(self):
        return f'<Prescription {self.prescription_number}>'


class PrescriptionItem(db.Model):
    """Individual medication item in a prescription."""
    __tablename__ = 'prescription_items'

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)

    # Dosage
    dosage = db.Column(db.String(100), nullable=False)  # e.g., "1 tablet"
    frequency = db.Column(db.String(50), nullable=False)  # e.g., "twice daily", "every 6 hours"
    route = db.Column(db.String(50), default='oral')  # oral, iv, im, topical, etc.
    duration = db.Column(db.String(50))  # e.g., "7 days"
    quantity = db.Column(db.Float)
    quantity_unit = db.Column(db.String(20))  # tablets, ml, mg

    # Instructions
    special_instructions = db.Column(db.Text)
    take_with_food = db.Column(db.Boolean, default=False)
    take_before_food = db.Column(db.Boolean, default=False)
    take_at_bedtime = db.Column(db.Boolean, default=False)

    # Status
    is_dispensed = db.Column(db.Boolean, default=False)
    dispensed_quantity = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    medication = db.relationship('Medication', backref='prescription_items')

    def __repr__(self):
        return f'<PrescriptionItem {self.medication_id}>'


class Medication(db.Model):
    """Medication / Drug catalog."""
    __tablename__ = 'medications'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    brand_name = db.Column(db.String(200))
    form = db.Column(db.String(50))  # tablet, capsule, injection, syrup, cream, etc.
    strength = db.Column(db.String(100))
    drug_class = db.Column(db.String(100))
    atc_code = db.Column(db.String(10))
    ndc_code = db.Column(db.String(20))

    # Inventory
    stock_quantity = db.Column(db.Float, default=0)
    reorder_level = db.Column(db.Float, default=10)
    unit = db.Column(db.String(20))

    # Pricing
    cost_price = db.Column(db.Float)
    selling_price = db.Column(db.Float)

    # Information
    manufacturer = db.Column(db.String(200))
    contraindications = db.Column(db.Text)
    side_effects = db.Column(db.Text)
    storage_conditions = db.Column(db.String(100))
    is_controlled = db.Column(db.Boolean, default=False)
    controlled_schedule = db.Column(db.String(20))  # Schedule II, III, IV, V
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Medication {self.name}>'


class VitalSign(db.Model):
    """Vital signs measurement."""
    __tablename__ = 'vital_signs'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Measurements
    temperature = db.Column(db.Float)  # Celsius
    temperature_site = db.Column(db.String(20), default='oral')  # oral, axillary, rectal, tympanic
    heart_rate = db.Column(db.Integer)  # bpm
    blood_pressure_systolic = db.Column(db.Integer)  # mmHg
    blood_pressure_diastolic = db.Column(db.Integer)  # mmHg
    blood_pressure_position = db.Column(db.String(20), default='sitting')
    respiratory_rate = db.Column(db.Integer)  # breaths per minute
    oxygen_saturation = db.Column(db.Float)  # SpO2 %
    pain_score = db.Column(db.Integer)  # 0-10
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    bmi = db.Column(db.Float)
    blood_glucose = db.Column(db.Float)  # mg/dL

    # Critical alerts
    is_critical = db.Column(db.Boolean, default=False)
    critical_alert = db.Column(db.String(255))

    # Context
    measurement_context = db.Column(db.String(50), default='routine')  # routine, pre_op, post_op, emergency
    notes = db.Column(db.Text)
    measured_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recorder = db.relationship('User', backref='recorded_vitals')

    def __repr__(self):
        return f'<VitalSign Patient:{self.patient_id}>'


class MedicalAttachment(db.Model):
    """Attachments to medical records (images, documents)."""
    __tablename__ = 'medical_attachments'

    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=False)
    attachment_type = db.Column(db.String(50), nullable=False)  # image, document, audio, video
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='medical_attachments')

    def __repr__(self):
        return f'<MedicalAttachment {self.title}>'


class Referral(db.Model):
    """Patient referral between providers."""
    __tablename__ = 'referrals'

    id = db.Column(db.Integer, primary_key=True)
    referral_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    from_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    to_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    reason = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='routine')  # routine, urgent, emergency
    clinical_notes = db.Column(db.Text)

    status = db.Column(db.String(20), default='pending')  # pending, accepted, completed, cancelled
    accepted_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='referrals')
    from_doctor = db.relationship('Doctor', foreign_keys=[from_doctor_id], backref='sent_referrals')
    to_doctor = db.relationship('Doctor', foreign_keys=[to_doctor_id], backref='received_referrals')

    def __repr__(self):
        return f'<Referral {self.referral_number}>'


class CareTeam(db.Model):
    """Care team assignment for multidisciplinary care."""
    __tablename__ = 'care_teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    primary_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='care_teams')
    primary_doctor = db.relationship('Doctor', backref='led_care_teams')
    members = db.relationship('CareTeamMember', backref='care_team', lazy='dynamic')

    def __repr__(self):
        return f'<CareTeam {self.name}>'


class CareTeamMember(db.Model):
    """Individual member of a care team."""
    __tablename__ = 'care_team_members'

    id = db.Column(db.Integer, primary_key=True)
    care_team_id = db.Column(db.Integer, db.ForeignKey('care_teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_in_team = db.Column(db.String(50), nullable=False)  # primary, specialist, nurse, therapist
    specialty = db.Column(db.String(100))
    notes = db.Column(db.Text)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='care_team_memberships')

    def __repr__(self):
        return f'<CareTeamMember {self.role_in_team}>'
