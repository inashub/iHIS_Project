"""
iHIS - Database Seeding
Initial data for roles, specialties, departments, admin user, and test data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, date, time, timedelta
from werkzeug.security import generate_password_hash

from extensions import db


def seed_database():
    """Seed the database with initial data if tables are empty."""
    from models.user import Role, Permission, User, role_permissions
    from models.patient import Department, Specialty
    from models.dentistry import DentalSpecialty
    from models.therapy import TherapySpecialty
    from models.laboratory import LabTestCatalog, LabTestParameter
    from models.radiology import ImagingModality, ImagingProcedure
    from models.medical_record import Medication
    from models.doctor import Doctor, DoctorSchedule
    from models.patient import Patient
    from models.nursing import Nurse
    from models.dentistry import Dentist
    from models.therapy import PhysicalTherapist

    # Check if already seeded
    if Role.query.first():
        return

    print("Seeding database...")

    # Create roles
    roles_data = [
        ('patient', 'Patient - can view own records, book appointments, message doctors'),
        ('doctor', 'Doctor - can manage patients, write prescriptions, order tests'),
        ('lab_tech', 'Laboratory Technician - can process lab orders and enter results'),
        ('radiologist', 'Radiologist - can review and report imaging studies'),
        ('pharmacist', 'Pharmacist - can dispense medications and manage inventory'),
        ('dentist', 'Dentist - can manage dental records and procedures'),
        ('therapist', 'Physical Therapist - can manage therapy plans and sessions'),
        ('nurse', 'Nurse - can record vitals, administer medications, write notes'),
        ('receptionist', 'Receptionist - can schedule appointments and manage check-ins'),
        ('admin', 'Hospital Administrator - can manage staff, departments, and reports'),
        ('superadmin', 'Super Administrator - full system control'),
    ]

    roles = {}
    for name, desc in roles_data:
        role = Role(name=name, description=desc)
        db.session.add(role)
        roles[name] = role

    db.session.commit()

    # Create permissions
    permissions_data = [
        # Patient permissions
        ('patient_view_own', 'patient', 'view', 'View own patient records'),
        ('patient_book_appointment', 'patient', 'create', 'Book appointments'),
        ('patient_message_doctor', 'patient', 'create', 'Message doctors'),

        # Doctor permissions
        ('doctor_view_patients', 'patient', 'view', 'View patient records'),
        ('doctor_edit_patients', 'patient', 'edit', 'Edit patient records'),
        ('doctor_create_records', 'medical_record', 'create', 'Create medical records'),
        ('doctor_write_prescriptions', 'prescription', 'create', 'Write prescriptions'),
        ('doctor_order_labs', 'lab_order', 'create', 'Order laboratory tests'),
        ('doctor_order_imaging', 'radiology_order', 'create', 'Order imaging'),

        # Lab permissions
        ('lab_process_orders', 'lab_order', 'edit', 'Process lab orders'),
        ('lab_enter_results', 'lab_result', 'create', 'Enter lab results'),
        ('lab_verify_results', 'lab_result', 'edit', 'Verify lab results'),

        # Radiology permissions
        ('radiology_process_orders', 'radiology_order', 'edit', 'Process imaging orders'),
        ('radiology_capture_images', 'radiology_study', 'create', 'Capture images'),
        ('radiology_write_reports', 'radiology_report', 'create', 'Write radiology reports'),

        # Pharmacy permissions
        ('pharmacy_dispense', 'prescription', 'edit', 'Dispense medications'),
        ('pharmacy_manage_inventory', 'pharmacy_inventory', 'edit', 'Manage inventory'),

        # Dental permissions
        ('dentist_manage_records', 'dental_record', 'edit', 'Manage dental records'),
        ('dentist_procedures', 'dental_procedure', 'create', 'Perform dental procedures'),

        # Therapy permissions
        ('therapist_assess', 'therapy_assessment', 'create', 'Create therapy assessments'),
        ('therapist_treat', 'therapy_session', 'create', 'Conduct therapy sessions'),

        # Nursing permissions
        ('nurse_record_vitals', 'vital_sign', 'create', 'Record vital signs'),
        ('nurse_administer_meds', 'medication_administration', 'create', 'Administer medications'),
        ('nurse_write_notes', 'nursing_note', 'create', 'Write nursing notes'),

        # Reception permissions
        ('reception_schedule', 'appointment', 'create', 'Schedule appointments'),
        ('reception_checkin', 'appointment', 'edit', 'Check in patients'),

        # Admin permissions
        ('admin_manage_staff', 'user', 'edit', 'Manage staff'),
        ('admin_view_reports', 'report', 'view', 'View reports'),
        ('admin_manage_departments', 'department', 'edit', 'Manage departments'),

        # Superadmin permissions
        ('superadmin_full_access', '*', '*', 'Full system access'),
    ]

    permissions = {}
    for name, resource, action, desc in permissions_data:
        perm = Permission(name=name, resource=resource, action=action, description=desc)
        db.session.add(perm)
        permissions[name] = perm

    db.session.commit()

    # Assign permissions to roles
    # Superadmin gets all permissions
    for perm in permissions.values():
        roles['superadmin'].permissions.append(perm)

    # Admin gets admin + reception + view permissions
    for pname in ['admin_manage_staff', 'admin_view_reports', 'admin_manage_departments',
                   'reception_schedule', 'reception_checkin', 'patient_view_own',
                   'doctor_view_patients', 'lab_process_orders', 'radiology_process_orders',
                   'pharmacy_manage_inventory']:
        if pname in permissions:
            roles['admin'].permissions.append(permissions[pname])

    # Doctor gets doctor permissions
    for pname in ['doctor_view_patients', 'doctor_edit_patients', 'doctor_create_records',
                   'doctor_write_prescriptions', 'doctor_order_labs', 'doctor_order_imaging',
                   'patient_view_own']:
        if pname in permissions:
            roles['doctor'].permissions.append(permissions[pname])

    # Assign basic permissions to other roles
    for pname in ['lab_process_orders', 'lab_enter_results', 'lab_verify_results']:
        if pname in permissions:
            roles['lab_tech'].permissions.append(permissions[pname])

    for pname in ['radiology_process_orders', 'radiology_capture_images', 'radiology_write_reports']:
        if pname in permissions:
            roles['radiologist'].permissions.append(permissions[pname])

    for pname in ['pharmacy_dispense', 'pharmacy_manage_inventory']:
        if pname in permissions:
            roles['pharmacist'].permissions.append(permissions[pname])

    for pname in ['dentist_manage_records', 'dentist_procedures']:
        if pname in permissions:
            roles['dentist'].permissions.append(permissions[pname])

    for pname in ['therapist_assess', 'therapist_treat']:
        if pname in permissions:
            roles['therapist'].permissions.append(permissions[pname])

    for pname in ['nurse_record_vitals', 'nurse_administer_meds', 'nurse_write_notes']:
        if pname in permissions:
            roles['nurse'].permissions.append(permissions[pname])

    for pname in ['reception_schedule', 'reception_checkin']:
        if pname in permissions:
            roles['receptionist'].permissions.append(permissions[pname])

    for pname in ['patient_view_own', 'patient_book_appointment', 'patient_message_doctor']:
        if pname in permissions:
            roles['patient'].permissions.append(permissions[pname])

    db.session.commit()

    # Create departments
    departments_data = [
        ('Emergency Department', 'ED', '24/7 emergency medical services', 'Ground Floor', 'ext.1001'),
        ('Internal Medicine', 'IM', 'General internal medicine and primary care', '1st Floor', 'ext.1101'),
        ('Cardiology', 'CARD', 'Heart and cardiovascular care', '2nd Floor', 'ext.1201'),
        ('Neurology', 'NEURO', 'Brain and nervous system care', '2nd Floor', 'ext.1202'),
        ('Pediatrics', 'PEDS', 'Children and adolescent care', '1st Floor', 'ext.1102'),
        ('Orthopedics', 'ORTHO', 'Bone and joint care', '3rd Floor', 'ext.1301'),
        ('Surgery', 'SURG', 'General and specialized surgery', '3rd Floor', 'ext.1302'),
        ('Obstetrics & Gynecology', 'OBGYN', 'Women health and maternity', '1st Floor', 'ext.1103'),
        ('Radiology', 'RAD', 'Medical imaging services', 'Ground Floor', 'ext.1002'),
        ('Laboratory', 'LAB', 'Clinical laboratory services', 'Ground Floor', 'ext.1003'),
        ('Pharmacy', 'PHARM', 'Medication dispensing', 'Ground Floor', 'ext.1004'),
        ('Dentistry', 'DENT', 'Dental and oral health', '2nd Floor', 'ext.1203'),
        ('Physical Therapy', 'PT', 'Rehabilitation and physical therapy', '1st Floor', 'ext.1104'),
        ('Oncology', 'ONC', 'Cancer care and treatment', '2nd Floor', 'ext.1204'),
        ('Intensive Care Unit', 'ICU', 'Critical care unit', '2nd Floor', 'ext.1205'),
        ('Administration', 'ADMIN', 'Hospital administration', '4th Floor', 'ext.1401'),
    ]

    for name, code, desc, floor, phone in departments_data:
        dept = Department(name=name, code=code, description=desc, floor=floor, phone=phone)
        db.session.add(dept)

    db.session.commit()

    # Create specialties
    specialties_data = [
        ('Internal Medicine', 'medical', 'General internal medicine'),
        ('Cardiology', 'medical', 'Heart and cardiovascular diseases'),
        ('Neurology', 'medical', 'Brain and nervous system'),
        ('Pediatrics', 'medical', 'Children health'),
        ('Orthopedics', 'surgical', 'Bone and joint surgery'),
        ('General Surgery', 'surgical', 'General surgical procedures'),
        ('ENT', 'surgical', 'Ear, nose, and throat'),
        ('Dermatology', 'medical', 'Skin conditions'),
        ('Psychiatry', 'medical', 'Mental health'),
        ('Ophthalmology', 'surgical', 'Eye care and surgery'),
        ('Oncology', 'medical', 'Cancer treatment'),
        ('Gynecology', 'surgical', 'Women reproductive health'),
        ('Urology', 'surgical', 'Urinary system'),
        ('Endocrinology', 'medical', 'Hormone and metabolism'),
        ('Gastroenterology', 'medical', 'Digestive system'),
        ('Pulmonology', 'medical', 'Respiratory system'),
        ('Nephrology', 'medical', 'Kidney diseases'),
        ('Family Medicine', 'medical', 'Family and primary care'),
        ('Emergency Medicine', 'medical', 'Emergency care'),
        ('Anesthesiology', 'medical', 'Anesthesia and pain management'),
        ('Radiology', 'diagnostic', 'Medical imaging'),
        ('Pathology', 'diagnostic', 'Laboratory medicine'),
        ('Physical Medicine', 'therapy', 'Physical medicine and rehabilitation'),
    ]

    for name, category, desc in specialties_data:
        spec = Specialty(name=name, category=category, description=desc)
        db.session.add(spec)

    db.session.commit()

    # Create dental specialties
    dental_specs = [
        'General Dentistry', 'Orthodontics', 'Prosthodontics', 'Endodontics',
        'Periodontics', 'Oral Surgery', 'Pediatric Dentistry',
        'Cosmetic Dentistry', 'Implantology', 'Oral Medicine', 'Maxillofacial Surgery'
    ]
    for name in dental_specs:
        ds = DentalSpecialty(name=name)
        db.session.add(ds)

    db.session.commit()

    # Create therapy specialties
    therapy_specs = [
        'Physical Therapy', 'Sports Rehabilitation', 'Neurological Rehabilitation',
        'Orthopedic Rehabilitation', 'Pediatric Rehabilitation', 'Geriatric Rehabilitation',
        'Cardiac Rehabilitation', 'Pulmonary Rehabilitation', 'Occupational Therapy',
        'Speech Therapy', 'Pain Management'
    ]
    for name in therapy_specs:
        ts = TherapySpecialty(name=name)
        db.session.add(ts)

    db.session.commit()

    # Create imaging modalities
    modalities = [
        ('X-Ray', 'XR', 'General radiography', 'DX'),
        ('CT Scan', 'CT', 'Computed tomography', 'CT'),
        ('MRI', 'MR', 'Magnetic resonance imaging', 'MR'),
        ('Ultrasound', 'US', 'Diagnostic ultrasound', 'US'),
        ('Mammography', 'MG', 'Breast imaging', 'MG'),
        ('PET Scan', 'PT', 'Positron emission tomography', 'PT'),
        ('Echocardiography', 'EC', 'Cardiac ultrasound', 'US'),
        ('Fluoroscopy', 'RF', 'Real-time X-ray imaging', 'RF'),
        ('DEXA', 'BA', 'Bone density scan', 'DX'),
    ]
    for name, code, desc, dicom in modalities:
        mod = ImagingModality(name=name, code=code, description=desc, dicom_modality_code=dicom)
        db.session.add(mod)

    db.session.commit()

    # Create lab test catalog
    lab_tests = [
        ('CBC', 'Complete Blood Count', 'hematology', 'Blood cell counts', 'blood', 'EDTA tube', 2, 50.0, '85025'),
        ('BMP', 'Basic Metabolic Panel', 'biochemistry', 'Electrolytes and kidney function', 'blood', 'SST tube', 4, 75.0, '80048'),
        ('CMP', 'Comprehensive Metabolic Panel', 'biochemistry', 'Extended metabolic panel', 'blood', 'SST tube', 4, 120.0, '80053'),
        ('Lipid Panel', 'Lipid Profile', 'biochemistry', 'Cholesterol and triglycerides', 'blood', 'SST tube', 6, 85.0, '80061'),
        ('TSH', 'Thyroid Stimulating Hormone', 'endocrinology', 'Thyroid function', 'blood', 'SST tube', 6, 55.0, '84443'),
        ('T4', 'Thyroxine', 'endocrinology', 'Thyroid hormone level', 'blood', 'SST tube', 6, 45.0, '84436'),
        ('T3', 'Triiodothyronine', 'endocrinology', 'Thyroid hormone level', 'blood', 'SST tube', 6, 50.0, '84481'),
        ('Liver Function', 'Liver Function Panel', 'biochemistry', 'Liver enzymes and proteins', 'blood', 'SST tube', 6, 110.0, '80076'),
        ('Kidney Function', 'Kidney Function Panel', 'biochemistry', 'Renal function tests', 'blood', 'SST tube', 4, 95.0, '80069'),
        ('PT/INR', 'Prothrombin Time/INR', 'coagulation', 'Blood clotting test', 'blood', 'Citrate tube', 4, 40.0, '85610'),
        ('aPTT', 'Activated Partial Thromboplastin Time', 'coagulation', 'Coagulation test', 'blood', 'Citrate tube', 4, 45.0, '85730'),
        ('Urinalysis', 'Complete Urinalysis', 'biochemistry', 'Urine analysis', 'urine', 'Sterile cup', 2, 35.0, '81001'),
        ('Urine Culture', 'Urine Culture', 'microbiology', 'Bacterial urine culture', 'urine', 'Sterile cup', 48, 80.0, '87088'),
        ('Blood Culture', 'Blood Culture', 'microbiology', 'Bacterial blood culture', 'blood', 'Blood culture bottles', 72, 150.0, '87040'),
        ('COVID-19 PCR', 'COVID-19 PCR Test', 'microbiology', 'SARS-CoV-2 detection', 'swab', 'Viral transport media', 24, 125.0, 'U0003'),
        ('Vitamin D', '25-OH Vitamin D', 'endocrinology', 'Vitamin D level', 'blood', 'SST tube', 24, 95.0, '82306'),
        ('Vitamin B12', 'Vitamin B12', 'endocrinology', 'B12 level', 'blood', 'SST tube', 24, 75.0, '82607'),
        ('Ferritin', 'Ferritin', 'hematology', 'Iron stores', 'blood', 'SST tube', 6, 65.0, '82728'),
        ('Iron Panel', 'Iron Studies', 'hematology', 'Iron, TIBC, transferrin', 'blood', 'SST tube', 6, 110.0, '83540'),
        ('CRP', 'C-Reactive Protein', 'immunology', 'Inflammation marker', 'blood', 'SST tube', 6, 55.0, '86140'),
        ('ESR', 'Erythrocyte Sedimentation Rate', 'hematology', 'Inflammation marker', 'blood', 'EDTA tube', 4, 35.0, '85652'),
        ('Troponin', 'Troponin I', 'immunology', 'Cardiac marker', 'blood', 'Heparin tube', 2, 125.0, '84484'),
        ('BNP', 'Brain Natriuretic Peptide', 'immunology', 'Heart failure marker', 'blood', 'EDTA tube', 4, 145.0, '83880'),
        ('PSA', 'Prostate Specific Antigen', 'immunology', 'Prostate cancer screening', 'blood', 'SST tube', 6, 95.0, '84153'),
        ('CEA', 'Carcinoembryonic Antigen', 'immunology', 'Tumor marker', 'blood', 'SST tube', 24, 110.0, '82378'),
        ('CA-125', 'Cancer Antigen 125', 'immunology', 'Ovarian cancer marker', 'blood', 'SST tube', 24, 125.0, '86304'),
        ('Stool Culture', 'Stool Culture', 'microbiology', 'Bacterial stool culture', 'stool', 'Stool container', 72, 120.0, '87046'),
        ('Ova & Parasite', 'Ova and Parasite Exam', 'microbiology', 'Parasite detection', 'stool', 'Stool container', 48, 85.0, '87177'),
        ('H. pylori', 'H. pylori Test', 'microbiology', 'Helicobacter pylori', 'stool', 'Stool container', 24, 95.0, '87338'),
    ]

    for code, name, category, desc, specimen, container, tat, cost, cpt in lab_tests:
        existing = LabTestCatalog.query.filter_by(code=code, name=name).first()
        if not existing:
            test = LabTestCatalog(
                code=code, name=name, category=category, description=desc,
                specimen_type=specimen, container_type=container,
                turnaround_time_hours=tat, cost=cost, cpt_code=cpt
            )
            db.session.add(test)

    db.session.commit()

    # Add some common medications
    medications = [
        ('Amoxicillin', 'Amoxicillin', 'Amoxil', 'Capsule', '500mg', 'Antibiotic', 'J01CA04', 1000, 50, 'capsules', 0.15, 0.50, 'Generic Pharma'),
        ('Azithromycin', 'Azithromycin', 'Zithromax', 'Tablet', '250mg', 'Antibiotic', 'J01FA10', 500, 25, 'tablets', 0.50, 1.50, 'Generic Pharma'),
        ('Ibuprofen', 'Ibuprofen', 'Advil', 'Tablet', '400mg', 'NSAID', 'M01AE01', 2000, 100, 'tablets', 0.05, 0.20, 'Generic Pharma'),
        ('Paracetamol', 'Paracetamol', 'Tylenol', 'Tablet', '500mg', 'Analgesic', 'N02BE01', 3000, 150, 'tablets', 0.03, 0.10, 'Generic Pharma'),
        ('Omeprazole', 'Omeprazole', 'Prilosec', 'Capsule', '20mg', 'PPI', 'A02BC01', 1000, 50, 'capsules', 0.20, 0.75, 'Generic Pharma'),
        ('Metformin', 'Metformin', 'Glucophage', 'Tablet', '500mg', 'Antidiabetic', 'A10BA02', 2000, 100, 'tablets', 0.10, 0.40, 'Generic Pharma'),
        ('Amlodipine', 'Amlodipine', 'Norvasc', 'Tablet', '5mg', 'Antihypertensive', 'C08CA01', 1000, 50, 'tablets', 0.15, 0.60, 'Generic Pharma'),
        ('Atorvastatin', 'Atorvastatin', 'Lipitor', 'Tablet', '20mg', 'Statin', 'C10AA05', 1000, 50, 'tablets', 0.25, 1.00, 'Generic Pharma'),
        ('Metoprolol', 'Metoprolol', 'Lopressor', 'Tablet', '50mg', 'Beta-blocker', 'C07AB02', 1000, 50, 'tablets', 0.20, 0.80, 'Generic Pharma'),
        ('Losartan', 'Losartan', 'Cozaar', 'Tablet', '50mg', 'ARB', 'C09CA01', 1000, 50, 'tablets', 0.30, 1.10, 'Generic Pharma'),
        ('Salbutamol', 'Salbutamol', 'Ventolin', 'Inhaler', '100mcg', 'Bronchodilator', 'R03AC02', 200, 20, 'inhalers', 2.00, 8.00, 'Generic Pharma'),
        ('Insulin Glargine', 'Insulin glargine', 'Lantus', 'Injection', '100U/mL', 'Insulin', 'A10AE04', 100, 10, 'vials', 15.00, 45.00, 'Sanofi'),
        ('Warfarin', 'Warfarin', 'Coumadin', 'Tablet', '5mg', 'Anticoagulant', 'B01AA03', 500, 25, 'tablets', 0.30, 1.20, 'Generic Pharma'),
        ('Ciprofloxacin', 'Ciprofloxacin', 'Cipro', 'Tablet', '500mg', 'Antibiotic', 'J01MA02', 500, 25, 'tablets', 0.40, 1.50, 'Generic Pharma'),
        ('Prednisone', 'Prednisone', 'Deltasone', 'Tablet', '10mg', 'Corticosteroid', 'H02AB07', 500, 25, 'tablets', 0.25, 0.90, 'Generic Pharma'),
    ]

    for name, generic, brand, form, strength, drug_class, atc, stock, reorder, unit, cost, price, mfg in medications:
        med = Medication(
            name=name, generic_name=generic, brand_name=brand,
            form=form, strength=strength, drug_class=drug_class,
            atc_code=atc, stock_quantity=stock, reorder_level=reorder,
            unit=unit, cost_price=cost, selling_price=price, manufacturer=mfg
        )
        db.session.add(med)

    db.session.commit()

    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@ihis-health.com',
        first_name='System',
        last_name='Administrator',
        phone='+1-555-0100',
        role='superadmin',
        role_id=roles['superadmin'].id,
        is_active=True,
        is_verified=True,
        last_login=datetime.utcnow()
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)

    # Create sample users for each role
    sample_users = [
        ('doctor1', 'doctor@ihis-health.com', 'John', 'Smith', 'doctor', 'doctor'),
        ('labtech1', 'lab@ihis-health.com', 'Sarah', 'Johnson', 'lab_tech', 'lab_tech'),
        ('radiologist1', 'radiology@ihis-health.com', 'Michael', 'Chen', 'radiologist', 'radiologist'),
        ('pharmacist1', 'pharmacy@ihis-health.com', 'Emily', 'Davis', 'pharmacist', 'pharmacist'),
        ('dentist1', 'dental@ihis-health.com', 'Robert', 'Wilson', 'dentist', 'dentist'),
        ('therapist1', 'therapy@ihis-health.com', 'Lisa', 'Anderson', 'therapist', 'therapist'),
        ('nurse1', 'nurse@ihis-health.com', 'James', 'Brown', 'nurse', 'nurse'),
        ('reception1', 'reception@ihis-health.com', 'Maria', 'Garcia', 'receptionist', 'receptionist'),
        ('admin1', 'hospital.admin@ihis-health.com', 'David', 'Lee', 'admin', 'admin'),
    ]

    created_users = {}
    for username, email, first, last, role_name, role_key in sample_users:
        user = User(
            username=username,
            email=email,
            first_name=first,
            last_name=last,
            phone=f'+1-555-{hash(username) % 9000 + 1000}',
            role=role_name,
            role_id=roles[role_key].id if role_key in roles else None,
            is_active=True,
            is_verified=True
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        created_users[role_name] = user

    db.session.commit()

    # Create doctor profile
    dept_im = Department.query.filter_by(code='IM').first()
    spec_im = Specialty.query.filter_by(name='Internal Medicine').first()
    if dept_im and spec_im and 'doctor' in created_users:
        doctor = Doctor(
            user_id=created_users['doctor'].id,
            employee_id='DOC001',
            license_number='MD12345678',
            primary_specialty_id=spec_im.id,
            department_id=dept_im.id,
            qualification='MD, Board Certified Internal Medicine',
            years_of_experience=12,
            consultation_duration_minutes=30,
            max_patients_per_day=20,
            status='active',
            joined_date=date(2015, 3, 1)
        )
        db.session.add(doctor)

    # Create nurse profile
    dept_icu = Department.query.filter_by(code='ICU').first()
    if dept_icu and 'nurse' in created_users:
        nurse = Nurse(
            user_id=created_users['nurse'].id,
            employee_id='NUR001',
            nursing_license='RN98765432',
            department_id=dept_icu.id,
            specialization='ICU',
            shift_preference='rotating',
            years_of_experience=8
        )
        db.session.add(nurse)

    # Create dentist profile
    dept_dent = Department.query.filter_by(code='DENT').first()
    if dept_dent and 'dentist' in created_users:
        gen_dent = DentalSpecialty.query.filter_by(name='General Dentistry').first()
        if gen_dent:
            dentist = Dentist(
                user_id=created_users['dentist'].id,
                dental_license='DDS87654321',
                dental_specialty_id=gen_dent.id
            )
            db.session.add(dentist)

    # Create therapist profile
    dept_pt = Department.query.filter_by(code='PT').first()
    if dept_pt and 'therapist' in created_users:
        pt_spec = TherapySpecialty.query.filter_by(name='Physical Therapy').first()
        if pt_spec:
            therapist = PhysicalTherapist(
                user_id=created_users['therapist'].id,
                therapist_license='PT76543210',
                specialty_id=pt_spec.id,
                years_of_experience=6,
                certifications='Manual Therapy, Sports Rehabilitation'
            )
            db.session.add(therapist)

    # Create sample patients
    patients_data = [
        ('PT001', 'James', 'Anderson', date(1985, 5, 15), 'male', 'O+', 'james.anderson@email.com', '555-2001'),
        ('PT002', 'Mary', 'Johnson', date(1972, 8, 22), 'female', 'A+', 'mary.johnson@email.com', '555-2002'),
        ('PT003', 'Robert', 'Williams', date(1990, 3, 10), 'male', 'B+', 'robert.w@email.com', '555-2003'),
        ('PT004', 'Patricia', 'Brown', date(1965, 11, 28), 'female', 'AB-', 'patricia.b@email.com', '555-2004'),
        ('PT005', 'Michael', 'Davis', date(1958, 7, 4), 'male', 'O-', 'michael.d@email.com', '555-2005'),
        ('PT006', 'Linda', 'Miller', date(1988, 1, 18), 'female', 'A-', 'linda.m@email.com', '555-2006'),
        ('PT007', 'William', 'Wilson', date(1978, 9, 30), 'male', 'B-', 'william.w@email.com', '555-2007'),
        ('PT008', 'Elizabeth', 'Moore', date(1995, 4, 12), 'female', 'O+', 'elizabeth.m@email.com', '555-2008'),
        ('PT009', 'David', 'Taylor', date(1960, 12, 25), 'male', 'A+', 'david.t@email.com', '555-2009'),
        ('PT010', 'Jennifer', 'Anderson', date(1982, 6, 8), 'female', 'AB+', 'jennifer.a@email.com', '555-2010'),
    ]

    for pat_id, first, last, dob, gender, blood, email, phone in patients_data:
        patient = Patient(
            patient_id=pat_id,
            first_name=first,
            last_name=last,
            date_of_birth=dob,
            gender=gender,
            blood_type=blood,
            email=email,
            phone_primary=phone,
            address=f'{hash(first) % 9999 + 1} Main Street',
            city='Healthcare City',
            state='CA',
            zip_code=f'{90000 + hash(first) % 9999}',
            country='USA',
            emergency_contact_name=f'Emergency Contact {first}',
            emergency_contact_phone=f'555-3{phone[-3:]}',
            emergency_contact_relationship='Spouse',
            height_cm=170 + hash(first) % 20,
            weight_kg=65 + hash(first) % 30,
            insurance_provider='BlueCross Health',
            insurance_policy_number=f'BC{hash(first) % 1000000:06d}'
        )
        patient.calculate_bmi()
        db.session.add(patient)

    db.session.commit()

    # Add sample allergies for first patient
    first_patient = Patient.query.filter_by(patient_id='PT001').first()
    if first_patient:
        from models.patient import Allergy, ChronicDisease
        allergy = Allergy(
            patient_id=first_patient.id,
            allergen='Penicillin',
            allergy_type='drug',
            severity='severe',
            reaction='Hives, difficulty breathing',
            onset_date=date(2000, 1, 15)
        )
        db.session.add(allergy)

        chronic = ChronicDisease(
            patient_id=first_patient.id,
            condition='Type 2 Diabetes Mellitus',
            icd10_code='E11.9',
            diagnosed_date=date(2015, 6, 1),
            status='active',
            severity='moderate'
        )
        db.session.add(chronic)

    db.session.commit()

    # Create doctor schedule
    doctor = Doctor.query.first()
    if doctor:
        for day in range(5):  # Mon-Fri
            schedule = DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                is_available=True,
                max_appointments=8,
                location=f'Room {101 + day}'
            )
            db.session.add(schedule)

    db.session.commit()

    # Create sample appointments
    doctor_record = Doctor.query.first()
    if doctor_record and first_patient:
        from models.doctor import Appointment
        for i in range(5):
            appt_date = date.today() + timedelta(days=i)
            appt = Appointment(
                appointment_number=f'APT{20240001 + i}',
                patient_id=first_patient.id,
                doctor_id=doctor_record.id,
                scheduled_date=appt_date,
                scheduled_time=time(10 + i, 0),
                duration_minutes=30,
                appointment_type='consultation' if i == 0 else 'follow_up',
                reason=f'Follow-up consultation #{i+1}' if i > 0 else 'Initial consultation',
                status='scheduled'
            )
            db.session.add(appt)

    db.session.commit()

    print("Database seeding completed successfully!")
