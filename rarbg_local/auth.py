import logging
from typing import Any, Dict, Optional

import requests
from cachetools import TTLCache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes
from sqlalchemy.orm.session import Session

from .db import User
from .singleton import singleton

logger = logging.getLogger(__name__)
AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

t = TTLCache(maxsize=10, ttl=3600)


@singleton
def get_my_jwkaas():
    from jwkaas import JWKaas

    return JWKaas(
        ['https://localhost:3000/api/v2', f'{AUTH0_DOMAIN}userinfo'],
        AUTH0_DOMAIN,
        jwks_url=f'{AUTH0_DOMAIN}.well-known/jwks.json',
    )


def get_user_info(
    token_info: Dict[str, Any], rest: HTTPAuthorizationCredentials
) -> Dict:
    key = token_info['sub']
    if key in t:
        return t[key]
    else:
        t[key] = requests.get(
            f'{AUTH0_DOMAIN}userinfo',
            headers={'Authorization': rest.scheme.title() + ' ' + rest.credentials},
        ).json()
    return get_user_info(token_info, rest)


def auth_hook(
    *,
    session: Session,
    header: HTTPAuthorizationCredentials,
    security_scopes: SecurityScopes,
    jwkaas=Depends(get_my_jwkaas),
) -> Optional[User]:
    token_info = jwkaas.get_token_info(header.credentials)
    if token_info is None:
        logger.info("Token info is None")
        return None

    assert security_scopes.scopes
    logger.info(f"Security scopes: {security_scopes.scopes}")
    for scope in security_scopes.scopes:
        if scope not in token_info['scope'].split():
            logger.info(f"Scope {scope} not in token info")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
            )
    logger.info("Has required scopes")

    us = get_user_info(token_info, header)

    user = session.query(User).filter_by(email=us['email']).one_or_none()

    if user is None:
        logger.info("User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    else:
        logger.info(f"User found: {user}")
        return user
