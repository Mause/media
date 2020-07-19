from typing import Any, Dict, Optional

import requests
from cachetools import TTLCache
from flask import current_app, request
from jwkaas import JWKaas

from .db import User, db

AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

my_jwkaas = JWKaas(
    ['https://localhost:3000/api/v2', f'{AUTH0_DOMAIN}userinfo'],
    AUTH0_DOMAIN,
    jwks_url=f'{AUTH0_DOMAIN}.well-known/jwks.json',
)

t = TTLCache(maxsize=10, ttl=3600)


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
    token_info = my_jwkaas.get_token_info(rest)
    if token_info is None:
        return None

    us = get_user_info(token_info, rest)

    return db.session.query(User).filter_by(email=us['email']).one_or_none()


def auth_hook(_: Any) -> Optional[User]:
    try:
        auth_type, rest = request.headers['authorization'].split(' ', 1)
        auth_type = auth_type.lower()
    except:
        return None

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
