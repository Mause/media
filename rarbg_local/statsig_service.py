from statsig_python_core import Statsig, StatsigOptions

from .settings import get_settings


async def statig_service(settings: Annotated[Settings, Depends(get_settings)]) -> Statsig:
    options = StatsigOptions()
    options.environment = "development"

    statsig = Statsig(settings.statsig_key, options)
    statsig.initialize().wait()

    return statsig
