"""merge open access tables into one

Revision ID: 6e55c8774914
Revises: 744695e84b5d
Create Date: 2021-02-07 09:03:52.928237

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6e55c8774914"
down_revision = "744695e84b5d"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "open_access",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journal_id", sa.Integer(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("is_in_doaj", sa.Boolean(), nullable=True),
        sa.Column("is_hybrid_journal", sa.Boolean(), nullable=True),
        sa.Column("is_gold_journal", sa.Boolean(), nullable=True),
        sa.Column("is_diamond_oa", sa.Boolean(), nullable=True),
        sa.Column("num_dois", sa.Integer(), nullable=True),
        sa.Column("num_open", sa.Integer(), nullable=True),
        sa.Column("open_rate", sa.Float(), nullable=True),
        sa.Column("num_green", sa.Integer(), nullable=True),
        sa.Column("green_rate", sa.Float(), nullable=True),
        sa.Column("num_bronze", sa.Integer(), nullable=True),
        sa.Column("bronze_rate", sa.Float(), nullable=True),
        sa.Column("num_hybrid", sa.Integer(), nullable=True),
        sa.Column("hybrid_rate", sa.Float(), nullable=True),
        sa.Column("num_gold", sa.Integer(), nullable=True),
        sa.Column("gold_rate", sa.Float(), nullable=True),
        sa.Column("hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["journal_id"],
            ["journals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.drop_table("open_access_publishing")
    op.drop_table("open_access_status")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "open_access_status",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("journal_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("is_in_doaj", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column(
            "is_hybrid_journal", sa.BOOLEAN(), autoincrement=False, nullable=True
        ),
        sa.Column("is_gold_journal", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("is_diamond_oa", sa.BOOLEAN(), autoincrement=False, nullable=True),
        sa.Column("year", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["journal_id"], ["journals.id"], name="open_access_status_journal_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="open_access_status_pkey"),
    )
    op.create_table(
        "open_access_publishing",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("journal_id", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("num_dois", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("num_open", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "open_rate",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("num_green", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "green_rate",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("num_bronze", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "bronze_rate",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("num_hybrid", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "hybrid_rate",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("num_gold", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column(
            "gold_rate",
            postgresql.DOUBLE_PRECISION(precision=53),
            autoincrement=False,
            nullable=True,
        ),
        sa.Column("year", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["journal_id"],
            ["journals.id"],
            name="open_access_publishing_journal_id_fkey",
        ),
        sa.PrimaryKeyConstraint("id", name="open_access_publishing_pkey"),
    )
    op.drop_table("open_access")
    # ### end Alembic commands ###
