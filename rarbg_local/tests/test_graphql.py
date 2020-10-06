from pytest import mark


@mark.asyncio
async def test_main(test_client, snapshot, responses):
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

    snapshot.assert_match(res.json())
