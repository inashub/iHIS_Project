"""
iHIS - AI Recommendations Model
Store AI-generated recommendations and insights.
"""
from datetime import datetime
from extensions import db


class AIRecommendation(db.Model):
    """AI-generated recommendations storage."""
    __tablename__ = 'ai_recommendations'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)

    # Recommendation Details
    module = db.Column(db.String(50), nullable=False)
    # clinical_assistant, diagnosis_support, prescription_checker, lab_interpretation,
    # radiology_assistant, risk_prediction, dental, rehabilitation

    recommendation_type = db.Column(db.String(50), nullable=False)
    # diagnosis_suggestion, drug_alert, lab_alert, image_finding, risk_alert,
    # treatment_suggestion, exercise_recommendation

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    confidence_score = db.Column(db.Float)  # 0.0 to 1.0
    data_source = db.Column(db.Text)  # JSON of input data used

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, accepted, rejected, implemented
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    review_notes = db.Column(db.Text)

    # Related records
    related_record_type = db.Column(db.String(50))  # medical_record, lab_order, radiology_order, etc.
    related_record_id = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    patient = db.relationship('Patient', backref='ai_recommendations')
    reviewer = db.relationship('User')

    def __repr__(self):
        return f'<AIRecommendation {self.module}:{self.recommendation_type}>'


class AIAnalyticsLog(db.Model):
    """Log of AI model usage and performance."""
    __tablename__ = 'ai_analytics_logs'

    id = db.Column(db.Integer, primary_key=True)
    module = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    input_summary = db.Column(db.Text)
    output_summary = db.Column(db.Text)
    processing_time_ms = db.Column(db.Integer)
    confidence_score = db.Column(db.Float)
    was_accurate = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User')

    def __repr__(self):
        return f'<AIAnalyticsLog {self.module}:{self.action}>'
