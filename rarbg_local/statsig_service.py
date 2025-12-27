import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from statsig import HashingAlgorithm, StatsigOptions, StatsigServer, StatsigUser

from .settings import Settings, get_settings

router = APIRouter()


async def get_statsig(
    settings: Annotated[Settings, Depends(get_settings)],
) -> StatsigServer:
    key = settings.statsig_key.get_secret_value()
    options = StatsigOptions(local_mode=key == 'statsig_key')

    statsig = StatsigServer()
    statsig.initialize(sdkKey=key, options=options)

    return statsig


class StatsigBootstrapResponse(BaseModel):
    statsig_values: dict | list


@router.post('/statsig-bootstrap')
async def statsig_bootstrap(
    request: Request,
    email: str,
    user_id: str,
    statsig: Annotated[StatsigServer, Depends(get_statsig)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StatsigBootstrapResponse:
    key = settings.statsig_key.get_secret_value()

    # Create a user object from the request
    user = StatsigUser(
        user_id=user_id,
        email=email,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('User-Agent'),
    )

    # Generate the client initialize response
    response_data = statsig.get_client_initialize_response(
        user, hash=HashingAlgorithm.DJB2, client_sdk_key=key
    )

    # Parse the JSON response
    statsig_values = json.loads(response_data)

    # Return the values to the client
    return StatsigBootstrapResponse(statsig_values=statsig_values)
