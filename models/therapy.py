"""
iHIS - Physical Therapy & Rehabilitation Model
Therapy assessments, sessions, exercises, and progress tracking.
"""
from datetime import datetime
from extensions import db


class TherapySpecialty(db.Model):
    """Rehabilitation specialty catalog."""
    __tablename__ = 'therapy_specialties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TherapySpecialty {self.name}>'


class PhysicalTherapist(db.Model):
    """Physical therapist / rehabilitation specialist."""
    __tablename__ = 'physical_therapists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    therapist_license = db.Column(db.String(50), unique=True)
    specialty_id = db.Column(db.Integer, db.ForeignKey('therapy_specialties.id'))
    years_of_experience = db.Column(db.Integer)
    certifications = db.Column(db.Text)

    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('therapist_profile', uselist=False))
    specialty = db.relationship('TherapySpecialty', backref='therapists')

    def get_full_name(self):
        return self.user.get_full_name() if self.user else 'Unknown'

    def __repr__(self):
        return f'<PhysicalTherapist {self.get_full_name()}>'


class TherapyAssessment(db.Model):
    """Initial therapy assessment / evaluation."""
    __tablename__ = 'therapy_assessments'

    id = db.Column(db.Integer, primary_key=True)
    assessment_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('physical_therapists.id'), nullable=False)
    referring_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'))
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'))

    # Assessment Date
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    assessment_type = db.Column(db.String(50))  # initial, re_evaluation, discharge

    # Pain Assessment
    pain_level_rest = db.Column(db.Integer)  # 0-10
    pain_level_activity = db.Column(db.Integer)
    pain_location = db.Column(db.String(200))
    pain_nature = db.Column(db.String(100))  # sharp, dull, aching, burning, throbbing
    pain_duration = db.Column(db.String(100))
    pain_aggravating_factors = db.Column(db.Text)
    pain_relieving_factors = db.Column(db.Text)

    # Functional Assessment
    functional_status = db.Column(db.Text)
    adl_independence = db.Column(db.String(20))  # independent, modified_independent, supervision, assistance, dependent
    mobility_status = db.Column(db.Text)
    gait_assessment = db.Column(db.Text)
    balance_assessment = db.Column(db.Text)

    # Physical Assessment
    posture_assessment = db.Column(db.Text)
    range_of_motion = db.Column(db.Text)  # JSON format
    muscle_strength = db.Column(db.Text)  # MMT 0-5 for each muscle group
    special_tests = db.Column(db.Text)
    palpation_findings = db.Column(db.Text)
    neurological_assessment = db.Column(db.Text)

    # Goals
    short_term_goals = db.Column(db.Text, nullable=False)
    long_term_goals = db.Column(db.Text, nullable=False)
    estimated_sessions = db.Column(db.Integer)
    estimated_duration_weeks = db.Column(db.Integer)
    prognosis = db.Column(db.Text)

    # Plan
    treatment_plan_summary = db.Column(db.Text, nullable=False)
    precautions = db.Column(db.Text)
    contraindications = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    therapist = db.relationship('PhysicalTherapist', backref='assessments')
    referring_doctor = db.relationship('Doctor', backref='therapy_referrals')
    medical_record = db.relationship('MedicalRecord')
    therapy_plans = db.relationship('TherapyPlan', backref='assessment', lazy='dynamic')

    def __repr__(self):
        return f'<TherapyAssessment {self.assessment_number}>'


