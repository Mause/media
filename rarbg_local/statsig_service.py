import json
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from .settings import Settings, get_settings

router = APIRouter()

if TYPE_CHECKING:
    from statsig_python_core import Statsig


async def get_statsig(
    settings: Annotated[Settings, Depends(get_settings)],
) -> 'Statsig':
    from statsig_python_core import Statsig, StatsigOptions

    key = settings.statsig_key.get_secret_value()
    options = StatsigOptions(
        environment="development", disable_network=key == "statsig_key"
    )

    statsig = Statsig(key, options)
    statsig.initialize().wait()

    return statsig


class StatsigBootstrapResponse(BaseModel):
    statsig_values: dict | list


@router.post('/statsig-bootstrap')
async def statsig_bootstrap(
    request: Request,
    email: str,
    user_id: str,
    statsig: Annotated['Statsig', Depends(get_statsig)],
) -> StatsigBootstrapResponse:
    from statsig_python_core import StatsigUser

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
    return StatsigBootstrapResponse(statsig_values=statsig_values)
