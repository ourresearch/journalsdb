"""ensure migrations in sync with recent manual changes

Revision ID: a9b1cd3a0a81
Revises: 32d38367dab3
Create Date: 2021-06-20 19:51:10.103244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a9b1cd3a0a81"
down_revision = "32d38367dab3"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(
        "author_permissions_journal_id_fkey", "author_permissions", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "author_permissions", "journals", ["journal_id"], ["id"]
    )
    op.drop_constraint(
        "extension_requests_journal_id_fkey", "extension_requests", type_="foreignkey"
    )
    op.create_foreign_key(
        None, "extension_requests", "journals", ["journal_id"], ["id"]
    )
    op.drop_index("issn_temp_issn_uindex", table_name="issn_temp")
    op.create_unique_constraint(None, "issn_temp", ["issn"])
    op.drop_index("journal_metadata_journal_id_index", table_name="journal_metadata")
    op.create_index(
        op.f("ix_journal_metadata_journal_id"),
        "journal_metadata",
        ["journal_id"],
        unique=False,
    )
    op.drop_index("journals_created_at_index", table_name="journals")
    op.create_index(
        op.f("ix_journals_created_at"), "journals", ["created_at"], unique=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_journals_created_at"), table_name="journals")
    op.create_index(
        "journals_created_at_index", "journals", ["created_at"], unique=False
    )
    op.drop_index(op.f("ix_journal_metadata_journal_id"), table_name="journal_metadata")
    op.create_index(
        "journal_metadata_journal_id_index",
        "journal_metadata",
        ["journal_id"],
        unique=False,
    )
    op.drop_constraint(None, "issn_temp", type_="unique")
    op.create_index("issn_temp_issn_uindex", "issn_temp", ["issn"], unique=True)
    op.drop_constraint(None, "extension_requests", type_="foreignkey")
    op.create_foreign_key(
        "extension_requests_journal_id_fkey",
        "extension_requests",
        "journals",
        ["journal_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(None, "author_permissions", type_="foreignkey")
    op.create_foreign_key(
        "author_permissions_journal_id_fkey",
        "author_permissions",
        "journals",
        ["journal_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # ### end Alembic commands ###
