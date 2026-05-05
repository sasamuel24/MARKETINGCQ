"""create_iniciativas_notificaciones_tokens

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-04-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Tabla iniciativas ──────────────────────────────────────────────────
    op.create_table(
        'iniciativas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('producto_propuesto', sa.Text(), nullable=False),
        sa.Column('analisis_competencia', sa.Text(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('business_case_path', sa.String(length=500), nullable=True),
        sa.Column(
            'status',
            sa.Enum(
                'BORRADOR', 'PENDIENTE_GG', 'APROBADA_GG', 'RECHAZADA_GG',
                'EN_PROTOTIPADO', 'PENDIENTE_APROBACION_DUAL',
                'PENDIENTE_JD', 'APROBADA_JD', 'RECHAZADA_JD',
                name='iniciativastatus',
            ),
            nullable=False,
            server_default='BORRADOR',
        ),
        sa.Column('luisa_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('gerente_tiendas_approved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('approved_by_gg_user_id', sa.Integer(), nullable=True),
        sa.Column('solicitud_id', sa.Integer(), nullable=True),
        sa.Column('solicitud_innovacion_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['usuarios.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approved_by_gg_user_id'], ['usuarios.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['solicitud_innovacion_id'], ['solicitudes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_iniciativas_id', 'iniciativas', ['id'], unique=False)
    op.create_index('ix_iniciativas_created_by_user_id', 'iniciativas', ['created_by_user_id'], unique=False)
    op.create_index('ix_iniciativas_status', 'iniciativas', ['status'], unique=False)

    # ── Tabla approval_tokens ──────────────────────────────────────────────
    op.create_table(
        'approval_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token', sa.String(length=36), nullable=False),
        sa.Column('iniciativa_id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column(
            'action',
            sa.Enum('PENDIENTE', 'APROBADO', 'RECHAZADO', name='approvaltokenaction'),
            nullable=False,
            server_default='PENDIENTE',
        ),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['iniciativa_id'], ['iniciativas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token', name='uq_approval_tokens_token'),
    )
    op.create_index('ix_approval_tokens_id', 'approval_tokens', ['id'], unique=False)
    op.create_index('ix_approval_tokens_token', 'approval_tokens', ['token'], unique=True)
    op.create_index('ix_approval_tokens_iniciativa_id', 'approval_tokens', ['iniciativa_id'], unique=False)

    # ── Tabla notificaciones ───────────────────────────────────────────────
    op.create_table(
        'notificaciones',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=50), nullable=False),
        sa.Column('titulo', sa.String(length=255), nullable=False),
        sa.Column('mensaje', sa.Text(), nullable=False),
        sa.Column('leida', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('iniciativa_id', sa.Integer(), nullable=True),
        sa.Column('solicitud_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['iniciativa_id'], ['iniciativas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['solicitud_id'], ['solicitudes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notificaciones_id', 'notificaciones', ['id'], unique=False)
    op.create_index('ix_notificaciones_user_id', 'notificaciones', ['user_id'], unique=False)
    op.create_index('ix_notificaciones_leida', 'notificaciones', ['leida'], unique=False)


def downgrade() -> None:
    op.drop_table('notificaciones')
    op.drop_table('approval_tokens')
    op.drop_table('iniciativas')
    op.execute("DROP TYPE IF EXISTS iniciativastatus")
    op.execute("DROP TYPE IF EXISTS approvaltokenaction")
