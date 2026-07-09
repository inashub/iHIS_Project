"""
iHIS - Patient Model
Patient demographics, medical history, and health records.
"""
from datetime import datetime
from extensions import db


class Department(db.Model):
    """Hospital department model."""
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    description = db.Column(db.Text)
    floor = db.Column(db.String(20))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    head_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    head_doctor = db.relationship('Doctor', foreign_keys=[head_doctor_id], backref='headed_departments')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Department {self.name}>'


class Specialty(db.Model):
    """Medical specialty model."""
    __tablename__ = 'specialties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50))  # medical, surgical, diagnostic, dental, therapy
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Specialty {self.name}>'


class Patient(db.Model):
    """Patient model - comprehensive demographics and health information."""
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=True)

    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # male, female, other
    blood_type = db.Column(db.String(5))  # A+, A-, B+, B-, AB+, AB-, O+, O-
    marital_status = db.Column(db.String(20))
    occupation = db.Column(db.String(100))
    nationality = db.Column(db.String(50), default='Unknown')
    language_preferred = db.Column(db.String(20), default='en')

    # Contact Information
    email = db.Column(db.String(120))
    phone_primary = db.Column(db.String(20), nullable=False)
    phone_secondary = db.Column(db.String(20))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    country = db.Column(db.String(50))

    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    emergency_contact_relationship = db.Column(db.String(50))

    # Insurance Information
    insurance_provider = db.Column(db.String(100))
    insurance_policy_number = db.Column(db.String(100))
    insurance_group_number = db.Column(db.String(100))
    insurance_expiry = db.Column(db.Date)

    # Medical Summary (quick access)
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    bmi = db.Column(db.Float)

    # Status
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_deceased = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('patient_profile', uselist=False))
    allergies = db.relationship('Allergy', backref='patient', lazy='dynamic')
    chronic_diseases = db.relationship('ChronicDisease', backref='patient', lazy='dynamic')
    vaccinations = db.relationship('Vaccination', backref='patient', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='patient', lazy='dynamic')
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='patient', lazy='dynamic')
    lab_orders = db.relationship('LabOrder', backref='patient', lazy='dynamic')
    radiology_orders = db.relationship('RadiologyOrder', backref='patient', lazy='dynamic')
    vital_signs = db.relationship('VitalSign', backref='patient', lazy='dynamic')
    documents = db.relationship('PatientDocument', backref='patient', lazy='dynamic')
    dental_records = db.relationship('DentalRecord', backref='patient', lazy='dynamic')
    therapy_assessments = db.relationship('TherapyAssessment', backref='patient', lazy='dynamic')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        if self.date_of_birth:
            today = datetime.now()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def calculate_bmi(self):
        if self.height_cm and self.weight_kg:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 2)
            return self.bmi
        return None

    def __repr__(self):
        return f'<Patient {self.patient_id}: {self.get_full_name()}>'


class Allergy(db.Model):
    """Patient allergy record."""
    __tablename__ = 'allergies'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    allergen = db.Column(db.String(100), nullable=False)
    allergy_type = db.Column(db.String(50))  # drug, food, environmental, latex, other
    severity = db.Column(db.String(20))  # mild, moderate, severe, life_threatening
    reaction = db.Column(db.Text)
    onset_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    reported_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Allergy {self.allergen}>'


class ChronicDisease(db.Model):
    """Patient chronic disease / medical condition record."""
    __tablename__ = 'chronic_diseases'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    condition = db.Column(db.String(100), nullable=False)
    icd10_code = db.Column(db.String(10))
    diagnosed_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, controlled, resolved
    severity = db.Column(db.String(20))  # mild, moderate, severe
    treating_physician = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ChronicDisease {self.condition}>'


class Vaccination(db.Model):
    """Patient vaccination record."""
    __tablename__ = 'vaccinations'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    vaccine_name = db.Column(db.String(100), nullable=False)
    vaccine_code = db.Column(db.String(50))  # CVX code
    dose_number = db.Column(db.Integer, default=1)
    total_doses = db.Column(db.Integer)
    date_administered = db.Column(db.Date, nullable=False)
    administering_provider = db.Column(db.String(100))
    lot_number = db.Column(db.String(50))
    site = db.Column(db.String(50))  # left_arm, right_arm, oral, etc.
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vaccination {self.vaccine_name}>'


class PatientDocument(db.Model):
    """Patient uploaded documents."""
    __tablename__ = 'patient_documents'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # id_proof, insurance, lab_report, other
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='uploaded_documents')

    def __repr__(self):
        return f'<PatientDocument {self.title}>'
