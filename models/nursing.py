"""
iHIS - Nursing Model
Vital signs, medication administration, nursing notes, care plans.
"""
from datetime import datetime
from extensions import db


class Nurse(db.Model):
    """Nurse model."""
    __tablename__ = 'nurses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True)
    nursing_license = db.Column(db.String(50), unique=True)
    license_expiry = db.Column(db.Date)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    specialization = db.Column(db.String(100))  # ICU, OR, ER, pediatric, oncology, etc.
    shift_preference = db.Column(db.String(20))  # day, evening, night, rotating
    years_of_experience = db.Column(db.Integer)

    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('nurse_profile', uselist=False))
    department = db.relationship('Department', backref='nurses')
    assignments = db.relationship('NurseAssignment', backref='nurse', lazy='dynamic')
    medication_admins = db.relationship('MedicationAdministration', backref='nurse', lazy='dynamic')

    def get_full_name(self):
        return self.user.get_full_name() if self.user else 'Unknown'

    def __repr__(self):
        return f'<Nurse {self.get_full_name()}>'


class NurseAssignment(db.Model):
    """Patient assignment to nurses."""
    __tablename__ = 'nurse_assignments'

    id = db.Column(db.Integer, primary_key=True)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    assigned_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)  # day, evening, night
    room_number = db.Column(db.String(20))
    bed_number = db.Column(db.String(20))
    acuity_level = db.Column(db.String(20), default='moderate')  # low, moderate, high, critical
    special_instructions = db.Column(db.Text)
    is_primary = db.Column(db.Boolean, default=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='nurse_assignments')
    assigner = db.relationship('User')

    def __repr__(self):
        return f'<NurseAssignment Nurse:{self.nurse_id} Patient:{self.patient_id}>'


class NursingNote(db.Model):
    """Nursing notes / documentation."""
    __tablename__ = 'nursing_notes'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'))

    # Note Details
    note_type = db.Column(db.String(50), nullable=False)
    # assessment, intervention, shift_note, admission, discharge, prn, incident, handoff

    # Note Content (SOAP format supported)
    subjective = db.Column(db.Text)
    objective = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    narrative = db.Column(db.Text)

    # Context
    shift = db.Column(db.String(20))  # day, evening, night
    note_date = db.Column(db.DateTime, default=datetime.utcnow)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='nursing_notes')
    nurse = db.relationship('Nurse', backref='notes')

    def __repr__(self):
        return f'<NursingNote {self.note_type}>'


class MedicationAdministration(db.Model):
    """Medication administration record (MAR)."""
    __tablename__ = 'medication_administrations'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)
    prescription_item_id = db.Column(db.Integer, db.ForeignKey('prescription_items.id'), nullable=False)

    # Administration Details
    scheduled_time = db.Column(db.DateTime, nullable=False)
    administered_time = db.Column(db.DateTime)
    dose_given = db.Column(db.String(100))
    route = db.Column(db.String(50))
    site = db.Column(db.String(50))  # injection site

    # Status
    status = db.Column(db.String(30), default='scheduled')
    # scheduled, administered, held, missed, refused, discontinued

    # Documentation
    patient_response = db.Column(db.Text)
    adverse_reaction = db.Column(db.Text)
    vital_signs_before = db.Column(db.Text)  # JSON
    notes = db.Column(db.Text)

    # Double-check
    double_checked_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    double_checked_at = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='medication_administrations')
    prescription_item = db.relationship('PrescriptionItem', backref='administrations')
    double_checker = db.relationship('User', foreign_keys=[double_checked_by])

    def __repr__(self):
        return f'<MedicationAdministration {self.status}>'


class CarePlan(db.Model):
    """Nursing care plan."""
    __tablename__ = 'care_plans'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)

    # Care Plan Content
    nursing_diagnosis = db.Column(db.Text, nullable=False)
    goals = db.Column(db.Text, nullable=False)
    interventions = db.Column(db.Text, nullable=False)
    expected_outcomes = db.Column(db.Text)
    evaluation = db.Column(db.Text)

    # Status
    status = db.Column(db.String(20), default='active')  # active, completed, revised

    # Dates
    start_date = db.Column(db.Date, nullable=False)
    target_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='care_plans')
    nurse = db.relationship('Nurse', backref='care_plans')

    def __repr__(self):
        return f'<CarePlan Patient:{self.patient_id}>'


class IntakeOutput(db.Model):
    """Fluid intake and output tracking."""
    __tablename__ = 'intake_output'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('nurses.id'), nullable=False)

    # Intake (mL)
    oral_intake = db.Column(db.Float, default=0)
    iv_intake = db.Column(db.Float, default=0)
    tube_feeding = db.Column(db.Float, default=0)
    other_intake = db.Column(db.Float, default=0)
    total_intake = db.Column(db.Float, default=0)

    # Output (mL)
    urine_output = db.Column(db.Float, default=0)
    stool_output = db.Column(db.Float, default=0)
    vomitus = db.Column(db.Float, default=0)
    drain_output = db.Column(db.Float, default=0)
    other_output = db.Column(db.Float, default=0)
    total_output = db.Column(db.Float, default=0)

    # Balance
    fluid_balance = db.Column(db.Float, default=0)

    # Shift
    shift_date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)  # day, evening, night
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

    patient = db.relationship('Patient', backref='intake_output_records')
    nurse = db.relationship('Nurse')

    def calculate_balance(self):
        self.total_intake = (self.oral_intake or 0) + (self.iv_intake or 0) + \
                           (self.tube_feeding or 0) + (self.other_intake or 0)
        self.total_output = (self.urine_output or 0) + (self.stool_output or 0) + \
                           (self.vomitus or 0) + (self.drain_output or 0) + (self.other_output or 0)
        self.fluid_balance = self.total_intake - self.total_output
        return self.fluid_balance

    def __repr__(self):
        return f'<IntakeOutput Patient:{self.patient_id} Shift:{self.shift}>'
