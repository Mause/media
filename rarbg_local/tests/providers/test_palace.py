from pathlib import Path

from pydantic import RootModel
from pytest_snapshot.plugin import Snapshot

from ...providers.palace import SearchResult, Session
from ..conftest import assert_match_json


def test_session(snapshot: Snapshot) -> None:
    assert_match_json(snapshot, Session.model_json_schema(), "Session.schema.json")


def test_search(snapshot: Snapshot, resource_path: Path) -> None:
    assert_match_json(snapshot, SearchResult.model_json_schema(), 'schema.json')

    with (resource_path / 'search.json').open() as fh:
        RootModel[list[SearchResult]].model_validate_json(fh.read())
