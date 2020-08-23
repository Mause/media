from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jwkaas import JWKaas
from jwt.api_jwt import PyJWT
from pytest import mark

from ..auth import get_my_jwkaas
from ..new import get_current_user
from .conftest import add_json


@mark.xfail()
def test_auth(responses, user):
    add_json(
        responses,
        'GET',
        'https://mause.au.auth0.com/userinfo',
        {'email': 'python@python.org'},
    )

    KID = 'kid'
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    jw = PyJWT().encode({'sub': 'python'}, private_key, 'RS256', {'kid': KID})

    jwkaas = JWKaas(None, None)
    jwkaas.pubkeys = {KID: private_key.public_key()}

    single_app = FastAPI()
    single_app.dependency_overrides[get_my_jwkaas] = lambda: jwkaas

    @single_app.get('/')
    async def show(user=Depends(get_current_user)):
        return user

    test_client = TestClient(single_app)

    r = test_client.get('/', headers={'Authorization': 'Bearer ' + jw.decode()})

    assert r.status_code == 200
    assert r.json() == {'first_name': 'python'}
