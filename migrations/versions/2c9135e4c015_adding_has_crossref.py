"""adding has_crossref

Revision ID: 2c9135e4c015
Revises: 5e1d2cb02f95
Create Date: 2021-04-29 18:31:24.477734

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2c9135e4c015"
down_revision = "5e1d2cb02f95"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "issn_metadata", sa.Column("has_crossref", sa.Boolean(), nullable=True)
    )
    op.add_column("issn_temp", sa.Column("has_crossref", sa.Boolean(), nullable=True))
    op.add_column(
        "issn_to_issnl", sa.Column("has_crossref", sa.Boolean(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("issn_to_issnl", "has_crossref")
    op.drop_column("issn_temp", "has_crossref")
    op.drop_column("issn_metadata", "has_crossref")
    # ### end Alembic commands ###
