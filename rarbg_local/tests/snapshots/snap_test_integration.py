# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_swagger 1'] = {
    'basePath': '/',
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
                        'example': [None, None],
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'type': 'array',
                },
                'incomplete': {
                    'items': {
                        'example': [None, None],
                        'items': [
                            {'type': 'string'},
                            {
                                'items': {'$ref': '#/definitions/ITorrent'},
                                'type': 'array',
                            },
                        ],
                        'type': 'array',
                    },
                    'type': 'array',
                },
                'packs': {'items': {'$ref': '#/definitions/ITorrent'}, 'type': 'array'},
            },
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
        'EpisodeInfo': {
            'properties': {
                'epnum': {'type': 'string'},
                'seasonnum': {'type': 'string'},
            },
            'type': 'object',
        },
        'ITorrent': {
            'properties': {
                'category': {'type': 'string'},
                'download': {'type': 'string'},
                'episode_info': {'$ref': '#/definitions/EpisodeInfo'},
                'seeders': {'type': 'integer'},
                'source': {
                    'enum': ('RARBG', 'KICKASS', 'HORRIBLESUBS'),
                    'example': 'RARBG',
                    'type': 'string',
                },
                'title': {'type': 'string'},
            },
            'type': 'object',
        },
        'Monitor': {
            'properties': {
                'added_by': {'type': 'string'},
                'id': {'type': 'integer'},
                'title': {'type': 'string'},
                'tmdb_id': {'type': 'integer'},
                'type': {'type': 'string'},
            },
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
    },
    'info': {'title': 'API', 'version': '1.0'},
    'paths': {
        '/api/download': {
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
        '/api/index': {
            'get': {
                'operationId': 'get_api_index',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            }
        },
        '/api/monitor': {
            'get': {
                'operationId': 'get_monitors_resource',
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
                        'schema': {
                            'items': {'$ref': '#/definitions/Monitor'},
                            'type': 'array',
                        },
                    }
                },
                'tags': ['default'],
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
                'tags': ['default'],
            },
        },
        '/api/monitor/{ident}': {
            'delete': {
                'operationId': 'delete_monitor_resource',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            },
            'parameters': [
                {'in': 'path', 'name': 'ident', 'required': True, 'type': 'integer'}
            ],
        },
        '/api/movie/{tmdb_id}': {
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
        '/api/search': {
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
        '/api/select/{tmdb_id}/season/{season}/download_all': {
            'get': {
                'operationId': 'get_download_all_episodes',
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
        '/api/stats': {
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
        '/api/torrents': {
            'get': {
                'operationId': 'get_api_torrents',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            }
        },
        '/api/tv/{tmdb_id}': {
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
                'tags': ['default'],
            }
        },
        '/api/tv/{tmdb_id}/season/{season}': {
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
                'tags': ['default'],
            },
            'parameters': [
                {'in': 'path', 'name': 'season', 'required': True, 'type': 'integer'}
            ],
        },
        '/diagnostics': {
            'get': {
                'operationId': 'get_api_diagnostics',
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            }
        },
        '/stream/{type}/{tmdb_id}': {
            'get': {
                'operationId': 'get_stream',
                'parameters': [
                    {'in': 'query', 'name': 'season', 'type': 'integer'},
                    {'in': 'query', 'name': 'episode', 'type': 'integer'},
                ],
                'responses': {'200': {'description': 'Success'}},
                'tags': ['default'],
            },
            'parameters': [
                {'in': 'path', 'name': 'type', 'required': True, 'type': 'string'},
                {'in': 'path', 'name': 'tmdb_id', 'required': True, 'type': 'string'},
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
    'tags': [{'description': 'Default namespace', 'name': 'default'}],
}
