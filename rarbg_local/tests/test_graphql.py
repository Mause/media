from pytest import mark

from .conftest import assert_match_json, themoviedb
from .factories import (
    MonitorFactory,
    MovieResponseFactory,
    TvApiResponseFactory,
    TvSeasonResponseFactory,
)


@mark.asyncio
async def test_main(test_client, snapshot, aioresponses, session):
    session.add(
        MonitorFactory(
            title='Meagan Pena', type='TV', added_by__username='Vincent Miller'
        )
    )
    session.commit()

    imdb_id = 'tt000000'
    themoviedb(
        aioresponses,
        '/tv/540',
        TvApiResponseFactory(
            id=540,
            name='Kathleen Williamson',
            number_of_seasons=1,
            seasons=[{'episode_count': 1, 'season_number': 1}],
        ).dict(),
    )
    themoviedb(
        aioresponses,
        '/tv/540/season/1',
        TvSeasonResponseFactory(
            episodes=[
                {
                    'air_date': '1998-08-18',
                    'episode_number': 564,
                    'id': '948',
                    'name': 'Angel Robertson',
                }
            ]
        ).dict(),
    )
    themoviedb(aioresponses, '/tv/540/external_ids', {'imdb_id': imdb_id})
    themoviedb(
        aioresponses,
        '/movie/540',
        MovieResponseFactory(imdb_id='tt293584', title='Christopher Robinson').dict(),
    )

    res = await test_client.post(
        '/graphql/',
        json={
            'query': '''
                query A {
                    monitors {
                        title
                        type
                        addedBy {
                            username
                        }
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

    assert_match_json(snapshot, res, 'graphql_response.json')


@mark.asyncio
async def test_mutation(test_client, snapshot):
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

    assert_match_json(snapshot, res, 'graphql_mutation_response.json')
