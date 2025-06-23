from pathlib import Path

from pytest_snapshot.plugin import Snapshot

from ..tmdb import SearchBaseResponse


def test_load(snapshot: Snapshot, resource_path: Path) -> None:
    snapshot.assert_match(
        SearchBaseResponse.model_validate_json(
            (resource_path / 'tmdb.json').read_text()
        ).model_dump_json(indent=2),
        'tmdb_search_base_response.json',
    )
