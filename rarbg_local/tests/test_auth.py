from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter
from jose import constants, jwk
from pytest import mark

from ..auth import AUTH0_DOMAIN, get_current_user, security
from ..db import User
from ..models import UserSchema
from .conftest import add_json


@mark.asyncio
async def test_auth(responses, user, fastapi_app, test_client):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from jwt.api_jwt import PyJWT

    del fastapi_app.dependency_overrides[get_current_user]

    jwks_uri = 'https://mause.au.auth0.com/.well-known/jwks.json'
    add_json(
        responses,
        method='GET',
        url='https://mause.au.auth0.com//.well-known/openid-configuration',
        json_body=(
            {
                'jwks_uri': jwks_uri,
                "id_token_signing_alg_values_supported": ["HS256", "RS256", "PS256"],
            }
        ),
    )

    # Arrange
    KID = 'kid'

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    iat = datetime.now(UTC)
    exp = iat + timedelta(seconds=36000)
    jw = PyJWT().encode(
        {
            'sub': 'python',
            'iss': AUTH0_DOMAIN,
            'exp': exp,
            'iat': iat,
            'https://media.mause.me/email': user.email,
            'aud': ['https://media.mause.me', 'https://mause.au.auth0.com/userinfo'],
            'scope': 'openid profile email',
        },
        key,
        'RS256',
        {'kid': KID},
    )

    public_key = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    add_json(
        responses,
        method='GET',
        url=jwks_uri,
        json_body={
            'keys': [
                {
                    **jwk.RSAKey(
                        algorithm=constants.Algorithms.RS256,
                        key=public_key.decode('utf-8'),
                    ).to_dict(),
                    'kid': KID,
                }
            ]
        },
    )
    router = APIRouter()

    @router.get('/simple', dependencies=[security], response_model=UserSchema)
    async def show(user: Annotated[User, security]):
        return user

    fastapi_app.include_router(router)
    fastapi_app.router.routes = [
        r for r in fastapi_app.router.routes if r.name != 'static'
    ]

    # Act
    r = await test_client.get('/simple', headers={'Authorization': 'Bearer ' + jw})

    # Assert
    assert r.status_code == 200, r.text
    assert r.json() == {'first_name': '', 'username': 'python'}, r.text


@mark.asyncio
async def test_no_auth(fastapi_app, test_client):
    del fastapi_app.dependency_overrides[get_current_user]

    r = await test_client.get('/api/diagnostics')

    assert r.status_code == 403
    assert r.json() == {'detail': 'Forbidden'}
