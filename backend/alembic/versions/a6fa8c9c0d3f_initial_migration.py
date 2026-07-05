"""initial migration

Revision ID: a6fa8c9c0d3f
Revises: 
Create Date: 2026-07-05 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a6fa8c9c0d3f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

    # 2. Roles Table
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('permissions', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 3. Users Table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # 4. Departments Table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('name')
    )

    # 5. Audit Templates Table
    op.create_table(
        'audit_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Question Groups Table
    op.create_table(
        'question_groups',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('order_num', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['audit_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id', 'order_num')
    )

    # 7. Questions Table
    op.create_table(
        'questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('group_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('response_type', sa.Enum('RADIO', 'CHECKBOX', 'DROPDOWN', 'TEXT', 'LONG_TEXT', 'NUMBER', 'DATE', 'IMAGE_UPLOAD', 'SIGNATURE', 'BARCODE', 'QR_SCAN', name='response_type_enum'), nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('compliance_weight', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_required', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('order_num', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['question_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'order_num')
    )

    # 8. Audits Table
    op.create_table(
        'audits',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('auditor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'REVIEWED', name='audit_status_enum'), nullable=False),
        sa.Column('compliance_percentage', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('overall_score', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('risk_level', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risk_level_enum'), nullable=False),
        sa.Column('gps_latitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('gps_longitude', sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('audited_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['auditor_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['template_id'], ['audit_templates.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audits_department', 'audits', ['department_id'], unique=False)
    op.create_index('idx_audits_status', 'audits', ['status'], unique=False)

    # 9. Audit Responses Table
    op.create_table(
        'audit_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('answer', sa.String(length=2000), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), server_default='0.00', nullable=False),
        sa.Column('remarks', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('audit_id', 'question_id')
    )

    # 10. Audit Response Media Table
    op.create_table(
        'audit_response_media',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('media_type', sa.Enum('IMAGE', 'VIDEO', 'AUDIO', name='media_type_enum'), nullable=False),
        sa.Column('original_url', sa.String(length=1000), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=1000), nullable=True),
        sa.Column('compressed_url', sa.String(length=1000), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('media_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['response_id'], ['audit_responses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. Capas Table
    op.create_table(
        'capas',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('deadline', sa.Date(), nullable=False),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='risk_level_enum', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'OPEN', 'CLOSED', name='capa_status_enum'), nullable=False),
        sa.Column('root_cause_analysis', sa.Text(), nullable=True),
        sa.Column('corrective_action', sa.Text(), nullable=True),
        sa.Column('preventive_action', sa.Text(), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['audit_id'], ['audits.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_capas_department', 'capas', ['department_id'], unique=False)
    op.create_index('idx_capas_status', 'capas', ['status'], unique=False)

    # 12. Capa Evidence Table
    op.create_table(
        'capa_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('capa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_url', sa.String(length=1000), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['capa_id'], ['capas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )

    # 13. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_name', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 14. Login History Table
    op.create_table(
        'login_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 15. Device Logs Table
    op.create_table(
        'device_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('device_os', sa.String(length=50), nullable=True),
        sa.Column('app_version', sa.String(length=20), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. Notifications Table
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=150), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('channel', sa.Enum('IN_APP', 'EMAIL', 'WHATSAPP', 'SMS', name='notify_channel_enum'), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. Seed Initial Master Data (Roles, Departments, Templates, default Admin)
    # Insert Roles
    op.execute("""
        INSERT INTO roles (name, description, permissions) VALUES
        ('SUPER ADMIN', 'Super user with system-wide settings configurations', '{"modules": {"users": ["read", "write"], "checklists": ["read", "write"], "audits": ["read", "write"], "capa": ["read", "write", "approve"], "reports": ["read"]}}'),
        ('HOSPITAL ADMIN', 'Hospital administrator managing users and templates', '{"modules": {"users": ["read", "write"], "checklists": ["read", "write"], "audits": ["read"], "capa": ["read"], "reports": ["read"]}}'),
        ('CEO', 'Executive management read-only metrics dashboard', '{"modules": {"audits": ["read"], "capa": ["read"], "reports": ["read"]}}'),
        ('CHO', 'Chief Hospital Officer read-only access', '{"modules": {"audits": ["read"], "capa": ["read"], "reports": ["read"]}}'),
        ('ICO', 'Infection Control Officer executing checklists and managing actions', '{"modules": {"checklists": ["read"], "audits": ["read", "write"], "capa": ["read", "write"], "reports": ["read"]}}'),
        ('QUALITY MANAGER', 'Quality officer overseeing compliance and CAPA closure', '{"modules": {"checklists": ["read"], "audits": ["read"], "capa": ["read", "write", "approve"], "reports": ["read"]}}'),
        ('DOCTOR IN CHARGE', 'Department representative tracking actions', '{"modules": {"audits": ["read"], "capa": ["read", "write"]}}'),
        ('NURSING SUPERINTENDENT', 'Head nurse reviewing ward audits', '{"modules": {"audits": ["read", "write"], "capa": ["read", "write"]}}'),
        ('ICU HEAD', 'ICU representative responding to CAPAs', '{"modules": {"audits": ["read"], "capa": ["read", "write"]}}'),
        ('OT HEAD', 'OT representative responding to CAPAs', '{"modules": {"audits": ["read"], "capa": ["read", "write"]}}'),
        ('LAB DIRECTOR', 'Lab safety auditor and response lead', '{"modules": {"audits": ["read", "write"], "capa": ["read", "write"]}}'),
        ('DEPARTMENT HEAD', 'General department lead tracking checklists', '{"modules": {"audits": ["read"], "capa": ["read", "write"]}}'),
        ('BIOMEDICAL WASTE OFFICER', 'Waste tracking audits execution lead', '{"modules": {"audits": ["read", "write"], "capa": ["read", "write"]}}'),
        ('AUDITOR', 'Third party or clinical workflow auditor', '{"modules": {"audits": ["read", "write"], "reports": ["read"]}}'),
        ('READ ONLY MANAGEMENT', 'Management user read-only access', '{"modules": {"audits": ["read"], "reports": ["read"]}}')
    """)

    # Insert default super admin user (password is 'adminpassword123')
    op.execute("""
        INSERT INTO users (email, hashed_password, full_name, role_id, is_active)
        VALUES ('admin@hospital.com', '$2b$12$9xCii5OdjeJB3d9UpeSuuuKL6jutm1RN4R/Hao0kgd2KPBD0E2LwG', 'System Administrator', (SELECT id FROM roles WHERE name='SUPER ADMIN'), true)
    """)

    # Insert Default Departments
    op.execute("""
        INSERT INTO departments (name, code) VALUES
        ('Intensive Care Unit', 'ICU'),
        ('Operation Theater', 'OT'),
        ('Outpatient Department', 'OPD'),
        ('Emergency Medicine', 'ER'),
        ('Clinical Laboratory', 'LAB'),
        ('General Ward A', 'WARD-A'),
        ('Biomedical Waste Facility', 'BMW')
    """)

    # Insert Default Checklist Template
    # Template: Hand Hygiene Compliance Audit
    template_id = 'e7a2b9d0-8f92-4f3b-823b-0bb56d2a71d2'
    op.execute(f"""
        INSERT INTO audit_templates (id, title, description, version, is_active, created_by)
        VALUES ('{template_id}', 'Hand Hygiene Compliance Audit', 'Standard NABH audit checklist monitoring Hand Hygiene protocols.', 1, true, (SELECT id FROM users WHERE email='admin@hospital.com'))
    """)

    # Group 1: Pre-requisites & Infrastructure
    group_1_id = 'c1a7d65b-c2e3-47a8-8e6d-74d32a9e3f71'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_1_id}', '{template_id}', '1. Hand Hygiene Infrastructure', 1)
    """)

    # Group 1 Questions
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_1_id}', 'Are handwash sinks clean, dry, and free of blockages?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 1),
        ('{group_1_id}', 'Is running tap water continuously available?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 2),
        ('{group_1_id}', 'Is liquid handwash soap available in a functional dispenser?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 3),
        ('{group_1_id}', 'Are clean, single-use paper towels or air dryers operational?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 4)
    """)

    # Group 2: Five Moments Compliance
    group_2_id = 'f9a2e6cb-3a78-43d9-9bb5-86ef2e09cb42'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_2_id}', '{template_id}', '2. Five Moments Compliance', 2)
    """)

    # Group 2 Questions
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_2_id}', 'Do staff perform hand hygiene before touching a patient?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 1),
        ('{group_2_id}', 'Do staff perform hand hygiene before clean/aseptic procedures?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 2),
        ('{group_2_id}', 'Do staff perform hand hygiene after body fluid exposure risk?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 3),
        ('{group_2_id}', 'Do staff perform hand hygiene after touching a patient?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 4),
        ('{group_2_id}', 'Do staff perform hand hygiene after touching patient surroundings?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 5)
    """)

    # PPE Template: Personal Protective Equipment Compliance Audit
    template_ppe_id = 'e8f9b9d0-8f92-4f3b-823b-0bb56d2a71d3'
    op.execute(f"""
        INSERT INTO audit_templates (id, title, description, version, is_active, created_by)
        VALUES ('{template_ppe_id}', 'PPE Compliance Audit', 'Monitors donning, doffing, stocking, and proper usage of PPE.', 1, true, (SELECT id FROM users WHERE email='admin@hospital.com'))
    """)
    group_ppe_1 = 'd1a7d65b-c2e3-47a8-8e6d-74d32a9e3f72'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_ppe_1}', '{template_ppe_id}', '1. PPE Infrastructure & Availability', 1)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_ppe_1}', 'Are PPE storage stations fully stocked with gloves, masks, and gowns?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 1),
        ('{group_ppe_1}', 'Are all PPE items available in appropriate sizes?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 2)
    """)
    group_ppe_2 = 'e9a2e6cb-3a78-43d9-9bb5-86ef2e09cb43'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_ppe_2}', '{template_ppe_id}', '2. Donning, Doffing & Disposal Protocol', 2)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_ppe_2}', 'Do staff perform hand hygiene before donning and after doffing PPE?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 1),
        ('{group_ppe_2}', 'Are used PPE discarded immediately in designated color-coded bins?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 2)
    """)

    # BMW Template: Biomedical Waste Management Audit
    template_bmw_id = 'e9a2b9d0-8f92-4f3b-823b-0bb56d2a71d4'
    op.execute(f"""
        INSERT INTO audit_templates (id, title, description, version, is_active, created_by)
        VALUES ('{template_bmw_id}', 'Biomedical Waste (BMW) Audit', 'Standard audit evaluating segregation, puncture-proof boxing, and safe transit.', 1, true, (SELECT id FROM users WHERE email='admin@hospital.com'))
    """)
    group_bmw_1 = 'e1a7d65b-c2e3-47a8-8e6d-74d32a9e3f73'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_bmw_1}', '{template_bmw_id}', '1. Waste Segregation & Coding', 1)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_bmw_1}', 'Are yellow bags used strictly for human anatomical waste and soiled linen?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 1),
        ('{group_bmw_1}', 'Are sharp containers/puncture-proof boxes used for needles and syringes?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 2)
    """)
    group_bmw_2 = 'f9a2e6cb-3a78-43d9-9bb5-86ef2e09cb44'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_bmw_2}', '{template_bmw_id}', '2. Labeling & Safe Transit', 2)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_bmw_2}', 'Are all waste bags sealed and labeled with date and ward code before transport?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 1),
        ('{group_bmw_2}', 'Is waste transported in covered, dedicated trolleys to storage area?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 2)
    """)

    # OT Template: Operation Theater Sterility Audit
    template_ot_id = 'f0a2b9d0-8f92-4f3b-823b-0bb56d2a71d5'
    op.execute(f"""
        INSERT INTO audit_templates (id, title, description, version, is_active, created_by)
        VALUES ('{template_ot_id}', 'Operation Theater Sterility Audit', 'Critical NABH compliance audit for OT HVAC air particulates, autoclaves and sterilizations.', 1, true, (SELECT id FROM users WHERE email='admin@hospital.com'))
    """)
    group_ot_1 = 'f1a7d65b-c2e3-47a8-8e6d-74d32a9e3f74'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_ot_1}', '{template_ot_id}', '1. Air Quality & Cleanliness', 1)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_ot_1}', 'Are OT humidity, temperature, and positive pressure levels monitored daily?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 1),
        ('{group_ot_1}', 'Is clean zone disinfection protocol fully completed between surgeries?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 2)
    """)
    group_ot_2 = 'a9a2e6cb-3a78-43d9-9bb5-86ef2e09cb45'
    op.execute(f"""
        INSERT INTO question_groups (id, template_id, title, order_num)
        VALUES ('{group_ot_2}', '{template_ot_id}', '2. Autoclave and Pack Sterilization', 2)
    """)
    op.execute(f"""
        INSERT INTO questions (group_id, text, response_type, options, compliance_weight, is_required, order_num) VALUES
        ('{group_ot_2}', 'Are biological/chemical validation indicators verified before opening instrument packs?', 'RADIO', '["Yes", "No", "N/A"]', 3, true, 1),
        ('{group_ot_2}', 'Are autoclave maintenance logs updated and certified monthly?', 'RADIO', '["Yes", "No", "N/A"]', 2, true, 2)
    """)


def downgrade() -> None:
    # Drop tables in reverse order of dependencies
    op.drop_table('notifications')
    op.drop_table('device_logs')
    op.drop_table('login_history')
    op.drop_table('audit_logs')
    op.drop_table('capa_evidence')
    op.drop_table('capas')
    op.drop_table('audit_response_media')
    op.drop_table('audit_responses')
    op.drop_table('audits')
    op.drop_table('questions')
    op.drop_table('question_groups')
    op.drop_table('audit_templates')
    op.drop_table('departments')
    op.drop_table('users')
    op.drop_table('roles')

    # Drop custom postgres enums
    op.execute("DROP TYPE notify_channel_enum")
    op.execute("DROP TYPE capa_status_enum")
    op.execute("DROP TYPE media_type_enum")
    op.execute("DROP TYPE risk_level_enum")
    op.execute("DROP TYPE audit_status_enum")
    op.execute("DROP TYPE response_type_enum")
