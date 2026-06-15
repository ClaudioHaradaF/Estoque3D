"""add is_admin to usuario

Revision ID: a1b2c3d4e5f6
Revises: 91ffb16ed017
Create Date: 2026-06-15 09:11:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'a1b2c3d4e5f6'
down_revision = '91ffb16ed017'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("PRAGMA table_info(usuario)")
    conn = op.get_bind()
    result = conn.execute(sa.text("PRAGMA table_info('usuario')")).fetchall()
    cols = [row[1] for row in result]
    if 'is_admin' not in cols:
        with op.batch_alter_table('usuario') as batch_op:
            batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        op.execute("UPDATE usuario SET is_admin = 1 WHERE email = 'harborio3d@gmail.com'")


def downgrade():
    with op.batch_alter_table('usuario') as batch_op:
        batch_op.drop_column('is_admin')