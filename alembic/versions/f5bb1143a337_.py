"""empty message

Revision ID: f5bb1143a337
Revises: 3e86cca42fcb
Create Date: 2020-01-18 14:29:06.006593

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f5bb1143a337'
down_revision = '3e86cca42fcb'
branch_labels = None
depends_on = None


def upgrade():
    sqlite = op.get_bind().engine.url.drivername == 'sqlite'

    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('download', sa.Column('added_by_id', sa.Integer(), nullable=True))
    if not sqlite:
        op.create_foreign_key(None, 'download', 'users', ['added_by_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'download', type_='foreignkey')
    op.drop_column('download', 'added_by_id')
    # ### end Alembic commands ###
