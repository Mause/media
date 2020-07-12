# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_index 1'] = {
    'movies': [
        {
            'download': {
                'added_by': {'username': 'python'},
                'id': 2,
                'imdb_id': 'tt0000001',
                'timestamp': '2020-04-20T00:00:00',
                'title': 'Other world',
                'tmdb_id': 2,
                'transmission_id': '000000000000000000',
                'type': 'movie',
            },
            'id': 1,
        }
    ],
    'series': [
        {
            'imdb_id': 'tt000000',
            'seasons': {
                '1': [
                    {
                        'download': {
                            'added_by': {'username': 'python'},
                            'id': 1,
                            'imdb_id': 'tt000000',
                            'timestamp': '2020-04-21T00:00:00',
                            'title': 'Hello world',
                            'tmdb_id': 1,
                            'transmission_id': '00000000000000000',
                            'type': 'episode',
                        },
                        'episode': 1,
                        'id': 1,
                        'season': 1,
                        'show_title': 'Programming',
                    }
                ]
            },
            'title': 'Programming',
            'tmdb_id': 1,
        }
    ],
}

snapshots['test_serial 1'] = {'series': {'helo': {'id': 1}}}

snapshots['test_swagger 1'] = {
    'basePath': '/api',
    'consumes': ['application/json'],
    'definitions': {
        'Download': {
            'properties': {
                'episode': {'nullable': True, 'type': 'string'},
                'magnet': {'pattern': '^magnet:', 'type': 'string'},
                'season': {'nullable': True, 'type': 'string'},
                'tmdb_id': {'format': 'int32', 'type': 'integer'},
            },
            'type': 'object',
        },
        'DownloadAllResponse': {
            'properties': {
                'complete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Complete',
                    'type': 'array',
                },
                'incomplete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Incomplete',
                    'type': 'array',
                },
                'packs': {
                    'items': {'$ref': '#/definitions/ITorrent'},
                    'title': 'Packs',
                    'type': 'array',
                },
            },
            'required': ['packs', 'complete', 'incomplete'],
            'title': 'DownloadAllResponse',
            'type': 'object',
        },
        'DownloadSchema': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
        'Episode': {
            'properties': {
                'air_date': {'format': 'date', 'type': 'string'},
                'episode_number': {'type': 'integer'},
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
            },
            'type': 'object',
        },
        'EpisodeDetailsSchema': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
        'EpisodeInfo': {
            'properties': {
                'complete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Complete',
                    'type': 'array',
                },
                'incomplete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Incomplete',
                    'type': 'array',
                },
                'packs': {
                    'items': {'$ref': '#/definitions/ITorrent'},
                    'title': 'Packs',
                    'type': 'array',
                },
            },
            'required': ['packs', 'complete', 'incomplete'],
            'title': 'DownloadAllResponse',
            'type': 'object',
        },
        'ITorrent': {
            'properties': {
                'complete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Complete',
                    'type': 'array',
                },
                'incomplete': {
                    'items': {
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'title': 'Incomplete',
                    'type': 'array',
                },
                'packs': {
                    'items': {'$ref': '#/definitions/ITorrent'},
                    'title': 'Packs',
                    'type': 'array',
                },
            },
            'required': ['packs', 'complete', 'incomplete'],
            'title': 'DownloadAllResponse',
            'type': 'object',
        },
        'IndexResponseSchema': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
        'InnerTorrent': {
            'properties': {
                'eta': {'type': 'integer'},
                'files': {
                    'items': {'$ref': '#/definitions/InnerTorrentFile'},
                    'type': 'array',
                },
                'hashString': {'type': 'string'},
                'id': {'type': 'integer'},
                'percentDone': {'type': 'number'},
            },
            'type': 'object',
        },
        'InnerTorrentFile': {
            'properties': {
                'bytesCompleted': {'type': 'integer'},
                'length': {'type': 'integer'},
                'name': {'type': 'string'},
            },
            'type': 'object',
        },
        'Monitor': {
            'properties': {
                'added_by': {'title': 'Added By', 'type': 'string'},
                'id': {'title': 'Id', 'type': 'integer'},
                'title': {'title': 'Title', 'type': 'string'},
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                'type': {'enum': ['MOVIE', 'TV'], 'title': 'Type'},
            },
            'required': ['tmdb_id', 'type', 'id', 'title', 'added_by'],
            'title': 'MonitorGet',
            'type': 'object',
        },
        'MonitorCreated': {'properties': {'id': {'type': 'integer'}}, 'type': 'object'},
        'MonitorPost': {
            'properties': {
                'tmdb_id': {'format': 'int32', 'type': 'integer'},
                'type': {'enum': ['MOVIE', 'TV'], 'type': 'string'},
            },
            'type': 'object',
        },
        'MovieDetailsSchema': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
        'SearchResponse': {
            'properties': {
                'Type': {
                    'enum': ('movie', 'episode'),
                    'example': 'movie',
                    'type': 'string',
                },
                'Year': {'type': 'integer'},
                'imdbID': {'type': 'integer'},
                'title': {'type': 'string'},
                'type': {
                    'enum': ('movie', 'episode'),
                    'example': 'movie',
                    'type': 'string',
                },
                'year': {'type': 'integer'},
            },
            'type': 'object',
        },
        'SeasonMeta': {
            'properties': {
                'episode_count': {'type': 'integer'},
                'season_number': {'type': 'integer'},
            },
            'type': 'object',
        },
        'SeriesDetails': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
        'Stats': {
            'properties': {
                'episode': {'type': 'integer'},
                'movie': {'type': 'integer'},
            },
            'type': 'object',
        },
        'StatsResponse': {
            'properties': {
                'user': {'type': 'string'},
                'values': {'$ref': '#/definitions/Stats'},
            },
            'type': 'object',
        },
        'TorrentsResponse': {
            'properties': {
                '*': {
                    'additionalProperties': {'$ref': '#/definitions/InnerTorrent'},
                    'type': 'object',
                }
            },
            'type': 'object',
        },
        'TvResponse': {
            'properties': {
                'imdb_id': {'type': 'string'},
                'number_of_seasons': {'type': 'integer'},
                'seasons': {
                    'items': {'$ref': '#/definitions/SeasonMeta'},
                    'type': 'array',
                },
                'title': {'type': 'string'},
            },
            'type': 'object',
        },
        'TvSeasonResponse': {
            'properties': {
                'episodes': {
                    'items': {'$ref': '#/definitions/Episode'},
                    'type': 'array',
                }
            },
            'type': 'object',
        },
        'UserSchema': {
            'properties': {
                'movies': {
                    'items': {'$ref': '#/definitions/MovieDetailsSchema'},
                    'title': 'Movies',
                    'type': 'array',
                },
                'series': {
                    'items': {'$ref': '#/definitions/SeriesDetails'},
                    'title': 'Series',
                    'type': 'array',
                },
            },
            'required': ['series', 'movies'],
            'title': 'IndexResponse',
            'type': 'object',
        },
    },
    'info': {'title': 'API', 'version': '1.0'},
    'paths': {
        '/diagnostics': {
            'get': {
                'operationId': 'get_api_diagnostics',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            }
        },
        '/download': {
            'post': {
                'operationId': 'post_api_download',
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'payload',
                        'required': True,
                        'schema': {
                            'items': {'$ref': '#/definitions/Download'},
                            'type': 'array',
                        },
                    }
                ],
                'responses': {'200': {'description': 'OK'}},
                'tags': ['default'],
            }
        },
        '/index': {
            'get': {
                'operationId': 'get_api_index',
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/IndexResponseSchema'},
                    }
                },
                'tags': ['default'],
            }
        },
        '/monitor': {
            'get': {
                'operationId': 'get_monitors_resource',
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {
                            'items': {'$ref': '#/definitions/Monitor'},
                            'type': 'array',
                        },
                    }
                },
                'tags': ['monitor'],
            },
            'post': {
                'operationId': 'post_monitors_resource',
                'parameters': [
                    {
                        'in': 'body',
                        'name': 'payload',
                        'required': True,
                        'schema': {'$ref': '#/definitions/MonitorPost'},
                    },
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    },
                ],
                'responses': {
                    '201': {
                        'description': 'Created',
                        'schema': {'$ref': '#/definitions/MonitorCreated'},
                    }
                },
                'tags': ['monitor'],
            },
        },
        '/monitor/{ident}': {
            'delete': {
                'operationId': 'delete_monitor_resource',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['monitor'],
            },
            'parameters': [
                {'in': 'path', 'name': 'ident', 'required': True, 'type': 'integer'}
            ],
        },
        '/movie/{tmdb_id}': {
            'get': {
                'operationId': 'get_api_movie',
                'parameters': [
                    {
                        'description': 'The Movie Database ID',
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'type': 'integer',
                    }
                ],
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            }
        },
        '/search': {
            'get': {
                'operationId': 'get_api_search',
                'parameters': [
                    {
                        'description': 'Search query',
                        'in': 'query',
                        'name': 'query',
                        'required': True,
                        'type': 'string',
                    },
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {
                            'items': {'$ref': '#/definitions/SearchResponse'},
                            'type': 'array',
                        },
                    }
                },
                'tags': ['default'],
            }
        },
        '/select/{tmdb_id}/season/{season}/download_all': {
            'get': {
                'operationId': 'get_download_all_episodes',
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/DownloadAllResponse'},
                    }
                },
                'tags': ['default'],
            },
            'parameters': [
                {'in': 'path', 'name': 'tmdb_id', 'required': True, 'type': 'string'},
                {'in': 'path', 'name': 'season', 'required': True, 'type': 'string'},
            ],
        },
        '/stats': {
            'get': {
                'operationId': 'get_api_stats',
                'parameters': [
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/StatsResponse'},
                    }
                },
                'tags': ['default'],
            }
        },
        '/stream/{type}/{tmdb_id}': {
            'get': {
                'operationId': 'get_stream',
                'parameters': [
                    {'in': 'query', 'name': 'season', 'type': 'integer'},
                    {'in': 'query', 'name': 'episode', 'type': 'integer'},
                    {
                        'collectionFormat': 'multi',
                        'enum': ['horriblesubs', 'rarbg', 'kickass'],
                        'in': 'query',
                        'name': 'source',
                        'type': 'string',
                    },
                ],
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            },
            'parameters': [
                {
                    'description': None,
                    'enum': ['series', 'movie'],
                    'in': 'path',
                    'name': 'type',
                    'required': True,
                    'type': 'string',
                },
                {'in': 'path', 'name': 'tmdb_id', 'required': True, 'type': 'string'},
            ],
        },
        '/torrents': {
            'get': {
                'operationId': 'get_api_torrents',
                'parameters': [
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    }
                ],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/TorrentsResponse'},
                    }
                },
                'tags': ['default'],
            }
        },
        '/tv/{tmdb_id}': {
            'get': {
                'operationId': 'get_api_tv',
                'parameters': [
                    {
                        'description': 'The Movie Database ID',
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'type': 'integer',
                    },
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/TvResponse'},
                    }
                },
                'tags': ['tv'],
            }
        },
        '/tv/{tmdb_id}/season/{season}': {
            'get': {
                'operationId': 'get_api_tv_season',
                'parameters': [
                    {
                        'description': 'The Movie Database ID',
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'type': 'integer',
                    },
                    {
                        'description': 'An optional fields mask',
                        'format': 'mask',
                        'in': 'header',
                        'name': 'X-Fields',
                        'type': 'string',
                    },
                ],
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {'$ref': '#/definitions/TvSeasonResponse'},
                    }
                },
                'tags': ['tv'],
            },
            'parameters': [
                {'in': 'path', 'name': 'season', 'required': True, 'type': 'integer'}
            ],
        },
    },
    'produces': ['application/json'],
    'responses': {
        'MaskError': {'description': 'When any error occurs on mask'},
        'ParseError': {'description': "When a mask can't be parsed"},
        'ValidationError': {},
        'ValidationErrorWrapper': {},
    },
    'security': [{'basic': []}],
    'securityDefinitions': {'basic': {'type': 'basic'}},
    'swagger': '2.0',
    'tags': [
        {'description': 'Default namespace', 'name': 'default'},
        {'description': 'Contains media monitor resources', 'name': 'monitor'},
        {'name': 'tv'},
    ],
}

snapshots['test_schema 1'] = {
    'properties': {
        'Type': {'deprecated': True, 'enum': ['series', 'movie'], 'title': 'Type'},
        'Year': {'deprecated': True, 'title': 'Year', 'type': 'integer'},
        'imdbID': {'title': 'Imdbid', 'type': 'integer'},
        'title': {'title': 'Title', 'type': 'string'},
        'type': {'enum': ['series', 'movie'], 'title': 'Type'},
        'year': {'title': 'Year', 'type': 'integer'},
    },
    'required': ['title', 'type', 'year', 'imdbID', 'Year', 'Type'],
    'title': 'SearchResponse',
    'type': 'object',
}
