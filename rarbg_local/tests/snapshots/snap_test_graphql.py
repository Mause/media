# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_main 1'] = {
    'data': {
        'monitors': [
            {
                'addedBy': {'username': 'Vincent Miller'},
                'title': 'Meagan Pena',
                'type': 'TV',
            }
        ],
        'movie': {'imdbId': 'tt293584', 'title': 'Christopher Robinson'},
        'tv': {
            'imdbId': 'tt000000',
            'name': 'Kathleen Williamson',
            'numberOfSeasons': 1,
            'season': {
                'episodes': [
                    {
                        'airDate': '1998-08-18',
                        'episodeNumber': 564,
                        'id': '948',
                        'name': 'Angel Robertson',
                    }
                ]
            },
            'seasons': [{'episodeCount': 1, 'seasonNumber': 1}],
        },
    }
}

snapshots['test_mutation 1'] = {'data': {'addDownload': 'specific episode magnet://'}}
