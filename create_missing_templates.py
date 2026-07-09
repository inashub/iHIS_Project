"""
Script to create missing templates with generic content.
"""
import os

# Template directories and their needed files
templates = {
    'doctor': ['patients.html', 'patient_detail.html', 'new_record.html', 'new_prescription.html',
               'order_lab.html', 'order_imaging.html', 'medical_records.html', 'prescriptions.html',
               'appointments.html'],
    'patient': ['dashboard.html'],
    'laboratory': ['orders.html', 'order_detail.html', 'enter_results.html', 'test_catalog.html',
                   'quality_control.html'],
    'radiology': ['orders.html', 'studies.html', 'write_report.html', 'procedures.html'],
    'pharmacy': ['prescriptions.html', 'dispense.html', 'inventory.html', 'refills.html'],
    'dentistry': ['patients.html', 'dental_chart.html', 'procedures.html', 'orthodontics.html'],
    'therapy': ['patients.html', 'new_assessment.html', 'plans.html', 'exercises.html', 'progress.html'],
    'nursing': ['patients.html', 'record_vitals.html', 'notes.html', 'medication_admin.html', 'care_plans.html'],
    'reception': ['schedule.html', 'appointments.html', 'register_patient.html'],
    'admin': ['staff.html', 'departments.html', 'audit_logs.html', 'reports.html'],
    'superadmin': ['users.html', 'roles.html', 'settings.html'],
    'emr': ['view.html'],
    'appointments': ['list.html', 'book.html'],
    'reports': ['index.html', 'patient_report.html', 'appointment_report.html',
                'prescription_report.html', 'lab_report.html', 'statistics.html'],
    'errors': ['403.html', '404.html', '500.html'],
}

generic_dashboard = '''{% extends "dashboard_base.html" %}
{% block title %}{{ title|default('Dashboard') }}{% endblock %}
{% block dashboard_active %}active{% endblock %}

{% block dashboard_content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div><h4 class="mb-1">{{ heading|default('Page') }}</h4><p class="text-muted mb-0">{{ subtitle|default('') }}</p></div>
</div>
<div class="dashboard-card p-4">
    <div class="text-center py-5 text-muted">
        <i class="bi bi-cone-striped fs-1"></i>
        <h5 class="mt-3">Coming Soon</h5>
        <p>This feature is under development.</p>
    </div>
</div>
{% endblock %}
'''

generic_list = '''{% extends "dashboard_base.html" %}
{% block title %}{{ title|default('List') }}{% endblock %}
{% block dashboard_content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <div><h4 class="mb-1">{{ heading|default('List') }}</h4></div>
</div>
<div class="dashboard-card">
    <div class="card-body p-4 text-center text-muted">
        <i class="bi bi-list fs-1"></i>
        <h5 class="mt-3">Coming Soon</h5>
        <p>This feature is under development.</p>
    </div>
</div>
{% endblock %}
'''

error_template = '''{% extends "base.html" %}
{% block content %}
<div class="text-center py-5">
    <h1 class="display-1 text-muted">{{ code }}</h1>
    <h3>{{ message }}</h3>
    <a href="{{ url_for('main.index') }}" class="btn btn-primary mt-3">Go Home</a>
</div>
{% endblock %}
'''

base_dir = '/mnt/agents/output/ihis/templates'

for folder, files in templates.items():
    folder_path = os.path.join(base_dir, folder)
    os.makedirs(folder_path, exist_ok=True)
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        if os.path.exists(filepath):
            continue
        content = generic_list
        if filename == 'dashboard.html' or folder in ['emr']:
            content = generic_dashboard
        elif folder == 'errors':
            code = filename.replace('.html', '')
            messages = {'403': 'Forbidden', '404': 'Page Not Found', '500': 'Server Error'}
            content = error_template.replace('{{ code }}', code).replace('{{ message }}', messages.get(code, 'Error'))
            with open(filepath, 'w') as f:
                f.write(content)
            continue

        with open(filepath, 'w') as f:
            f.write(content)
        print(f'Created: {filepath}')

# Create additional templates
additional_templates = {
    'about.html': '''{% extends "base.html" %}
{% block content %}
<div class="container py-5">
    <h2>About iHIS</h2>
    <p>Intelligent Health Information System - A comprehensive healthcare management platform.</p>
</div>
{% endblock %}''',
    'contact.html': '''{% extends "base.html" %}
{% block content %}
<div class="container py-5">
    <h2>Contact Us</h2>
    <p>Email: admin@ihis-health.com</p>
    <p>Phone: +1 (555) 123-4567</p>
</div>
{% endblock %}''',
}

for filename, content in additional_templates.items():
    filepath = os.path.join(base_dir, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write(content)
        print(f'Created: {filepath}')

print("All missing templates created!")
