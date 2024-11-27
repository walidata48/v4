"""add relationship to models

Revision ID: 459dc115edb9
Revises: 
Create Date: 2024-11-27 16:45:10.088426

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '459dc115edb9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Drop the foreign key constraint first
    op.drop_constraint('registration_ibfk_1', 'registration', type_='foreignkey')
    
    # Now drop the user table
    op.drop_table('user')

def downgrade():
    # Recreate the user table if needed
    op.create_table('user',
        # Define columns here
    )
    
    # Recreate the foreign key constraint
    op.create_foreign_key('registration_ibfk_1', 'registration', 'user', ['user_id'], ['id'])
