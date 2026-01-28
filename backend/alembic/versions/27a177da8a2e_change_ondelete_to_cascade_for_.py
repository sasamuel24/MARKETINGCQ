"""change_ondelete_to_cascade_for_solicitud_files_and_eventos

Revision ID: 27a177da8a2e
Revises: 6392fce3515a
Create Date: 2026-01-27 09:10:51.160728

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '27a177da8a2e'
down_revision = '6392fce3515a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cambiar foreign key de solicitud_files para que elimine en cascada
    op.drop_constraint('solicitud_files_solicitud_id_fkey', 'solicitud_files', type_='foreignkey')
    op.create_foreign_key(
        'solicitud_files_solicitud_id_fkey',
        'solicitud_files', 'solicitudes',
        ['solicitud_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Cambiar foreign key de solicitud_eventos para que elimine en cascada
    op.drop_constraint('solicitud_eventos_solicitud_id_fkey', 'solicitud_eventos', type_='foreignkey')
    op.create_foreign_key(
        'solicitud_eventos_solicitud_id_fkey',
        'solicitud_eventos', 'solicitudes',
        ['solicitud_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revertir foreign key de solicitud_files a RESTRICT
    op.drop_constraint('solicitud_files_solicitud_id_fkey', 'solicitud_files', type_='foreignkey')
    op.create_foreign_key(
        'solicitud_files_solicitud_id_fkey',
        'solicitud_files', 'solicitudes',
        ['solicitud_id'], ['id'],
        ondelete='RESTRICT'
    )
    
    # Revertir foreign key de solicitud_eventos a RESTRICT
    op.drop_constraint('solicitud_eventos_solicitud_id_fkey', 'solicitud_eventos', type_='foreignkey')
    op.create_foreign_key(
        'solicitud_eventos_solicitud_id_fkey',
        'solicitud_eventos', 'solicitudes',
        ['solicitud_id'], ['id'],
        ondelete='RESTRICT'
    )
