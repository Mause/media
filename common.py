from alembic import op

revision = None


def get_driver():
    return op.get_bind().engine.url.drivername
