"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-09-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, index=True),
        sa.Column('full_name', sa.String(255)),
        sa.Column('hashed_password', sa.String(255)),
        sa.Column('role', sa.String(32), index=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'customers',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('first_name', sa.String(120)),
        sa.Column('last_name', sa.String(120)),
        sa.Column('national_id', sa.String(20), index=True, nullable=True),
        sa.Column('passport_number', sa.String(40), index=True, nullable=True),
        sa.Column('birth_date', sa.String(16), nullable=True),
        sa.Column('gender', sa.String(16), nullable=True),
        sa.Column('nationality', sa.String(80), default='ایران'),
        sa.Column('province', sa.String(80), nullable=True),
        sa.Column('city', sa.String(80), nullable=True),
        sa.Column('address', sa.Text, nullable=True),
        sa.Column('phone', sa.String(32), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('overall_risk_score', sa.Integer, default=0),
        sa.Column('overall_risk_level', sa.String(16), default='low'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'customer_notes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), index=True),
        sa.Column('author_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('body', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'applications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_number', sa.String(32), unique=True, index=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), index=True),
        sa.Column('status', sa.String(32), index=True, default='draft'),
        sa.Column('source', sa.String(32), default='web'),
        sa.Column('current_step', sa.String(32), default='personal'),
        sa.Column('declared_income', sa.String(80), nullable=True),
        sa.Column('source_of_funds', sa.String(120), nullable=True),
        sa.Column('occupation', sa.String(120), nullable=True),
        sa.Column('expected_volume', sa.String(80), nullable=True),
        sa.Column('jurisdiction', sa.String(80), default='ایران'),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_app_status_created', 'applications', ['status', 'created_at'])
    op.create_table(
        'application_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('kind', sa.String(64)),
        sa.Column('message', sa.Text),
        sa.Column('payload', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'documents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), index=True),
        sa.Column('doc_type', sa.String(32), index=True),
        sa.Column('status', sa.String(32), default='uploaded'),
        sa.Column('original_filename', sa.String(255)),
        sa.Column('content_type', sa.String(80)),
        sa.Column('size_bytes', sa.Integer),
        sa.Column('storage_key', sa.String(512)),
        sa.Column('is_simulated', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'document_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id'), index=True),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('storage_key', sa.String(512)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'extracted_fields',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('document_id', sa.String(36), sa.ForeignKey('documents.id'), index=True),
        sa.Column('field_name', sa.String(64)),
        sa.Column('field_label', sa.String(80)),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('confidence', sa.Float, default=0),
        sa.Column('confirmed', sa.Boolean, default=False),
    )
    op.create_table(
        'verifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('kind', sa.String(32)),
        sa.Column('status', sa.String(32)),
        sa.Column('score', sa.Float, nullable=True),
        sa.Column('details', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'face_verifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('similarity', sa.Float),
        sa.Column('quality_score', sa.Float),
        sa.Column('confidence', sa.Float),
        sa.Column('decision', sa.String(32)),
        sa.Column('reasons', sa.JSON, nullable=True),
        sa.Column('liveness_ready', sa.Boolean, default=True),
        sa.Column('is_simulated', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('score', sa.Integer),
        sa.Column('level', sa.String(16), index=True),
        sa.Column('recommended_decision', sa.String(48)),
        sa.Column('explanation', sa.Text),
        sa.Column('policy_version_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'risk_factors',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('assessment_id', sa.String(36), sa.ForeignKey('risk_assessments.id'), index=True),
        sa.Column('code', sa.String(64)),
        sa.Column('label', sa.String(160)),
        sa.Column('weight', sa.Integer),
        sa.Column('triggered', sa.Boolean),
        sa.Column('detail', sa.Text),
    )
    op.create_table(
        'screening_results',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('kind', sa.String(32), index=True),
        sa.Column('matched', sa.Boolean, default=False),
        sa.Column('score', sa.Float, default=0),
        sa.Column('list_name', sa.String(120), nullable=True),
        sa.Column('matched_name', sa.String(255), nullable=True),
        sa.Column('is_simulated', sa.Boolean, default=True),
        sa.Column('payload', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'policies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('code', sa.String(64), unique=True),
        sa.Column('title', sa.String(255)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'policy_versions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('policy_id', sa.String(36), sa.ForeignKey('policies.id'), index=True),
        sa.Column('version', sa.String(32)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('body', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'policy_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('version_id', sa.String(36), sa.ForeignKey('policy_versions.id'), index=True),
        sa.Column('clause', sa.String(32)),
        sa.Column('section', sa.String(160)),
        sa.Column('text', sa.Text),
        sa.Column('embedding', sa.JSON, nullable=True),
    )
    op.create_table(
        'cases',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('case_number', sa.String(32), unique=True, index=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), index=True),
        sa.Column('status', sa.String(32), index=True, default='open'),
        sa.Column('priority', sa.String(16), default='normal'),
        sa.Column('risk_level', sa.String(16), default='medium'),
        sa.Column('assigned_to', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('sla_hours', sa.Integer, default=48),
        sa.Column('sla_due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision', sa.String(48), nullable=True),
        sa.Column('decision_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_case_status_priority', 'cases', ['status', 'priority'])
    op.create_table(
        'case_assignments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('cases.id'), index=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'reviews',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('case_id', sa.String(36), sa.ForeignKey('cases.id'), index=True),
        sa.Column('reviewer_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('action', sa.String(32)),
        sa.Column('reason', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), sa.ForeignKey('applications.id'), index=True),
        sa.Column('code', sa.String(48)),
        sa.Column('source', sa.String(32)),
        sa.Column('reason', sa.Text),
        sa.Column('policy_clauses', sa.JSON, nullable=True),
        sa.Column('actor_id', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('actor_id', sa.String(36), index=True, nullable=True),
        sa.Column('actor_role', sa.String(32), nullable=True),
        sa.Column('action', sa.String(80), index=True),
        sa.Column('entity', sa.String(64), index=True),
        sa.Column('entity_id', sa.String(36), index=True),
        sa.Column('previous_state', sa.JSON, nullable=True),
        sa.Column('new_state', sa.JSON, nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('ip', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('policy_version', sa.String(32), nullable=True),
        sa.Column('model_version', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_audit_entity', 'audit_events', ['entity', 'entity_id'])
    op.create_table(
        'notifications',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True),
        sa.Column('title', sa.String(160)),
        sa.Column('body', sa.Text),
        sa.Column('kind', sa.String(48)),
        sa.Column('read', sa.Boolean, default=False),
        sa.Column('payload', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('kind', sa.String(64), index=True),
        sa.Column('status', sa.String(32), default='queued'),
        sa.Column('progress', sa.Integer, default=0),
        sa.Column('stage', sa.String(80), default='queued'),
        sa.Column('entity_id', sa.String(36), index=True, nullable=True),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'ai_evaluations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('application_id', sa.String(36), index=True, nullable=True),
        sa.Column('model_name', sa.String(80)),
        sa.Column('model_version', sa.String(40)),
        sa.Column('prompt_version', sa.String(40)),
        sa.Column('policy_version', sa.String(40), nullable=True),
        sa.Column('retrieved_evidence', sa.JSON, nullable=True),
        sa.Column('output', sa.Text),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('reviewer_outcome', sa.String(48), nullable=True),
        sa.Column('overridden', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), index=True),
        sa.Column('token_hash', sa.String(128), unique=True),
        sa.Column('revoked', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table('refresh_tokens')
    op.drop_table('ai_evaluations')
    op.drop_table('jobs')
    op.drop_table('notifications')
    op.drop_table('audit_events')
    op.drop_table('decisions')
    op.drop_table('reviews')
    op.drop_table('case_assignments')
    op.drop_table('cases')
    op.drop_table('policy_chunks')
    op.drop_table('policy_versions')
    op.drop_table('policies')
    op.drop_table('screening_results')
    op.drop_table('risk_factors')
    op.drop_table('risk_assessments')
    op.drop_table('face_verifications')
    op.drop_table('verifications')
    op.drop_table('extracted_fields')
    op.drop_table('document_versions')
    op.drop_table('documents')
    op.drop_table('application_events')
    op.drop_table('applications')
    op.drop_table('customer_notes')
    op.drop_table('customers')
    op.drop_table('users')
