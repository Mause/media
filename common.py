from alembic import op


def get_driver() -> str:
    return op.get_bind().engine.name
