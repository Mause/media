from pathlib import Path

from pytest import fixture
from pytest_alembic.config import Config
from pytest_alembic.tests import (
    # test_model_definitions_match_ddl,
    test_single_head_revision,
    # test_up_down_consistency,
    # test_upgrade,
)


@fixture
def alembic_config(tmp_path: Path) -> Config:
    return Config(
        config_options={
            'sqlalchemy.url': f'sqlite://{tmp_path}/db.db',
        }
    )


__all__ = [
    # "test_upgrade",
    # "test_model_definitions_match_ddl",
    "test_single_head_revision",
    # "test_up_down_consistency",
]
