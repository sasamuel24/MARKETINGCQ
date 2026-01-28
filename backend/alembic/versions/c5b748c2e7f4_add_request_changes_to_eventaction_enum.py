"""add_request_changes_to_eventaction_enum

Revision ID: c5b748c2e7f4
Revises: 27a177da8a2e
Create Date: 2026-01-27 09:41:06.310890

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5b748c2e7f4'
down_revision = '27a177da8a2e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agregar nuevo valor al enum eventaction
    op.execute("ALTER TYPE eventaction ADD VALUE 'REQUEST_CHANGES'")


def downgrade() -> None:
    # No se puede eliminar un valor de enum en PostgreSQL sin recrear el tipo
    # Esta operación no es reversible de forma simple
    pass
