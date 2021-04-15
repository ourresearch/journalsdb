"""add journal metadata fields

Revision ID: b6a7221990ba
Revises: 8136d2440010
Create Date: 2021-04-05 18:52:58.047531

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b6a7221990ba"
down_revision = "8136d2440010"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "journal_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("journal_id", sa.Integer(), nullable=False),
        sa.Column("home_page_url", sa.String(length=500), nullable=True),
        sa.Column("author_instructions_url", sa.String(length=500), nullable=True),
        sa.Column("editorial_page_url", sa.String(length=500), nullable=True),
        sa.Column("facebook_url", sa.String(length=500), nullable=True),
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
        sa.Column("twitter_url", sa.String(length=500), nullable=True),
        sa.Column("wikidata_url", sa.String(length=500), nullable=True),
        sa.Column("society_journal", sa.Boolean(), nullable=True),
        sa.Column("society_journal_name", sa.Text(), nullable=True),
        sa.Column("society_journal_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["journal_id"],
            ["journals.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("journal_metadata")
    # ### end Alembic commands ###