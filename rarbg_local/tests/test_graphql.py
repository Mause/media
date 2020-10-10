from pytest import mark

from .conftest import themoviedb
from .factories import (
    MovieResponseFactory,
    TvApiResponseFactory,
    TvSeasonResponseFactory,
)


@mark.asyncio
async def test_main(test_client, snapshot, responses):
    themoviedb(responses, '/tv/540', TvApiResponseFactory(id=540).dict())
    themoviedb(responses, '/tv/540/season/1', TvSeasonResponseFactory().dict())
    themoviedb(responses, '/tv/540/external_ids', {'imdb_id': 'tt000000'})
    themoviedb(responses, '/movie/540', MovieResponseFactory().dict())

    res = await test_client.post(
        '/graphql/',
        json={
            'query': '''
                query A {
                    monitors {
                        name
                    }
                    movie(id: 540) {
                        title
                        imdbId
                    }
                    tv(id: 540) {
                        name
                        imdbId
                        numberOfSeasons
                        seasons {
                            episodeCount
                            seasonNumber
                        }
                        season(number: 1) {
                            episodes {
                                name
                                id
                                airDate
                                episodeNumber
                            }
                        }
                    }
                }
            ''',
        },
    )

    assert not res.json().get('errors')

    snapshot.assert_match(res.json())


@mark.asyncio
async def test_mutation(test_client, snapshot, responses):
    res = await test_client.post(
        '/graphql/',
        json={
            'query': '''
                mutation B {
                    addDownload(magnet: "magnet://", season: 1, episode: -1)
                }
            '''
        },
    )

    assert not res.json().get('errors')

    snapshot.assert_match(res.json())
