from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from cachetools import TTLCache
from fastapi import Depends, HTTPException
from flask import current_app, request
from jwkaas import JWKaas
from starlette.status import HTTP_401_UNAUTHORIZED

from .db import User, db
from .utils import precondition

AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

t = TTLCache(maxsize=10, ttl=3600)


@lru_cache()
def get_my_jwkaas():
    return JWKaas(
        ['https://localhost:3000/api/v2', f'{AUTH0_DOMAIN}userinfo'],
        AUTH0_DOMAIN,
        jwks_url=f'{AUTH0_DOMAIN}.well-known/jwks.json',
    )


def get_user_info(token_info: Dict[str, Any], rest: str) -> Dict:
    key = token_info['sub']
    if key in t:
        return t[key]
    else:
        t[key] = requests.get(
            f'{AUTH0_DOMAIN}userinfo', headers={'Authorization': 'Bearer ' + rest},
        ).json()
    return get_user_info(token_info, rest)


def bearer_auth(rest: str) -> Optional[User]:
    token_info = get_my_jwkaas().get_token_info(rest)
    if token_info is None:
        return None

    us = get_user_info(token_info, rest)

    return db.session.query(User).filter_by(email=us['email']).one_or_none()


def get_auth() -> Optional[Tuple[str, str]]:
    try:
        auth_type, rest = request.headers['authorization'].split(' ', 1)
        auth_type = auth_type.lower()
    except:
        return None
    else:
        return auth_type, rest


def auth_hook(_: Any) -> Optional[User]:
    at = get_auth()
    if not at:
        return None
    auth_type, rest = at

    if auth_type == 'basic':
        return basic_auth()
    elif auth_type == 'bearer':
        return bearer_auth(rest)
    else:
        raise TypeError()


def basic_auth() -> Optional[User]:
    auth = request.authorization
    assert auth
    user = db.session.query(User).filter_by(username=auth['username']).one_or_none()

    if current_app.user_manager.verify_password(
        auth['password'], user.password if user else None
    ):
        return user
    else:
        return None


def Scopes(requested: List[str]) -> Callable:
    def scopes() -> List[str]:
        auth_type, rest = precondition(get_auth(), 'missing auth')
        scopes = get_my_jwkaas().get_token_info(rest)['scopes']

        if not all(r in scopes for r in requested):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)
        return scopes

    return Depends(scopes)
