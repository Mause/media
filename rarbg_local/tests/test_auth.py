from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends
from fastapi.routing import APIRoute
from jwkaas import JWKaas
from jwt.api_jwt import PyJWT

from ..auth import get_my_jwkaas
from ..new import get_current_user
from .conftest import add_json


def test_auth(responses, user, fastapi_app, test_client):
    # Arrange
    add_json(
        responses, 'GET', 'https://mause.au.auth0.com/userinfo', {'email': user.email},
    )

    KID = 'kid'
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    jw = PyJWT().encode({'sub': 'python'}, private_key, 'RS256', {'kid': KID})

    jwkaas = JWKaas(None, None)
    jwkaas.pubkeys = {KID: private_key.public_key()}

    fastapi_app.dependency_overrides[get_my_jwkaas] = lambda: jwkaas

    async def show(user=Depends(get_current_user)):
        return user

    fastapi_app.router.routes.insert(0, APIRoute('/simple', show))  # highest priority

    # Act
    r = test_client.get('/simple', headers={'Authorization': 'Bearer ' + jw.decode()})

    # Assert
    assert r.status_code == 200, r.text
    assert r.json() == {'first_name': 'python'}, r.text
