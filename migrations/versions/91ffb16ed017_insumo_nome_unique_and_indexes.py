"""insumo nome unique and indexes

Revision ID: 91ffb16ed017
Revises: 71cb919c0c45
Create Date: 2026-06-15 09:07:09.587171

"""
from alembic import op
import sqlalchemy as sa


revision = '91ffb16ed017'
down_revision = '71cb919c0c45'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('insumo', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_insumo_created_at'), ['created_at'], unique=False)
        batch_op.create_unique_constraint('uq_insumo_nome', ['nome'])


def downgrade():
    with op.batch_alter_table('insumo', schema=None) as batch_op:
        batch_op.drop_constraint('uq_insumo_nome', type_='unique')
        batch_op.drop_index(batch_op.f('ix_insumo_created_at'))