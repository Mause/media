# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_schema 1'] = {
    'definitions': {
        'MediaType': {
            'description': 'An enumeration.',
            'enum': ['series', 'movie'],
            'title': 'MediaType',
        }
    },
    'properties': {
        'imdbID': {'title': 'Imdbid', 'type': 'integer'},
        'title': {'title': 'Title', 'type': 'string'},
        'type': {'$ref': '#/definitions/MediaType'},
        'year': {'title': 'Year', 'type': 'integer'},
    },
    'required': ['title', 'type', 'imdbID'],
    'title': 'SearchResponse',
    'type': 'object',
}

snapshots['test_index 1'] = {
    'movies': [
        {
            'download': {
                'added_by': {'first_name': '', 'username': 'python'},
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
                            'added_by': {'first_name': '', 'username': 'python'},
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

snapshots['test_movie 1'] = {'imdb_id': 'tt0000000', 'title': 'Hello'}

snapshots['test_openapi 1'] = {
    'components': {
        'schemas': {
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
            'InnerTorrent': {
                'properties': {
                    'eta': {'title': 'Eta', 'type': 'integer'},
                    'files': {
                        'items': {'$ref': '#/components/schemas/InnerTorrentFile'},
                        'title': 'Files',
                        'type': 'array',
                    },
                    'hashString': {'title': 'Hashstring', 'type': 'string'},
                    'id': {'title': 'Id', 'type': 'integer'},
                    'percentDone': {'title': 'Percentdone', 'type': 'number'},
                },
                'required': ['eta', 'hashString', 'id', 'percentDone', 'files'],
                'title': 'InnerTorrent',
                'type': 'object',
            },
            'InnerTorrentFile': {
                'properties': {
                    'bytesCompleted': {'title': 'Bytescompleted', 'type': 'integer'},
                    'length': {'title': 'Length', 'type': 'integer'},
                    'name': {'title': 'Name', 'type': 'string'},
                },
                'required': ['bytesCompleted', 'length', 'name'],
                'title': 'InnerTorrentFile',
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
                    'status': {'default': False, 'title': 'Status', 'type': 'boolean'},
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
            'ProviderSource': {
                'description': 'An enumeration.',
                'enum': ['kickass', 'horriblesubs', 'rarbg'],
                'title': 'ProviderSource',
            },
            'SearchResponse': {
                'properties': {
                    'imdbID': {'title': 'Imdbid', 'type': 'integer'},
                    'title': {'title': 'Title', 'type': 'string'},
                    'type': {'$ref': '#/components/schemas/MediaType'},
                    'year': {'title': 'Year', 'type': 'integer'},
                },
                'required': ['title', 'type', 'imdbID'],
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
                'required': ['number_of_seasons', 'seasons', 'title'],
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
            'UserSchema': {
                'properties': {
                    'first_name': {'title': 'First Name', 'type': 'string'},
                    'username': {'title': 'Username', 'type': 'string'},
                },
                'required': ['username', 'first_name'],
                'title': 'UserSchema',
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
        },
        'securitySchemes': {
            'XOpenIdConnect': {
                'openIdConnectUrl': (
                    'https://mause.au.auth0.com/.well-known/openid-configuration'
                ),
                'type': 'openIdConnect',
            }
        },
    },
    'info': {'title': 'Media', 'version': '0.1.0-dev'},
    'openapi': '3.0.2',
    'paths': {
        '/api/delete/{type}/{id}': {
            'get': {
                'operationId': 'delete',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Delete',
            }
        },
        '/api/diagnostics': {
            'get': {
                'operationId': 'diagnostics',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Diagnostics',
            }
        },
        '/api/diagnostics/pool': {
            'get': {
                'operationId': 'pool',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Pool',
            }
        },
        '/api/download': {
            'post': {
                'operationId': 'download_post',
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
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        'anyOf': [
                                            {
                                                '$ref': '#/components/schemas/MovieDetailsSchema'
                                            },
                                            {
                                                '$ref': '#/components/schemas/EpisodeDetailsSchema'
                                            },
                                        ]
                                    },
                                    'title': 'Response Download Post Api Download Post',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Download Post',
            }
        },
        '/api/index': {
            'get': {
                'operationId': 'index',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Index',
            }
        },
        '/api/monitor': {
            'get': {
                'operationId': 'monitor_get',
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        '$ref': '#/components/schemas/MonitorGet'
                                    },
                                    'title': 'Response Monitor Get Api Monitor Get',
                                    'type': 'array',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Monitor Get',
                'tags': ['monitor'],
            },
            'post': {
                'operationId': 'monitor_post',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Monitor Post',
                'tags': ['monitor'],
            },
        },
        '/api/monitor/{monitor_id}': {
            'delete': {
                'operationId': 'monitor_delete',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Monitor Delete',
                'tags': ['monitor'],
            }
        },
        '/api/movie/{tmdb_id}': {
            'get': {
                'operationId': 'movie',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Movie',
            }
        },
        '/api/search': {
            'get': {
                'operationId': 'search',
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
                                    'title': 'Response Search Api Search Get',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Search',
            }
        },
        '/api/select/{tmdb_id}/season/{season}/download_all': {
            'get': {
                'operationId': 'select',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Select',
            }
        },
        '/api/stats': {
            'get': {
                'operationId': 'stats',
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'items': {
                                        '$ref': '#/components/schemas/StatsResponse'
                                    },
                                    'title': 'Response Stats Api Stats Get',
                                    'type': 'array',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Stats',
            }
        },
        '/api/stream/{type}/{tmdb_id}': {
            'get': {
                'operationId': 'stream',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type',
                        'required': True,
                        'schema': {'title': 'Type', 'type': 'string'},
                    },
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'string'},
                    },
                    {
                        'in': 'query',
                        'name': 'source',
                        'required': False,
                        'schema': {'$ref': '#/components/schemas/ProviderSource'},
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Stream',
            }
        },
        '/api/torrents': {
            'get': {
                'operationId': 'torrents',
                'responses': {
                    '200': {
                        'content': {
                            'application/json': {
                                'schema': {
                                    'additionalProperties': {
                                        '$ref': '#/components/schemas/InnerTorrent'
                                    },
                                    'title': 'Response Torrents Api Torrents Get',
                                    'type': 'object',
                                }
                            }
                        },
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Torrents',
            }
        },
        '/api/tv/{tmdb_id}': {
            'get': {
                'operationId': 'api_tv',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Api Tv',
                'tags': ['tv'],
            }
        },
        '/api/tv/{tmdb_id}/season/{season}': {
            'get': {
                'operationId': 'api_tv_season',
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
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'Api Tv Season',
                'tags': ['tv'],
            }
        },
        '/api/user/unauthorized': {
            'get': {
                'operationId': 'user',
                'responses': {
                    '200': {
                        'content': {'application/json': {'schema': {}}},
                        'description': 'Successful Response',
                    }
                },
                'security': [{'XOpenIdConnect': ['openid']}],
                'summary': 'User',
            }
        },
        '/redirect/plex/{tmdb_id}': {
            'get': {
                'operationId': 'redirect_to_plex',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'tmdb_id',
                        'required': True,
                        'schema': {'title': 'Tmdb Id', 'type': 'string'},
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
                'summary': 'Redirect To Plex',
            }
        },
        '/redirect/{type_}/{tmdb_id}': {
            'get': {
                'operationId': 'redirect_to_imdb',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type_',
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
                'summary': 'Redirect To Imdb',
            }
        },
        '/redirect/{type_}/{tmdb_id}/{season}/{episode}': {
            'get': {
                'operationId': 'redirect_to_imdb',
                'parameters': [
                    {
                        'in': 'path',
                        'name': 'type_',
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
                'summary': 'Redirect To Imdb',
            }
        },
    },
    'servers': [
        {
            'description': 'Development',
            'url': '{protocol}://localhost:5000/',
            'variables': {'protocol': {'default': 'https', 'enum': ['http', 'https']}},
        },
        {'description': 'Staging', 'url': 'https://media-staging.herokuapps.com/'},
        {'description': 'Production', 'url': 'https://media.mause.me/'},
    ],
}

snapshots['test_season_info 1'] = {
    'episodes': [{'air_date': None, 'episode_number': 1, 'id': 0, 'name': 'The Pilot'}]
}

snapshots['test_select_season 1'] = {
    'imdb_id': 'tt1000',
    'number_of_seasons': 1,
    'seasons': [{'episode_count': 1, 'season_number': 1}],
    'title': 'hello',
}

snapshots['test_pool_status 1'] = {
    'checkedin': None,
    'checkedout': None,
    'overflow': None,
    'size': 5,
    'worker_id': 1,
}
