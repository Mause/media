from alembic import op


def get_driver():
    return op.get_bind().engine.name
