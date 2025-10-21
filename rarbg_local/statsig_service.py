import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from statsig_python_core import Statsig, StatsigOptions, StatsigUser

from .settings import Settings, get_settings

router = APIRouter()


async def get_statig(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Statsig:
    options = StatsigOptions()
    options.environment = "development"

    statsig = Statsig(settings.statsig_key.get_secret_value(), options)
    statsig.initialize().wait()

    return statsig


@router.post('/statsig-bootstrap')
async def statsig_bootstrap(
    request: Request,
    email: str,
    user_id: str,
    statsig: Annotated[Statsig, Depends(get_statig)],
):
    # Create a user object from the request
    user = StatsigUser(
        user_id=user_id,
        email=email,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get('User-Agent'),
    )

    # Generate the client initialize response
    response_data = statsig.get_client_initialize_response(
        user, hash='djb2', client_sdk_key='client-sdk-key'
    )

    # Parse the JSON response
    statsig_values = json.loads(response_data)

    # Return the values to the client
    return {'statsigValues': statsig_values}
