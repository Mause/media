from typing import Annotated, NewType

from pydantic import StringConstraints

"""
The Movie DB ID
"""
TmdbId = NewType('TmdbId', int)

"""
Internet Movie Database ID
"""
ImdbId = NewType(
    'ImdbId',
    Annotated[
        str,
        StringConstraints(
            pattern=r'^tt\d+$',
        ),
    ],
)
