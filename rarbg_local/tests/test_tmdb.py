from ..tmdb import SearchBaseResponse


def test_load(snapshot, resource_path):
    snapshot.assert_match(
        SearchBaseResponse.model_validate_json(
            (resource_path / 'tmdb.json').read_text()
        ).model_dump_json(indent=2),
        'tmdb_search_base_response.json',
    )
