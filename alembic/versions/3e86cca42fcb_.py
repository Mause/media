"""empty message

Revision ID: 3e86cca42fcb
Revises: 01602e6e9637
Create Date: 2020-01-18 13:52:48.008881

"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import DefaultClause

from alembic import op
from common import get_driver

# revision identifiers, used by Alembic.
revision = '3e86cca42fcb'
down_revision = '01602e6e9637'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    sqlite = get_driver() == 'sqlite'
    ca = sa.Column(
        'timestamp',
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=DefaultClause(str(datetime.now()) if sqlite else func.now()),
    )
    op.add_column('download', ca)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('download', 'timestamp')
    # ### end Alembic commands ###
