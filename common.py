from alembic import op


def get_driver():
    engine = op.get_bind().engine
    return engine.url.drivername if hasattr(engine, 'url') else engine.name
