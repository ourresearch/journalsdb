"""adding apc_data_source

Revision ID: 75ff6e385482
Revises: 429e15bb8412
Create Date: 2021-03-11 18:43:11.971255

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "75ff6e385482"
down_revision = "429e15bb8412"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "publishers", sa.Column("apc_data_source", sa.String(length=500), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("publishers", "apc_data_source")
    # ### end Alembic commands ###
