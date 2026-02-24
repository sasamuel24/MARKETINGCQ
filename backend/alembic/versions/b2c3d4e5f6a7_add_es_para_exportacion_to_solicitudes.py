"""add_es_para_exportacion_to_solicitudes

Revision ID: b2c3d4e5f6a7
Revises: a1e2f3c4d5b6
Create Date: 2026-02-24 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1e2f3c4d5b6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable porque solo aplica cuando el área es "Operaciones y Calidad"
    op.add_column('solicitudes', sa.Column('es_para_exportacion', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('solicitudes', 'es_para_exportacion')
