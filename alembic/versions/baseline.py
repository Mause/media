"""Add en_AU collation

Revision ID: baseline
Create Date: 2025-05-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("CREATE COLLATION \"en_AU\" (LOCALE = 'en_AU.utf8')")
    )


def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text("DROP COLLATION IF EXISTS \"en_AU\"")
    )
