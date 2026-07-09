"""
iHIS - Physical Therapy Routes
Therapy portal for assessments, sessions, and progress tracking.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models.therapy import TherapyAssessment, TherapyPlan, TherapySession, TherapyExercise, RehabilitationProgress
from models.patient import Patient

therapy_bp = Blueprint('therapy', __name__, template_folder='../templates/therapy')


@therapy_bp.route('/dashboard')
@login_required
def dashboard():
    """Therapy dashboard."""
    if current_user.role not in ['therapist', 'admin', 'superadmin']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))

    today = date.today()
    today_sessions = TherapySession.query.filter(
        db.func.date(TherapySession.session_date) == today
    ).count()

    active_plans = TherapyPlan.query.filter_by(status='active').count()

    high_risk = RehabilitationProgress.query.filter(
        RehabilitationProgress.discharge_readiness == 'not_ready'
    ).count()

    recent_sessions = TherapySession.query.order_by(
        TherapySession.session_date.desc()).limit(10).all()

    return render_template('therapy/dashboard.html',
                         today_sessions=today_sessions,
                         active_plans=active_plans,
                         high_risk=high_risk,
                         recent_sessions=recent_sessions)


@therapy_bp.route('/patients')
@login_required
def patients():
    """List therapy patients."""
    if current_user.role not in ['therapist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    patients = Patient.query.filter_by(is_deleted=False).order_by(
        Patient.last_name).paginate(page=page, per_page=20, error_out=False)
    return render_template('therapy/patients.html', patients=patients)


@therapy_bp.route('/patient/<int:patient_id>/assess', methods=['GET', 'POST'])
@login_required
def new_assessment(patient_id):
    """Create therapy assessment."""
    patient = Patient.query.filter_by(id=patient_id, is_deleted=False).first_or_404()

    if request.method == 'POST':
        assessment = TherapyAssessment(
            assessment_number=f'TA{datetime.now().strftime("%Y%m%d%H%M%S")}',
            patient_id=patient.id,
            therapist_id=current_user.id,
            assessment_date=datetime.now(),
            pain_level_rest=int(request.form.get('pain_rest', 0)),
            pain_level_activity=int(request.form.get('pain_activity', 0)),
            pain_location=request.form.get('pain_location'),
            functional_status=request.form.get('functional_status'),
            range_of_motion=request.form.get('range_of_motion'),
            muscle_strength=request.form.get('muscle_strength'),
            short_term_goals=request.form.get('short_term_goals'),
            long_term_goals=request.form.get('long_term_goals'),
            treatment_plan_summary=request.form.get('treatment_plan')
        )
        db.session.add(assessment)
        db.session.commit()
        flash('Assessment created.', 'success')
        return redirect(url_for('therapy.patients'))

    return render_template('therapy/new_assessment.html', patient=patient)


@therapy_bp.route('/plans')
@login_required
def plans():
    """List therapy plans."""
    if current_user.role not in ['therapist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    plans = TherapyPlan.query.order_by(TherapyPlan.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('therapy/plans.html', plans=plans)


@therapy_bp.route('/exercises')
@login_required
def exercises():
    """Exercise library."""
    if current_user.role not in ['therapist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    exercises = TherapyExercise.query.filter_by(is_active=True).order_by(
        TherapyExercise.name).paginate(page=page, per_page=20, error_out=False)
    return render_template('therapy/exercises.html', exercises=exercises)


@therapy_bp.route('/progress')
@login_required
def progress():
    """Progress tracking."""
    if current_user.role not in ['therapist', 'admin', 'superadmin']:
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    progress = RehabilitationProgress.query.order_by(
        RehabilitationProgress.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('therapy/progress.html', progress=progress)
