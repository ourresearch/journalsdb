"""remove issns column

Revision ID: 744695e84b5d
Revises: 52c47a497011
Create Date: 2021-01-30 16:13:18.477138

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '744695e84b5d'
down_revision = '52c47a497011'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('journals', 'issns')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('journals', sa.Column('issns', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
