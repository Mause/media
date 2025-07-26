import json

from pytest_snapshot.plugin import Snapshot

from ...providers.palace import Session


def test_search(snapshot: Snapshot) -> None:
    snapshot.assert_match(
        json.dumps(Session.model_json_schema(), indent=2), "Session.schema.json"
    )
