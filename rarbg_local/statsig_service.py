import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from statsig import (
    HashingAlgorithm,
    StatsigEnvironmentTier,
    StatsigOptions,
    StatsigServer,
    StatsigUser,
)

from rarbg_local.auth import get_current_user
from rarbg_local.db import User

from .settings import Settings, get_settings

router = APIRouter()


async def get_statsig(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StatsigServer:
    key = settings.statsig_key.get_secret_value()
    options = StatsigOptions(
        tier=StatsigEnvironmentTier.development,
        local_mode=key == "statsig_key",
    )

    statsig = StatsigServer()
    statsig.initialize(key, options)

    return statsig


class StatsigBootstrapResponse(BaseModel):
    statsig_values: dict | list


def get_statsig_user(
    request: Request, user: Annotated[User, Depends(get_current_user)]
) -> StatsigUser:
    return make_statsig_user(request, user.email, str(user.id))


def make_statsig_user(
    request: Request,
    email: str | None,
    user_id: str | None,
) -> StatsigUser:
    return StatsigUser(
        user_id=user_id,
        email=email,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('User-Agent'),
    )


@router.post('/statsig-bootstrap')
async def statsig_bootstrap(
    request: Request,
    email: str,
    user_id: str,
    statsig: Annotated[StatsigServer, Depends(get_statsig)],
) -> StatsigBootstrapResponse:
    user = make_statsig_user(request, email, user_id)
    # Create a user object from the request
    # Generate the client initialize response
    response_data = statsig.get_client_initialize_response(
        user, hash=HashingAlgorithm.DJB2, client_sdk_key='client-sdk-key'
    )

    # Parse the JSON response
    statsig_values = json.loads(response_data)

    # Return the values to the client
    return StatsigBootstrapResponse(statsig_values=statsig_values)
