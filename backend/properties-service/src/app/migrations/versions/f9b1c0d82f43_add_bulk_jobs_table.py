"""Add bulk jobs table

Revision ID: f9b1c0d82f43
Revises: 9d80aa711364
Create Date: 2026-07-27 21:37:03.563882

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9b1c0d82f43'
down_revision: Union[str, Sequence[str], None] = '9d80aa711364'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'bulk_jobs',
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('job_type', sa.Enum('bulk_create_properties', name='jobtype'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', name='jobstatus'), nullable=False),
        sa.Column('errors', postgresql.ARRAY(postgresql.JSONB(astext_type=sa.Text())), nullable=False),
        sa.Column('retry_of_job_id', sa.Uuid(), nullable=True),
        sa.Column('storage_key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['retry_of_job_id'], ['bulk_jobs.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_bulk_jobs_id'), 'bulk_jobs', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_bulk_jobs_id'), table_name='bulk_jobs')
    op.drop_table('bulk_jobs')
    # create_table emitted these enum types; dropping the table does not remove them
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='jobtype').drop(op.get_bind(), checkfirst=True)