class TherapyPlan(db.Model):
    """Therapy treatment plan."""
    __tablename__ = 'therapy_plans'

    id = db.Column(db.Integer, primary_key=True)
    plan_number = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('physical_therapists.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('therapy_assessments.id'), nullable=False)

    # Plan Details
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    frequency_per_week = db.Column(db.Integer)
    session_duration_minutes = db.Column(db.Integer, default=60)

    # Treatment Modalities (stored as JSON)
    modalities = db.Column(db.Text)  # JSON array: manual_therapy, exercise, electrotherapy, etc.
    interventions = db.Column(db.Text, nullable=False)
    home_exercise_program = db.Column(db.Text)

    # Goals
    goals = db.Column(db.Text, nullable=False)
    outcome_measures = db.Column(db.Text)  # JSON: VAS, ODI, DASH, Berg, TUG, etc.

    # Status
    status = db.Column(db.String(20), default='active')  # active, completed, discontinued, on_hold
    discharge_criteria = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    therapist = db.relationship('PhysicalTherapist', backref='therapy_plans')
    sessions = db.relationship('TherapySession', backref='therapy_plan', lazy='dynamic')
    progress_records = db.relationship('RehabilitationProgress', backref='therapy_plan', lazy='dynamic')

    def __repr__(self):
        return f'<TherapyPlan {self.plan_number}>'


class TherapySession(db.Model):
    """Individual therapy session."""
    __tablename__ = 'therapy_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_number = db.Column(db.Integer, nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('therapy_plans.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('physical_therapists.id'), nullable=False)

    # Session Details
    session_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer)
    session_type = db.Column(db.String(50))  # individual, group, home_visit, telehealth

    # SOAP Notes
    subjective = db.Column(db.Text)
    objective = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)

    # Treatment Provided
    interventions = db.Column(db.Text)  # JSON list of interventions performed
    exercises_performed = db.Column(db.Text)  # JSON list
    modalities_used = db.Column(db.Text)  # JSON list

    # Response
    patient_response = db.Column(db.Text)
    pain_level_before = db.Column(db.Integer)
    pain_level_after = db.Column(db.Integer)
    tolerance = db.Column(db.String(20))  # good, fair, poor
    adverse_reactions = db.Column(db.Text)

    # Next Session
    next_session_plan = db.Column(db.Text)
    home_exercise_given = db.Column(db.Boolean, default=False)
    home_exercise_instructions = db.Column(db.Text)

    # Attendance
    attendance_status = db.Column(db.String(20), default='completed')  # completed, no_show, cancelled, rescheduled

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = db.relationship('Patient', backref='therapy_sessions')
    therapist = db.relationship('PhysicalTherapist', backref='sessions')

    def __repr__(self):
        return f'<TherapySession #{self.session_number}>'


class TherapyExercise(db.Model):
    """Exercise library for therapy prescriptions."""
    __tablename__ = 'therapy_exercises'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    # strengthening, stretching, balance, aerobic, neuromuscular, manual_therapy

    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text)
    muscle_groups = db.Column(db.String(255))
    contraindications = db.Column(db.Text)
    equipment_needed = db.Column(db.String(255))

    # Media
    image_path = db.Column(db.String(255))
    video_path = db.Column(db.String(255))

    # Parameters
    default_sets = db.Column(db.Integer)
    default_reps = db.Column(db.Integer)
    default_duration_seconds = db.Column(db.Integer)
    default_hold_seconds = db.Column(db.Integer)
    default_frequency = db.Column(db.String(50))  # daily, twice_daily, etc.

    difficulty_level = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User')

    def __repr__(self):
        return f'<TherapyExercise {self.name}>'


class RehabilitationProgress(db.Model):
    """Patient rehabilitation progress tracking."""
    __tablename__ = 'rehabilitation_progress'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('therapy_plans.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('physical_therapists.id'), nullable=False)
    assessment_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Outcome Measures
    pain_score_current = db.Column(db.Integer)  # 0-10
    pain_score_change = db.Column(db.Integer)  # change from baseline
    rom_improvement = db.Column(db.String(20))  # improved, unchanged, worsened
    strength_improvement = db.Column(db.String(20))
    functional_improvement = db.Column(db.String(20))

    # Standardized Outcome Scores
    oswestry_score = db.Column(db.Float)  # ODI 0-100
    dash_score = db.Column(db.Float)  # DASH 0-100
    berg_balance_score = db.Column(db.Float)  # 0-56
    tug_test_seconds = db.Column(db.Float)  # Timed Up and Go
    six_min_walk_meters = db.Column(db.Float)

    # Progress Metrics
    goals_achieved = db.Column(db.Text)
    goals_status = db.Column(db.Text)  # JSON: goal -> achieved/partial/not_achieved
    compliance_rate = db.Column(db.Float)  # % of sessions attended
    hep_compliance = db.Column(db.String(20))  # excellent, good, fair, poor

    # Assessment
    therapist_assessment = db.Column(db.Text)
    discharge_readiness = db.Column(db.String(20))  # ready, nearing, not_ready
    plan_modifications = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient')
    therapist = db.relationship('PhysicalTherapist')

    def __repr__(self):
        return f'<RehabilitationProgress Plan:{self.plan_id}>'


class FunctionalOutcome(db.Model):
    """Standardized functional outcome measurements."""
    __tablename__ = 'functional_outcomes'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    assessment_id = db.Column(db.Integer, db.ForeignKey('therapy_assessments.id'))
    plan_id = db.Column(db.Integer, db.ForeignKey('therapy_plans.id'))

    outcome_tool = db.Column(db.String(100), nullable=False)  # VAS, ODI, DASH, Berg, TUG, 6MWT, FIM
    score = db.Column(db.Float, nullable=False)
    raw_data = db.Column(db.Text)  # JSON of individual items
    interpretation = db.Column(db.String(255))
    measured_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    measured_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='functional_outcomes')
    measurer = db.relationship('User')

    def __repr__(self):
        return f'<FunctionalOutcome {self.outcome_tool}={self.score}>'
