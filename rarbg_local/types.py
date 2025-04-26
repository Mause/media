from typing import Literal, NewType

"""
The Movie DB ID
"""
TmdbId = NewType('TmdbId', int)

"""
Internet Movie Database ID
"""
ImdbId = NewType('ImdbId', str)

ThingType = Literal['movie', 'tv']
