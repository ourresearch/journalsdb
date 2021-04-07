"""merge migrations

Revision ID: e2abdf81151f
Revises: b9c0f72bc63a, b6a7221990ba
Create Date: 2021-04-06 19:50:04.064091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e2abdf81151f"
down_revision = ("b9c0f72bc63a", "b6a7221990ba")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
