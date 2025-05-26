import logging
from inspect import signature
from typing import Annotated, cast

from cachetools import TTLCache
from fastapi import Depends, HTTPException, Request, Security, params, status
from fastapi.security import (
    HTTPBasic,
    HTTPBasicCredentials,
    OpenIdConnect,
    SecurityScopes,
)
from fastapi_oidc import get_auth
from sqlalchemy.orm.session import Session

from .db import User, get_db

logger = logging.getLogger(__name__)
AUTH0_DOMAIN = 'https://mause.au.auth0.com/'

t = TTLCache[str, dict](maxsize=10, ttl=3600)

get_my_jwkaas = get_auth(
    client_id="",
    audience=AUTH0_DOMAIN + 'userinfo',
    base_authorization_server_uri=AUTH0_DOMAIN,
    issuer=AUTH0_DOMAIN,
    signature_cache_ttl=3600,
)
anno = cast(params.Depends, signature(get_my_jwkaas).parameters['auth_header'].default)
cast(OpenIdConnect, anno.dependency).auto_error = False


async def get_current_user(
    session: Annotated[Session, Depends(get_db)],
    security_scopes: SecurityScopes,
    header: Annotated[str, anno],
) -> User | None:
    if header is None or not header.lower().startswith('bearer '):
        logger.info("Token info is None")
        return None

    token_info = get_my_jwkaas(auth_header=header)

    if not security_scopes.scopes:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing security scopes'
        )

    logger.info(f"Security scopes: {security_scopes.scopes}")
    for scope in security_scopes.scopes:
        if scope not in token_info.scope.split():
            logger.info(f"Scope {scope} not in token info")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not enough permissions",
            )
    logger.info("Has required scopes")

    email = getattr(token_info, 'https://media.mause.me/email')

    user = session.query(User).filter_by(email=email).one_or_none()

    if user is None:
        logger.info("User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    else:
        logger.info(f"User found: {user}")
        return user


@Depends
def security(
    request: Request,
    auth0: Annotated[
        User,
        Security(
            get_current_user,
            scopes=['openid'],
        ),
    ],
    basic_auth: Annotated[HTTPBasicCredentials, Security(HTTPBasic(auto_error=False))],
):
    if basic_auth and request.url.path == '/api/monitor/cron':
        return basic_auth
    elif auth0:
        return auth0
    else:
        raise HTTPException(status_code=403)
