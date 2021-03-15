"""add published_year to retraction watch

Revision ID: 429e15bb8412
Revises: 89df7caa1e08
Create Date: 2021-03-02 14:53:44.589315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "429e15bb8412"
down_revision = "89df7caa1e08"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "retraction_watch", sa.Column("published_year", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("retraction_watch", "published_year")
    # ### end Alembic commands ###