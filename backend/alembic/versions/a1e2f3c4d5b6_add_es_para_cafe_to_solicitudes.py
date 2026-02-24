"""add_es_para_cafe_to_solicitudes

Revision ID: a1e2f3c4d5b6
Revises: b03a6c09e7d3
Create Date: 2026-02-24 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1e2f3c4d5b6'
down_revision = 'b03a6c09e7d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable porque solo aplica cuando el área es "Operaciones y Calidad"
    op.add_column('solicitudes', sa.Column('es_para_cafe', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('solicitudes', 'es_para_cafe')
