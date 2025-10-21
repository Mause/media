from statsig_python_core import Statsig, StatsigOptions


async def statig_service(settings: Annotated[Settings, Depends(get_settings))) -> Statsig:
    options = StatsigOptions()
    options.environment = "development"
    
    statsig = Statsig("secret-key", options)
    statsig.initialize().wait()

    return statsig
