from typing import Any, Dict, Optional

import requests
from cachetools import TTLCache
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes
from jwkaas import JWKaas
from sqlalchemy.orm.session import Session

from .db import User

AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

t = TTLCache(maxsize=10, ttl=3600)


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


def auth_hook(
    session: Session = Depends('.new.get_current_user'),
    header: str = Security('.new.openid_connect'),
    security_scopes: SecurityScopes = Depends(),
    jwkaas=Depends(get_my_jwkaas),
) -> Optional[User]:
    _, header = header.split()
    token_info = jwkaas.get_token_info(header)
    if token_info is None:
        return None

    for scope in security_scopes.scopes:
        if scope not in token_info.scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
            )

    us = get_user_info(token_info, header)

    return session.query(User).filter_by(email=us['email']).one_or_none()
