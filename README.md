# iHIS - Intelligent Health Information System

A comprehensive, production-ready healthcare management platform built with Python Flask, SQLAlchemy, and Bootstrap 5.

## Features

- **11 Specialized Portals**: Patient, Doctor, Laboratory, Radiology, Pharmacy, Dentistry, Physical Therapy, Nursing, Reception, Administration, and Super Admin
- **Electronic Medical Records (EMR)**: SOAP notes, diagnoses with ICD-10, prescriptions, vital signs
- **AI-Ready Architecture**: Pre-built interfaces and placeholder classes for future AI integration
- **Role-Based Access Control (RBAC)**: Granular permissions with 11 user roles
- **Appointment System**: Online booking, scheduling, and queue management
- **Laboratory Management**: Test catalog, order processing, result entry, quality control
- **Radiology (DICOM-ready)**: Imaging orders, studies, reports with DICOM structure
- **Pharmacy**: Dispensing, inventory tracking, drug interaction alerts, refill management
- **Dentistry**: Interactive dental charting (Universal/FDI/Palmer), procedures, orthodontics
- **Physical Therapy**: Assessments, treatment plans, exercise library, progress tracking
- **Security**: Password hashing, session management, CSRF protection, audit logging

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application at `http://localhost:5000`

### Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `admin` | `admin123` |
| Doctor | `doctor1` | `password123` |
| Lab Technician | `labtech1` | `password123` |
| Radiologist | `radiologist1` | `password123` |
| Pharmacist | `pharmacist1` | `password123` |
| Dentist | `dentist1` | `password123` |
| Therapist | `therapist1` | `password123` |
| Nurse | `nurse1` | `password123` |
| Receptionist | `reception1` | `password123` |
| Admin | `admin1` | `password123` |

## Project Structure

```
ihis/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── requirements.txt        # Python dependencies
├── models/                 # Database models
│   ├── user.py            # User, Role, Permission, AuditLog
│   ├── patient.py         # Patient, Department, Specialty
│   ├── doctor.py          # Doctor, Appointment, Schedule
│   ├── medical_record.py  # EMR, Diagnosis, Prescription, VitalSign
│   ├── laboratory.py      # LabOrder, LabResult, QualityControl
│   ├── radiology.py       # RadiologyOrder, Study, Report
│   ├── pharmacy.py        # Inventory, Dispensing, DrugInteraction
│   ├── dentistry.py       # DentalRecord, Charting, OrthodonticCase
│   ├── therapy.py         # Assessment, Plan, Session, Exercise
│   ├── nursing.py         # Nurse, MedicationAdmin, CarePlan
│   └── ai_recommendations.py # AI recommendations storage
├── routes/                 # Flask blueprints
│   ├── auth.py            # Authentication routes
│   ├── main.py            # Public pages
│   ├── doctor.py          # Doctor portal
│   ├── patient.py         # Patient portal
│   ├── laboratory.py      # Lab portal
│   ├── radiology.py       # Radiology portal
│   ├── pharmacy.py        # Pharmacy portal
│   ├── dentistry.py       # Dental portal
│   ├── therapy.py         # PT portal
│   ├── nursing.py         # Nursing portal
│   ├── reception.py       # Reception portal
│   ├── admin.py           # Admin portal
│   ├── superadmin.py      # Super admin portal
│   ├── emr.py             # EMR access
│   ├── appointments.py    # Appointment management
│   ├── reports.py         # Report generation
│   └── api.py             # REST API endpoints
├── services/ai/           # AI integration layer
├── templates/             # HTML templates
├── static/                # CSS, JS, uploads
├── database/              # Database files
└── tests/                 # Unit tests
```

## AI Integration Layer

The system includes a dedicated `/services/ai/` module with placeholder classes:

- `AIClinicalAssistant` - Patient analysis and clinical insights
- `AIDiagnosisSupport` - Differential diagnosis and ICD-10 mapping
- `AIPrescriptionChecker` - Drug safety validation
- `AIDrugInteractionEngine` - Interaction analysis
- `AILaboratoryInterpretation` - Lab result interpretation
- `AIRadiologyAssistant` - Image analysis and findings detection
- `AIPatientRiskPrediction` - Mortality, readmission, fall risk
- `AIAppointmentOptimization` - Schedule optimization
- `AIMedicalCodingAssistant` - ICD-10/CPT coding
- `AIHospitalAnalytics` - Operational analytics
- `AIDentalAssistant` - Dental X-ray analysis
- `AIRehabilitationAssistant` - Progress analysis and recommendations

## Database

SQLite is used by default with an easy migration path to PostgreSQL/MySQL. The schema includes 40+ tables with proper foreign keys, indexes, soft delete support, and audit timestamps.

## API Endpoints

RESTful API available at `/api/`:

- `GET /api/health` - Health check
- `GET /api/dashboard-stats` - Dashboard statistics
- `GET /api/patients` - Patient list
- `GET /api/patient/<id>` - Patient details
- `GET /api/appointments` - Appointment list
- `GET /api/lab-tests` - Lab test catalog
- `GET /api/medications` - Medication catalog
- `GET /api/notifications` - User notifications

## Security Features

- Password hashing with PBKDF2-SHA256
- CSRF protection on all forms
- Session management with timeout
- Role-based access control (RBAC)
- Audit trail for all actions
- Account lockout after failed attempts
- Secure file upload validation

## License

This project is designed for healthcare institutions and can be customized for hospital, clinic, or national healthcare system deployment.
