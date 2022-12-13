"""Search Configuration Table

Revision ID: ca2707a8c7a3
Revises: 
Create Date: 2022-11-24 18:03:19.408635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ca2707a8c7a3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'search_config',
        sa.Column('id', sa.UnicodeText, primary_key=True),
        sa.Column('link', sa.UnicodeText, nullable=False),
        sa.Column('value', sa.UnicodeText, nullable=False)
    )


def downgrade():
    op.drop_table('search_config')
