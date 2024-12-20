"""Add Check model

Revision ID: 34ff4bcf4684
Revises: 
Create Date: 2024-11-28 23:10:45.669198

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '34ff4bcf4684'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('coach_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('registration_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('date', sa.Date(), nullable=False))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))
        batch_op.drop_constraint('attendance_ibfk_2', type_='foreignkey')
        batch_op.create_foreign_key(None, 'registration', ['registration_id'], ['id'])
        batch_op.create_foreign_key(None, 'user', ['coach_id'], ['id'])
        batch_op.drop_column('session_id')
        batch_op.drop_column('session_date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('attendance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('session_date', sa.DATE(), nullable=False))
        batch_op.add_column(sa.Column('session_id', mysql.INTEGER(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('attendance_ibfk_2', 'session', ['session_id'], ['id'])
        batch_op.drop_column('created_at')
        batch_op.drop_column('date')
        batch_op.drop_column('registration_id')
        batch_op.drop_column('coach_id')

    # ### end Alembic commands ###
