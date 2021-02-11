"""modify open access table

Revision ID: 594a0424c091
Revises: 6e55c8774914
Create Date: 2021-02-09 17:14:48.722730

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "594a0424c091"
down_revision = "6e55c8774914"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("open_access", sa.Column("issn_l", sa.Text(), nullable=False))
    op.add_column("open_access", sa.Column("title", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_open_access_issn_l"), "open_access", ["issn_l"], unique=False
    )
    op.drop_column("open_access", "journal_id")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "open_access",
        sa.Column("journal_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "open_access_journal_id_fkey", "open_access", "journals", ["journal_id"], ["id"]
    )
    op.drop_index(op.f("ix_open_access_issn_l"), table_name="open_access")
    op.drop_column("open_access", "title")
    op.drop_column("open_access", "issn_l")
    # ### end Alembic commands ###
