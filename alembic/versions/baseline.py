"""Add en_AU collation

Revision ID: baseline
Create Date: 2025-05-25

"""

import sqlalchemy as sa

from alembic import op
from common import get_driver

# revision identifiers, used by Alembic.
revision = "baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if get_driver() == 'sqlite':
        inner = conn.connection.driver_connection
        assert inner
        inner.create_collation(
            "en_AU", lambda a, b: 0 if a.lower() == b.lower() else -1
        )
    else:
        conn.execute(sa.text("CREATE COLLATION \"en_AU\" (LOCALE = 'en_AU.utf8')"))


def downgrade() -> None:
    conn = op.get_bind()
    if get_driver() == 'sqlite':
        inner = conn.connection.driver_connection
        assert inner
        inner.drop_collation("en_AU")
    else:
        conn.execute(sa.text("DROP COLLATION IF EXISTS \"en_AU\""))
