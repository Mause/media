import logging

from cachetools import TTLCache
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes
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


def auth_hook(
    *,
    session: Session,
    security_scopes: SecurityScopes,
    token_info=Depends(get_my_jwkaas),
) -> User | None:
    if token_info is None:
        logger.info("Token info is None")
        return None

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


async def get_current_user(
    security_scopes: SecurityScopes,
    session=Depends(get_db),
    token_info=Depends(get_my_jwkaas),
):
    user = auth_hook(
        session=session, security_scopes=security_scopes, token_info=token_info
    )
    if user:
        return user
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


security = Security(
    get_current_user,
    scopes=['openid'],
)
