"""
iHIS - Doctor Model
Doctor profiles, schedules, and clinical relationships.
"""
from datetime import datetime, time
from extensions import db


class Doctor(db.Model):
    """Doctor model - professional information and scheduling."""
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True)

    # Professional Information
    license_number = db.Column(db.String(50), unique=True)
    license_expiry = db.Column(db.Date)
    npi_number = db.Column(db.String(20))
    primary_specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'))
    secondary_specialty_id = db.Column(db.Integer, db.ForeignKey('specialties.id'))
    qualification = db.Column(db.String(255))  # e.g., "MD, Board Certified"
    education = db.Column(db.Text)
    years_of_experience = db.Column(db.Integer)
    languages_spoken = db.Column(db.String(255))  # Comma-separated

    # Department & Scheduling
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    consultation_duration_minutes = db.Column(db.Integer, default=30)
    max_patients_per_day = db.Column(db.Integer, default=20)
    is_available_for_telemedicine = db.Column(db.Boolean, default=False)

    # Ratings & Reviews
    rating_average = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)

    # Status
    status = db.Column(db.String(20), default='active')  # active, on_leave, suspended, retired
    joined_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship('User', backref=db.backref('doctor_profile', uselist=False))
    primary_specialty = db.relationship('Specialty', foreign_keys=[primary_specialty_id],
                                        backref='primary_doctors')
    secondary_specialty = db.relationship('Specialty', foreign_keys=[secondary_specialty_id],
                                          backref='secondary_doctors')
    department = db.relationship('Department', foreign_keys=[department_id], backref='doctors')
    schedules = db.relationship('DoctorSchedule', backref='doctor', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='doctor', lazy='dynamic')
    medical_records = db.relationship('MedicalRecord', backref='doctor', lazy='dynamic')
    prescriptions = db.relationship('Prescription', backref='doctor', lazy='dynamic')

    def get_full_name(self):
        return self.user.get_full_name() if self.user else 'Unknown'

    def __repr__(self):
        return f'<Doctor {self.get_full_name()}>'


class DoctorSchedule(db.Model):
    """Doctor weekly schedule template."""
    __tablename__ = 'doctor_schedules'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    max_appointments = db.Column(db.Integer, default=10)
    location = db.Column(db.String(100))  # Room number, clinic location
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DoctorSchedule Dr.{self.doctor_id} Day:{self.day_of_week}>'


class Appointment(db.Model):
    """Appointment model - scheduling and tracking."""
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)

    # Appointment Details
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    appointment_type = db.Column(db.String(50), default='consultation')  # consultation, follow_up, procedure, emergency, telemedicine
    priority = db.Column(db.String(20), default='routine')  # routine, urgent, emergency
    reason = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    notes = db.Column(db.Text)

    # Status Tracking
    status = db.Column(db.String(30), default='scheduled')
    # scheduled, confirmed, checked_in, in_progress, completed, cancelled, no_show, rescheduled
    checked_in_at = db.Column(db.DateTime)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    # Billing
    billing_status = db.Column(db.String(20), default='pending')  # pending, billed, paid, waived
    fee = db.Column(db.Float)

    # Cancellation
    cancelled_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    cancelled_at = db.Column(db.DateTime)
    cancellation_reason = db.Column(db.Text)

    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_appointments')
    canceller = db.relationship('User', foreign_keys=[cancelled_by])

    def __repr__(self):
        return f'<Appointment {self.appointment_number}>'


class TimeSlot(db.Model):
    """Available time slots for booking."""
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    slot_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    doctor = db.relationship('Doctor', backref='time_slots')

    def __repr__(self):
        return f'<TimeSlot {self.slot_date} {self.start_time}-{self.end_time}>'
