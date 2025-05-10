import logging
from typing import Any

import requests
from cachetools import TTLCache, cached
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes
from fastapi_oidc import get_auth
from sqlalchemy.orm.session import Session

from .db import User

logger = logging.getLogger(__name__)
AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

t = TTLCache[str, dict](maxsize=10, ttl=3600)

get_my_jwkaas = get_auth(
    client_id="",
    base_authorization_server_uri=AUTH0_DOMAIN,
    issuer=AUTH0_DOMAIN,
    signature_cache_ttl=3600,
)


@cached(t, key=lambda token_info, rest: token_info.sub)
def get_user_info(
    token_info: dict[str, Any], rest: HTTPAuthorizationCredentials
) -> dict:
    return requests.get(
        f'{AUTH0_DOMAIN}userinfo',
        headers={'Authorization': rest.scheme.title() + ' ' + rest.credentials},
    ).json()


def auth_hook(
    *,
    session: Session,
    header: HTTPAuthorizationCredentials,
    security_scopes: SecurityScopes,
    jwkaas=Depends(get_my_jwkaas),
) -> User | None:
    token_info = jwkaas
    if token_info is None:
        logger.info("Token info is None")
        return None

    assert security_scopes.scopes
    logger.info(f"Security scopes: {security_scopes.scopes}")
    for scope in security_scopes.scopes:
        if scope not in token_info.scope.split():
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
