def test_statsig_integration() -> None:
    from ..sentry.statsig import StatsigIntegration

    StatsigIntegration.setup_once()
    assert StatsigIntegration.identifier == "statsig-python-core"
