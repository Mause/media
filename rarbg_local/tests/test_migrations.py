from pathlib import Path

from pytest import fixture
from pytest_alembic.config import Config
from pytest_alembic.tests import (
    test_model_definitions_match_ddl,
    test_single_head_revision,
    test_up_down_consistency,
    test_upgrade,
)
from pytest_alembic.tests.experimental import (
    # test_all_models_register_on_metadata,
    test_downgrade_leaves_no_trace,
)
from sqlalchemy import URL


@fixture
def alembic_config(tmp_path: Path) -> Config:
    return Config(
        config_options={
            'sqlalchemy.url': str(
                URL.create(drivername='sqlite', database=str(tmp_path / 'db.db'))
            )
        }
    )


__all__ = [
    "test_upgrade",
    "test_model_definitions_match_ddl",
    # "test_all_models_register_on_metadata",
    "test_single_head_revision",
    "test_downgrade_leaves_no_trace",
    "test_up_down_consistency",
]
