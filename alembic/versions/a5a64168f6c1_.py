"""empty message

Revision ID: a5a64168f6c1
Revises: 2abd0ee3433d
Create Date: 2020-03-08 18:01:55.431768

"""
import sqlalchemy as sa
from alembic import op
from common import get_driver
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a5a64168f6c1'
down_revision = '2abd0ee3433d'
branch_labels = None
depends_on = None


mediatype = postgresql.ENUM('MOVIE', 'TV', name='mediatype')


def upgrade():
    if get_driver() != 'sqlite':
        mediatype.create(op.get_bind())

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'monitor',
        sa.Column(
            'type',
            sa.Enum('MOVIE', 'TV', name='mediatype', create_type=True),
            server_default='MOVIE',
            nullable=False,
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('monitor', 'type')
    if get_driver() != 'sqlite':
        mediatype.drop(op.get_bind())
    # ### end Alembic commands ###