"""refactor missing journal table

Revision ID: 05635d20ceb7
Revises: a9b1cd3a0a81
Create Date: 2021-06-21 09:21:07.891420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "05635d20ceb7"
down_revision = "a9b1cd3a0a81"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "missing_journals_new",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("issn", sa.String(length=9), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("missing_journals_new")
    # ### end Alembic commands ###
