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

snapshots['test_swagger 1'] = {
    'basePath': '/api',
    'consumes': ['application/json'],
    'definitions': {
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
        'DownloadPost': {
            'properties': {
                'episode': {'title': 'Episode', 'type': 'string'},
                'magnet': {'pattern': '^magnet:', 'title': 'Magnet', 'type': 'string'},
                'season': {'title': 'Season', 'type': 'string'},
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
            },
            'required': ['tmdb_id', 'magnet'],
            'title': 'DownloadPost',
            'type': 'object',
        },
        'DownloadSchema': {
            'properties': {
                'added_by': {'$ref': '#/definitions/UserSchema'},
                'id': {'title': 'Id', 'type': 'integer'},
                'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                'timestamp': {
                    'format': 'date-time',
                    'title': 'Timestamp',
                    'type': 'string',
                },
                'title': {'title': 'Title', 'type': 'string'},
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                'transmission_id': {'title': 'Transmission Id', 'type': 'string'},
                'type': {'title': 'Type', 'type': 'string'},
            },
            'required': [
                'id',
                'tmdb_id',
                'transmission_id',
                'imdb_id',
                'type',
                'title',
                'timestamp',
                'added_by',
            ],
            'title': 'DownloadSchema',
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
                'download': {'$ref': '#/definitions/DownloadSchema'},
                'episode': {'title': 'Episode', 'type': 'integer'},
                'id': {'title': 'Id', 'type': 'integer'},
                'season': {'title': 'Season', 'type': 'integer'},
                'show_title': {'title': 'Show Title', 'type': 'string'},
            },
            'required': ['id', 'download', 'show_title', 'season'],
            'title': 'EpisodeDetailsSchema',
            'type': 'object',
        },
        'EpisodeInfo': {
            'properties': {
                'epnum': {'title': 'Epnum', 'type': 'string'},
                'seasonnum': {'title': 'Seasonnum', 'type': 'string'},
            },
            'title': 'EpisodeInfo',
            'type': 'object',
        },
        'ITorrent': {
            'properties': {
                'category': {'title': 'Category', 'type': 'string'},
                'download': {'title': 'Download', 'type': 'string'},
                'episode_info': {'$ref': '#/definitions/EpisodeInfo'},
                'seeders': {'title': 'Seeders', 'type': 'integer'},
                'source': {'$ref': '#/definitions/ProviderSource'},
                'title': {'title': 'Title', 'type': 'string'},
            },
            'required': [
                'source',
                'title',
                'seeders',
                'download',
                'category',
                'episode_info',
            ],
            'title': 'ITorrent',
            'type': 'object',
        },
        'IndexResponse': {
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
        'MonitorGet': {
            'properties': {
                'added_by': {'title': 'Added By', 'type': 'string'},
                'id': {'title': 'Id', 'type': 'integer'},
                'title': {'title': 'Title', 'type': 'string'},
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                'type': {'$ref': '#/definitions/MonitorMediaType'},
            },
            'required': ['tmdb_id', 'type', 'id', 'title', 'added_by'],
            'title': 'MonitorGet',
            'type': 'object',
        },
        'MonitorMediaType': {
            'description': 'An enumeration.',
            'enum': ['MOVIE', 'TV'],
            'title': 'MonitorMediaType',
        },
        'MonitorPost': {
            'properties': {
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                'type': {'$ref': '#/definitions/MonitorMediaType'},
            },
            'required': ['tmdb_id', 'type'],
            'title': 'MonitorPost',
            'type': 'object',
        },
        'MovieDetailsSchema': {
            'properties': {
                'download': {'$ref': '#/definitions/DownloadSchema'},
                'id': {'title': 'Id', 'type': 'integer'},
            },
            'required': ['id', 'download'],
            'title': 'MovieDetailsSchema',
            'type': 'object',
        },
        'ProviderSource': {
            'description': 'An enumeration.',
            'enum': ['KICKASS', 'HORRIBLESUBS', 'RARBG'],
            'title': 'ProviderSource',
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
                'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                'seasons': {
                    'additionalProperties': {
                        'items': {'$ref': '#/definitions/EpisodeDetailsSchema'},
                        'type': 'array',
                    },
                    'title': 'Seasons',
                    'type': 'object',
                },
                'title': {'title': 'Title', 'type': 'string'},
                'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
            },
            'required': ['title', 'imdb_id', 'tmdb_id', 'seasons'],
            'title': 'SeriesDetails',
            'type': 'object',
        },
        'Stats': {
            'properties': {
                'episode': {'default': 0, 'title': 'Episode', 'type': 'integer'},
                'movie': {'default': 0, 'title': 'Movie', 'type': 'integer'},
            },
            'title': 'Stats',
            'type': 'object',
        },
        'StatsResponse': {
            'properties': {
                'user': {'title': 'User', 'type': 'string'},
                'values': {'$ref': '#/definitions/Stats'},
            },
            'required': ['user', 'values'],
            'title': 'StatsResponse',
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
            'properties': {'username': {'title': 'Username', 'type': 'string'}},
            'required': ['username'],
            'title': 'UserSchema',
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
                            'items': {'$ref': '#/definitions/DownloadPost'},
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
                        'schema': {'$ref': '#/definitions/IndexResponse'},
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
                            'items': {'$ref': '#/definitions/MonitorGet'},
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
                    }
                ],
                'responses': {
                    '201': {
                        'description': 'Created',
                        'schema': {'$ref': '#/definitions/MonitorGet'},
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
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            },
            'parameters': [
                {'in': 'path', 'name': 'tmdb_id', 'required': True, 'type': 'integer'}
            ],
        },
        '/openapi.json': {
            'get': {
                'operationId': 'get_api_openapi',
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
                'responses': {
                    '200': {
                        'description': 'Success',
                        'schema': {
                            'items': {'$ref': '#/definitions/StatsResponse'},
                            'type': 'array',
                        },
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
    'definitions': {
        'MediaType': {
            'description': 'An enumeration.',
            'enum': ['series', 'movie'],
            'title': 'MediaType',
        }
    },
    'properties': {
        'Type': {'$ref': '#/definitions/MediaType'},
        'Year': {'deprecated': True, 'title': 'Year', 'type': 'integer'},
        'imdbID': {'title': 'Imdbid', 'type': 'integer'},
        'title': {'title': 'Title', 'type': 'string'},
        'type': {'$ref': '#/definitions/MediaType'},
        'year': {'title': 'Year', 'type': 'integer'},
    },
    'required': ['title', 'type', 'year', 'imdbID', 'Year', 'Type'],
    'title': 'SearchResponse',
    'type': 'object',
}

snapshots['test_openapi 1'] = {
    'components': {
        'schemas': {
            'Body_login_token_post': {
                'properties': {
                    'client_id': {'title': 'Client Id', 'type': 'string'},
                    'client_secret': {'title': 'Client Secret', 'type': 'string'},
                    'grant_type': {
                        'pattern': 'password',
                        'title': 'Grant Type',
                        'type': 'string',
                    },
                    'password': {'title': 'Password', 'type': 'string'},
                    'scope': {'default': '', 'title': 'Scope', 'type': 'string'},
                    'username': {'title': 'Username', 'type': 'string'},
                },
                'required': ['username', 'password'],
                'title': 'Body_login_token_post',
                'type': 'object',
            },
            'DownloadAllResponse': {
                'properties': {
                    'complete': {
                        'items': {
                            'items': [
                                {'type': 'string'},
                                {
                                    'items': {'$ref': '#/components/schemas/ITorrent'},
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
                                    'items': {'$ref': '#/components/schemas/ITorrent'},
                                    'type': 'array',
                                },
                            ],
                            'type': 'array',
                        },
                        'title': 'Incomplete',
                        'type': 'array',
                    },
                    'packs': {
                        'items': {'$ref': '#/components/schemas/ITorrent'},
                        'title': 'Packs',
                        'type': 'array',
                    },
                },
                'required': ['packs', 'complete', 'incomplete'],
                'title': 'DownloadAllResponse',
                'type': 'object',
            },
            'DownloadPost': {
                'properties': {
                    'episode': {'title': 'Episode', 'type': 'string'},
                    'magnet': {
                        'pattern': '^magnet:',
                        'title': 'Magnet',
                        'type': 'string',
                    },
                    'season': {'title': 'Season', 'type': 'string'},
                    'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                },
                'required': ['tmdb_id', 'magnet'],
                'title': 'DownloadPost',
                'type': 'object',
            },
            'DownloadSchema': {
                'properties': {
                    'added_by': {'$ref': '#/components/schemas/UserSchema'},
                    'id': {'title': 'Id', 'type': 'integer'},
                    'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                    'timestamp': {
                        'format': 'date-time',
                        'title': 'Timestamp',
                        'type': 'string',
                    },
                    'title': {'title': 'Title', 'type': 'string'},
                    'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                    'transmission_id': {'title': 'Transmission Id', 'type': 'string'},
                    'type': {'title': 'Type', 'type': 'string'},
                },
                'required': [
                    'id',
                    'tmdb_id',
                    'transmission_id',
                    'imdb_id',
                    'type',
                    'title',
                    'timestamp',
                    'added_by',
                ],
                'title': 'DownloadSchema',
                'type': 'object',
            },
            'Episode': {
                'properties': {
                    'air_date': {
                        'format': 'date',
                        'title': 'Air Date',
                        'type': 'string',
                    },
                    'episode_number': {'title': 'Episode Number', 'type': 'integer'},
                    'id': {'title': 'Id', 'type': 'integer'},
                    'name': {'title': 'Name', 'type': 'string'},
                },
                'required': ['name', 'id', 'episode_number'],
                'title': 'Episode',
                'type': 'object',
            },
            'EpisodeDetailsSchema': {
                'properties': {
                    'download': {'$ref': '#/components/schemas/DownloadSchema'},
                    'episode': {'title': 'Episode', 'type': 'integer'},
                    'id': {'title': 'Id', 'type': 'integer'},
                    'season': {'title': 'Season', 'type': 'integer'},
                    'show_title': {'title': 'Show Title', 'type': 'string'},
                },
                'required': ['id', 'download', 'show_title', 'season'],
                'title': 'EpisodeDetailsSchema',
                'type': 'object',
            },
            'EpisodeInfo': {
                'properties': {
                    'epnum': {'title': 'Epnum', 'type': 'string'},
                    'seasonnum': {'title': 'Seasonnum', 'type': 'string'},
                },
                'required': ['seasonnum', 'epnum'],
                'title': 'EpisodeInfo',
                'type': 'object',
            },
            'HTTPValidationError': {
                'properties': {
                    'detail': {
                        'items': {'$ref': '#/components/schemas/ValidationError'},
                        'title': 'Detail',
                        'type': 'array',
                    }
                },
                'title': 'HTTPValidationError',
                'type': 'object',
            },
            'ITorrent': {
                'properties': {
                    'category': {'title': 'Category', 'type': 'string'},
                    'download': {'title': 'Download', 'type': 'string'},
                    'episode_info': {'$ref': '#/components/schemas/EpisodeInfo'},
                    'seeders': {'title': 'Seeders', 'type': 'integer'},
                    'source': {'$ref': '#/components/schemas/ProviderSource'},
                    'title': {'title': 'Title', 'type': 'string'},
                },
                'required': [
                    'source',
                    'download',
                    'seeders',
                    'category',
                    'title',
                    'episode_info',
                ],
                'title': 'ITorrent',
                'type': 'object',
            },
            'IndexResponse': {
                'properties': {
                    'movies': {
                        'items': {'$ref': '#/components/schemas/MovieDetailsSchema'},
                        'title': 'Movies',
                        'type': 'array',
                    },
                    'series': {
                        'items': {'$ref': '#/components/schemas/SeriesDetails'},
                        'title': 'Series',
                        'type': 'array',
                    },
                },
                'required': ['series', 'movies'],
                'title': 'IndexResponse',
                'type': 'object',
            },
            'MediaType': {
                'description': 'An enumeration.',
                'enum': ['series', 'movie'],
                'title': 'MediaType',
            },
            'MonitorGet': {
                'properties': {
                    'added_by': {'title': 'Added By', 'type': 'string'},
                    'id': {'title': 'Id', 'type': 'integer'},
                    'title': {'title': 'Title', 'type': 'string'},
                    'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                    'type': {'$ref': '#/components/schemas/MonitorMediaType'},
                },
                'required': ['tmdb_id', 'type', 'id', 'title', 'added_by'],
                'title': 'MonitorGet',
                'type': 'object',
            },
            'MonitorMediaType': {
                'description': 'An enumeration.',
                'enum': ['MOVIE', 'TV'],
                'title': 'MonitorMediaType',
            },
            'MonitorPost': {
                'properties': {
                    'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                    'type': {'$ref': '#/components/schemas/MonitorMediaType'},
                },
                'required': ['tmdb_id', 'type'],
                'title': 'MonitorPost',
                'type': 'object',
            },
            'MovieDetailsSchema': {
                'properties': {
                    'download': {'$ref': '#/components/schemas/DownloadSchema'},
                    'id': {'title': 'Id', 'type': 'integer'},
                },
                'required': ['id', 'download'],
                'title': 'MovieDetailsSchema',
                'type': 'object',
            },
            'MovieResponse': {
                'properties': {
                    'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                    'title': {'title': 'Title', 'type': 'string'},
                },
                'required': ['title', 'imdb_id'],
                'title': 'MovieResponse',
                'type': 'object',
            },
            'PromoteCreate': {
                'properties': {
                    'roles': {
                        'items': {'type': 'string'},
                        'title': 'Roles',
                        'type': 'array',
                    },
                    'username': {'title': 'Username', 'type': 'string'},
                },
                'required': ['username', 'roles'],
                'title': 'PromoteCreate',
                'type': 'object',
            },
            'ProviderSource': {
                'description': 'An enumeration.',
                'enum': ['KICKASS', 'HORRIBLESUBS', 'RARBG'],
                'title': 'ProviderSource',
            },
            'SearchResponse': {
                'properties': {
                    'Type': {'$ref': '#/components/schemas/MediaType'},
                    'Year': {'deprecated': True, 'title': 'Year', 'type': 'integer'},
                    'imdbID': {'title': 'Imdbid', 'type': 'integer'},
                    'title': {'title': 'Title', 'type': 'string'},
                    'type': {'$ref': '#/components/schemas/MediaType'},
                    'year': {'title': 'Year', 'type': 'integer'},
                },
                'required': ['title', 'type', 'year', 'imdbID', 'Year', 'Type'],
                'title': 'SearchResponse',
                'type': 'object',
            },
            'SeasonMeta': {
                'properties': {
                    'episode_count': {'title': 'Episode Count', 'type': 'integer'},
                    'season_number': {'title': 'Season Number', 'type': 'integer'},
                },
                'required': ['episode_count', 'season_number'],
                'title': 'SeasonMeta',
                'type': 'object',
            },
            'SeriesDetails': {
                'properties': {
                    'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                    'seasons': {
                        'additionalProperties': {
                            'items': {
                                '$ref': '#/components/schemas/EpisodeDetailsSchema'
                            },
                            'type': 'array',
                        },
                        'title': 'Seasons',
                        'type': 'object',
                    },
                    'title': {'title': 'Title', 'type': 'string'},
                    'tmdb_id': {'title': 'Tmdb Id', 'type': 'integer'},
                },
                'required': ['title', 'imdb_id', 'tmdb_id', 'seasons'],
                'title': 'SeriesDetails',
                'type': 'object',
            },
            'Stats': {
                'properties': {
                    'episode': {'default': 0, 'title': 'Episode', 'type': 'integer'},
                    'movie': {'default': 0, 'title': 'Movie', 'type': 'integer'},
                },
                'title': 'Stats',
                'type': 'object',
            },
            'StatsResponse': {
                'properties': {
                    'user': {'title': 'User', 'type': 'string'},
                    'values': {'$ref': '#/components/schemas/Stats'},
                },
                'required': ['user', 'values'],
                'title': 'StatsResponse',
                'type': 'object',
            },
            'TvResponse': {
                'properties': {
                    'imdb_id': {'title': 'Imdb Id', 'type': 'string'},
                    'number_of_seasons': {
                        'title': 'Number Of Seasons',
                        'type': 'integer',
                    },
                    'seasons': {
                        'items': {'$ref': '#/components/schemas/SeasonMeta'},
                        'title': 'Seasons',
                        'type': 'array',
                    },
                    'title': {'title': 'Title', 'type': 'string'},
                },
                'required': ['number_of_seasons', 'title', 'imdb_id', 'seasons'],
                'title': 'TvResponse',
                'type': 'object',
            },
            'TvSeasonResponse': {
                'properties': {
                    'episodes': {
                        'items': {'$ref': '#/components/schemas/Episode'},
                        'title': 'Episodes',
                        'type': 'array',
                    }
                },
                'required': ['episodes'],
                'title': 'TvSeasonResponse',
                'type': 'object',
            },
            'UserCreate': {
                'properties': {
                    'password': {'title': 'Password', 'type': 'string'},
                    'username': {'title': 'Username', 'type': 'string'},
                },
                'required': ['username', 'password'],
                'title': 'UserCreate',
                'type': 'object',
            },
            'UserSchema': {
                'properties': {'username': {'title': 'Username', 'type': 'string'}},
                'required': ['username'],
                'title': 'UserSchema',
                'type': 'object',
            },
            'UserShim': {
                'properties': {'username': {'title': 'Username', 'type': 'string'}},
                'required': ['username'],
                'title': 'UserShim',
                'type': 'object',
            },
            'ValidationError': {
                'properties': {
                    'loc': {
                        'items': {'type': 'string'},
                        'title': 'Location',
                        'type': 'array',
                    },
                    'msg': {'title': 'Message', 'type': 'string'},
                    'type': {'title': 'Error Type', 'type': 'string'},
                },
                'required': ['loc', 'msg', 'type'],
                'title': 'ValidationError',
                'type': 'object',
            },
        }
    },
    'info': {'title': 'FastAPI', 'version': '0.1.0'},
    'openapi': '3.0.2',
    'paths': {
        '/create_user': {
            'post': {
                'operationId': 'create_user_create_user_post',
                'requestBody': {
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/UserCreate'}
                        }
                    },
                    'required': True,
                },
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/UserShim'}
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Create User',
                'tags': ['user'],
            }
        },
        '/delete/{type}/{id}': {
            'get': {
                'operationId': 'delete_delete__type___id__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type',
                        'required': True,
                        'schema': {'$ref': '#/components/schemas/MediaType'},
                    },
                    {
                        'in': 'path',
                        'name': 'id',
                        'required': True,
                        'schema': {'title': 'Id', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Delete',
            }
        },
        '/diagnostics': {
            'get': {
                'operationId': 'diagnostics_diagnostics_get',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'summary': 'Diagnostics',
            }
        },
        '/download': {
            'post': {
                'operationId': 'download_post_download_post',
                'requestBody': {
                    'content': {
                        'application/json': {
                            'schema': {
                                'items': {'$ref': '#/components/schemas/DownloadPost'},
                                'title': 'Things',
                                'type': 'array',
                            }
                        }
                    },
                    'required': True,
                },
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Download Post',
            }
        },
        '/index': {
            'get': {
                'operationId': 'index_index_get',
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/IndexResponse'}
                            }
                        },
                        'description': 'Successful Response',
                    }
                },
                'summary': 'Index',
            }
        },
        '/monitor': {
            'get': {
                'operationId': 'monitor_get_monitor_get',
                'parameters': [
                    {
                        'in': 'cookie',
                        'name': 'remember_token',
                        'required': False,
                        'schema': {'title': 'Remember Token', 'type': 'string'},
                    },
                    {
                        'in': 'cookie',
                        'name': 'session',
                        'required': False,
                        'schema': {'title': 'Session', 'type': 'string'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        '$ref': '#/components/schemas/MonitorGet'
                                    },
                                    'title': 'Response Monitor Get Monitor Get',
                                    'type': 'array',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Monitor Get',
                'tags': ['monitor'],
            },
            'post': {
                'operationId': 'monitor_post_monitor_post',
                'parameters': [
                    {
                        'in': 'cookie',
                        'name': 'remember_token',
                        'required': False,
                        'schema': {'title': 'Remember Token', 'type': 'string'},
                    },
                    {
                        'in': 'cookie',
                        'name': 'session',
                        'required': False,
                        'schema': {'title': 'Session', 'type': 'string'},
                    },
                ],
                'requestBody': {
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/MonitorPost'}
                        }
                    },
                    'required': True,
                },
                'responses': {
                    '201': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/MonitorGet'}
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Monitor Post',
                'tags': ['monitor'],
            },
        },
        '/monitor/{monitor_id}': {
            'delete': {
                'operationId': 'monitor_delete_monitor__monitor_id__delete',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'monitor_id',
                        'required': True,
                        'schema': {'title': 'Monitor Id', 'type': 'integer'},
                    }
                ],
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Monitor Delete',
                'tags': ['monitor'],
            }
        },
        '/movie/{tmdb_id}': {
            'get': {
                'operationId': 'movie_movie__tmdb_id__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'integer'},
                    }
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/MovieResponse'}
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Movie',
            }
        },
        '/promote': {
            'post': {
                'operationId': 'promote_promote_post',
                'parameters': [
                    {
                        'in': 'cookie',
                        'name': 'remember_token',
                        'required': False,
                        'schema': {'title': 'Remember Token', 'type': 'string'},
                    },
                    {
                        'in': 'cookie',
                        'name': 'session',
                        'required': False,
                        'schema': {'title': 'Session', 'type': 'string'},
                    },
                ],
                'requestBody': {
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/PromoteCreate'}
                        }
                    },
                    'required': True,
                },
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Promote',
                'tags': ['user'],
            }
        },
        '/redirect/plex/{tmdb_id}': {
            'get': {
                'operationId': 'redirect_plex_redirect_plex__tmdb_id__get',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'summary': 'Redirect Plex',
            }
        },
        '/redirect/{type_}/{ident}': {
            'get': {
                'operationId': 'redirect_redirect__type____ident__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type_',
                        'required': True,
                        'schema': {'$ref': '#/components/schemas/MediaType'},
                    },
                    {
                        'in': 'path',
                        'name': 'ident',
                        'required': True,
                        'schema': {'title': 'Ident', 'type': 'integer'},
                    },
                    {
                        'in': 'query',
                        'name': 'season',
                        'required': False,
                        'schema': {'title': 'Season', 'type': 'integer'},
                    },
                    {
                        'in': 'query',
                        'name': 'episode',
                        'required': False,
                        'schema': {'title': 'Episode', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Redirect',
            }
        },
        '/redirect/{type_}/{ident}/{season}/{episode}': {
            'get': {
                'operationId': 'redirect_redirect__type____ident___season___episode__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type_',
                        'required': True,
                        'schema': {'$ref': '#/components/schemas/MediaType'},
                    },
                    {
                        'in': 'path',
                        'name': 'ident',
                        'required': True,
                        'schema': {'title': 'Ident', 'type': 'integer'},
                    },
                    {
                        'in': 'path',
                        'name': 'season',
                        'required': True,
                        'schema': {'title': 'Season', 'type': 'integer'},
                    },
                    {
                        'in': 'path',
                        'name': 'episode',
                        'required': True,
                        'schema': {'title': 'Episode', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Redirect',
            }
        },
        '/search': {
            'get': {
                'operationId': 'search_search_get',
                'parameters': [
                    {
                        'in': 'query',
                        'name': 'query',
                        'required': True,
                        'schema': {'title': 'Query', 'type': 'string'},
                    }
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        '$ref': '#/components/schemas/SearchResponse'
                                    },
                                    'title': 'Response Search Search Get',
                                    'type': 'array',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Search',
            }
        },
        '/select/{tmdb_id}/season/{season}/download_all': {
            'get': {
                'operationId': 'select_select__tmdb_id__season__season__download_all_get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'integer'},
                    },
                    {
                        'in': 'path',
                        'name': 'season',
                        'required': True,
                        'schema': {'title': 'Season', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/DownloadAllResponse'
                                }
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Select',
            }
        },
        '/stats': {
            'get': {
                'operationId': 'stats_stats_get',
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        '$ref': '#/components/schemas/StatsResponse'
                                    },
                                    'title': 'Response Stats Stats Get',
                                    'type': 'array',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    }
                },
                'summary': 'Stats',
            }
        },
        '/stream/{type}/{tmdb_id}': {
            'get': {
                'operationId': 'stream_stream__type___tmdb_id__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type',
                        'required': True,
                        'schema': {'$ref': '#/components/schemas/MediaType'},
                    },
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'integer'},
                    },
                    {
                        'in': 'query',
                        'name': 'season',
                        'required': False,
                        'schema': {'title': 'Season', 'type': 'integer'},
                    },
                    {
                        'in': 'query',
                        'name': 'episode',
                        'required': False,
                        'schema': {'title': 'Episode', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/ITorrent'}
                            },
                            'text/event-stream': {},
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Stream',
            }
        },
        '/token': {
            'post': {
                'operationId': 'login_token_post',
                'requestBody': {
                    'content': {
                        'application/x-www-form-urlencoded': {
                            'schema': {
                                '$ref': '#/components/schemas/Body_login_token_post'
                            }
                        }
                    },
                    'required': True,
                },
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Login',
                'tags': ['user'],
            }
        },
        '/torrents': {
            'get': {
                'operationId': 'torrents_torrents_get',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'summary': 'Torrents',
            }
        },
        '/tv/{tmdb_id}': {
            'get': {
                'operationId': 'api_tv_tv__tmdb_id__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'integer'},
                    }
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {'$ref': '#/components/schemas/TvResponse'}
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Api Tv',
                'tags': ['tv'],
            }
        },
        '/tv/{tmdb_id}/season/{season}': {
            'get': {
                'operationId': 'api_tv_season_tv__tmdb_id__season__season__get',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'integer'},
                    },
                    {
                        'in': 'path',
                        'name': 'season',
                        'required': True,
                        'schema': {'title': 'Season', 'type': 'integer'},
                    },
                ],
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/TvSeasonResponse'
                                }
                            }
                        },
                        'description': 'Successful Response',
                    },
                    '422': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    '$ref': '#/components/schemas/HTTPValidationError'
                                }
                            }
                        },
                        'description': 'Validation Error',
                    },
                },
                'summary': 'Api Tv Season',
                'tags': ['tv'],
            }
        },
        '/user/unauthorized': {
            'get': {
                'operationId': 'user_user_unauthorized_get',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'summary': 'User',
            }
        },
    },
}

snapshots['test_movie 1'] = {'imdb_id': 'tt0000000', 'title': 'Hello'}
